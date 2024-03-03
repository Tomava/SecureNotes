import datetime
import os
import random
import sqlite3
import uuid
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)
import waitress
from config import (
    ENVIRONMENT,
    SECRET_KEY,
    JWT_SECRET_KEY,
    CREDENTIALS_DB,
    USERS_TABLE,
    REVOKED_TOKENS_TABLE,
    MAX_PASSWORD_LENGTH,
    ACCESS_EXPIRES
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

def get_database_result(database_name, statement):
    con = sqlite3.connect(database_name)
    cur = con.cursor()
    res = cur.execute(statement)
    con.commit()
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
    username = jwt_payload.get("sub")
    jti = jwt_payload.get("jti")

    dev_log(f"{issued_at}, {username}, {jti}")
    # Check revoked tokens
    # TODO: SQL injection here from 'iat' (not really, because the token are server generated). FIX: Use prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'SELECT * FROM {REVOKED_TOKENS_TABLE} WHERE token == "{jti}"',
    )
    if res.fetchone() is not None:
        return True

    # Check that token is more recent than last password change
    # TODO: SQL injection here from 'username'. FIX: Use prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'SELECT password_change_time FROM {USERS_TABLE} WHERE username == "{username}"',
    )

    result = res.fetchone()

    # Username not found
    if result is None:
        return False
    
    change_time = result[0]

    if issued_at < change_time:
        return True

    return False


@app.post("/signup")
def sign_up():
    request_data = request.form
    username = request_data.get("username")
    password = request_data.get("password")
    # TODO: SQL injection here from 'username'. FIX: Use prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'SELECT username FROM {USERS_TABLE} WHERE username == "{username}"',
    )
    # Username already taken
    if res.fetchone() is not None:
        return jsonify(messages.USERNAME_TAKEN_ERROR), 409

    password_hash = hash_password(password)
    uuid_value = uuid.uuid4()
    now = datetime.datetime.now().replace(microsecond=0)
    # TODO: SQL injection here from 'username'. FIX: Use prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f"""INSERT INTO {USERS_TABLE}(id, username, login_hash, password_change_time)
        VALUES ("{uuid_value}", "{username}", "{password_hash}", "{now.timestamp()}");""",
    )

    return jsonify(messages.USER_CREATED), 201


@app.post("/login")
def login():
    request_data = request.form
    username = request_data.get("username")
    password = request_data.get("password")

    # TODO: SQL injection here from 'username'. FIX: Use prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'SELECT login_hash FROM {USERS_TABLE} WHERE username == "{username}"',
    )

    result = res.fetchone()

    # Username not found
    if result is None:
        # Hash a random password to introduce similar delay as in verify function
        hash_password(random.randint(0, 1000))
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    login_hash = result[0]
    if not verify_password(login_hash, password):
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    access_token = create_access_token(identity=username)
    message = messages.LOGGED_IN
    message["access_token"] = access_token
    return jsonify(message), 200


@app.route("/protected", methods=["GET"])
@jwt_required()
def test_secret():
    current_user = get_jwt_identity()
    dev_log(current_user)
    return jsonify({"message": "success"}), 200


if __name__ == "__main__":
    if ENVIRONMENT == "prod":
        waitress.serve(app, host="0.0.0.0", port=8080)
    else:
        app.run(debug=True)
