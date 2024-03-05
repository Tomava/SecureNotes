import datetime
import os
import random
import sqlite3
import uuid
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
    JWTManager,
)
from flask_cors import CORS, cross_origin
import waitress
from config import (
    ENVIRONMENT,
    SECRET_KEY,
    JWT_SECRET_KEY,
    CREDENTIALS_DB,
    USERS_TABLE,
    REVOKED_TOKENS_TABLE,
    MAX_PASSWORD_LENGTH,
    ACCESS_EXPIRES,
    PORT
)
import messages as messages
import argon2

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
jwt = JWTManager(app)


def dev_log(message):
    if ENVIRONMENT == "dev":
        print(f"{datetime.datetime.now().replace(microsecond=0).isoformat()}: {message}")

def get_database_result(database_name, statement, args):
    dev_log(statement)
    try:
        con = sqlite3.connect(database_name)
        cur = con.cursor()
        res = cur.execute(statement, args)
        con.commit()
    except NameError as err:
        dev_log(err)
        return None
    except ValueError as err:
        dev_log(err)
        return None
    except IOError as err:
        dev_log(err)
        return None
    except sqlite3.Error as err:
        dev_log(err)
        return None
    return res


def hash_password(password):
    # VULNERABILITY_FIX: Avoid any too long password
    if len(password) > MAX_PASSWORD_LENGTH:
        password = password[:MAX_PASSWORD_LENGTH]
    password_hasher = argon2.PasswordHasher()
    hash_result = password_hasher.hash(password)
    return hash_result


def verify_password(saved_hash, password):
    password_hasher = argon2.PasswordHasher()

    if saved_hash is None:
        return False
    try:
        password_hasher.verify(saved_hash, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    dev_log(jwt_payload)
    issued_at = jwt_payload.get("iat")
    user_id = jwt_payload.get("sub")
    jti = jwt_payload.get("jti")

    dev_log(f"{issued_at}, {user_id}, {jti}")
    # Check revoked tokens
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT * FROM {REVOKED_TOKENS_TABLE} WHERE token == ?",
        (jti,)
    )

    # Error on SQL
    if res is None:
        return True

    # Token revoked
    if res.fetchone() is not None:
        return True

    # Check that token is more recent than last password change
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT password_change_time FROM {USERS_TABLE} WHERE id == ?",
        (user_id,)
    )

    # Error on SQL
    if res is None:
        return True

    result = res.fetchone()

    # Username not found
    if result is None:
        return False
    
    change_time = result[0]

    if issued_at < change_time:
        return True

    return False


@app.post("/signup")
@cross_origin()
def sign_up():
    request_data = request.get_json()
    username = request_data.get("username")
    front_login_hash = request_data.get("front_login_hash")
    front_login_salt = request_data.get("front_login_salt")
    encryption_salt = request_data.get("encryption_salt")
    encrypted_encryption_key = request_data.get("encrypted_encryption_key")
    #password = request_data.get("password")
    # VULNERABILITY_FIX: Avoid SQL injection in 'username' with parameterized query
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT username FROM {USERS_TABLE} WHERE username == ?",
        (username,)
    )

    # Error on SQL
    if res is None:
        return jsonify(messages.SERVER_ERROR), 500

    # Username already taken
    if res.fetchone() is not None:
        return jsonify(messages.USERNAME_TAKEN_ERROR), 409

    password_hash = hash_password(front_login_hash)
    uuid_value = str(uuid.uuid4())
    now = datetime.datetime.now().replace(microsecond=0)
    # VULNERABILITY_FIX: Avoid SQL injection in 'username' with parameterized query
    res = get_database_result(
        CREDENTIALS_DB,
        f"""INSERT INTO {USERS_TABLE} (
            id,
            username,
            login_hash,
            front_login_salt,
            encryption_salt,
            encrypted_encryption_key,
            password_change_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);""",
        (uuid_value,
         username,
         password_hash,
         front_login_salt,
         encryption_salt,
         encrypted_encryption_key,
         now.timestamp(),)
    )
    # Error on SQL
    if res is None:
        return jsonify(messages.SERVER_ERROR), 500

    return jsonify(messages.USER_CREATED), 201


@app.get("/hash")
@cross_origin()
def hash():
    username = request.args.get("username")
    dev_log(username)

    # VULNERABILITY_FIX: Avoid SQL injection in 'username' with parameterized query
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT front_login_salt FROM {USERS_TABLE} WHERE username == ?",
        (username,)
    )

    # Error on SQL
    if res is None:
        return jsonify(messages.SERVER_ERROR), 500

    result = res.fetchone()

    # Username not found
    if result is None:
        return jsonify(messages.USERNAME_NOT_FOUND_ERROR), 404
    
    front_login_salt = result[0]
    message = messages.LOGIN_HASH
    message["data"] = { "front_login_salt": front_login_salt }
    return jsonify(message), 200

@app.get("/login")
@cross_origin()
def login():
    username = request.args.get("username")
    front_login_hash = request.args.get("front_login_hash")

    # VULNERABILITY_FIX: Avoid SQL injection in 'username' with parameterized query
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT id, login_hash, encryption_salt, encrypted_encryption_key FROM {USERS_TABLE} WHERE username == ?",
        (username,)
    )

    # Error on SQL
    if res is None:
        return jsonify(messages.SERVER_ERROR), 500

    result = res.fetchone()

    # Username not found
    if result is None:
        # Hash a random password to introduce similar delay as in verify function
        hash_password(str(uuid.uuid4()))
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401
    
    used_id, login_hash, encryption_salt, encrypted_encryption_key = result
    if not verify_password(login_hash, front_login_hash):
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    access_token = create_access_token(identity=used_id)
    message = messages.LOGGED_IN
    # TODO: Set access token as HTTP only cookie instead of passing it in the data
    message["data"] = {
        "access_token": access_token,
        "encryption_salt": encryption_salt,
        "encrypted_encryption_key": encrypted_encryption_key
    }
    return jsonify(message), 200


@app.get("/logout")
@jwt_required()
@cross_origin()
def logout():
    jwt = get_jwt()
    issued_at = jwt.get("iat")
    jti = jwt.get("jti")

    res = get_database_result(
        CREDENTIALS_DB,
        f"INSERT INTO {REVOKED_TOKENS_TABLE}(token, expires) VALUES (?, ?)",
        (jti, issued_at)
    )

    # Error on SQL
    if res is None:
        return jsonify(messages.SERVER_ERROR), 500

    return jsonify(messages.LOGGED_OUT), 200


# TODO: Remove this, as it's only a test
@app.route("/protected", methods=["GET"])
@jwt_required()
def test_secret():
    current_user = get_jwt_identity()
    dev_log(current_user)
    return jsonify({"message": "success"}), 200


if __name__ == "__main__":
    if ENVIRONMENT == "prod":
        waitress.serve(app, host="0.0.0.0", port=PORT)
    else:
        app.run(debug=True, port=PORT)
