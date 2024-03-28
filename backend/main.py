import base64
import datetime
import secrets
import sqlite3
import uuid
import psycopg2
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_wtf.csrf import CSRFProtect, generate_csrf
import waitress
from config import *
import messages as messages
import argon2

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
csrf = CSRFProtect(app)


def login_required(f):
    @wraps(f)
    def check_user_login(*args, **kwargs):
        session_token = request.cookies.get(SESSION_TOKEN)
        if session_token is None:
            return jsonify(messages.UNAUTHORIZED_ERROR), 401

        try:
            res = get_database_result(
                CREDENTIALS_DB,
                f"SELECT user_id FROM {TOKENS_TABLE} WHERE token =(%s)",
                (session_token,),
                fetch=True,
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500

        if res is None:
            return jsonify(messages.UNAUTHORIZED_ERROR), 401

        return f(*args, **kwargs)

    return check_user_login


def dev_log(message):
    if ENVIRONMENT == "dev":
        print(
            f"{datetime.datetime.now().replace(microsecond=0).isoformat()}: {message}"
        )


def get_database_result(database_name, statement, args, fetch=False, fetch_all=False):
    dev_log(statement)
    con = psycopg2.connect(
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        host=DB_HOST,
        password=POSTGRES_PASSWORD,
        port=DB_PORT,
    )
    cur = con.cursor()
    cur.execute(statement, args)
    res = None
    if fetch_all:
        res = cur.fetchall()
    elif fetch:
        res = cur.fetchone()
    con.commit()
    cur.close()
    con.close()
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


@app.post("/signup")
@cross_origin()
@csrf.exempt
def sign_up():
    request_data = request.get_json()
    username = request_data.get("username")
    front_login_hash = request_data.get("front_login_hash")
    front_login_salt = request_data.get("front_login_salt")
    encryption_salt = request_data.get("encryption_salt")
    encrypted_encryption_key = request_data.get("encrypted_encryption_key")

    if len(username) > USERNAME_MAX_LEN or len(front_login_salt) != FRONT_LOGIN_SALT_LEN or len(encryption_salt) != ENCRYPTION_SALT_LEN or len(encrypted_encryption_key) != ENCRYPTED_ENCRYPTION_KEY_LEN:
        message = messages.INVALID_PARAMETERS_ERROR
        message["message"] = "Invalid character length of parameters"
        return jsonify(message), 400

    try:
        res = get_database_result(
            CREDENTIALS_DB,
            f"SELECT username FROM {USERS_TABLE} WHERE username = (%s)",
            (username,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    # Username already taken
    if res is not None:
        return jsonify(messages.USERNAME_TAKEN_ERROR), 409

    password_hash = hash_password(front_login_hash)
    uuid_value = str(uuid.uuid4())
    now = datetime.datetime.now().replace(microsecond=0)

    try:
        get_database_result(
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
            VALUES (%s, %s, %s, %s, %s, %s, %s);""",
            (
                uuid_value,
                username,
                password_hash,
                front_login_salt,
                encryption_salt,
                encrypted_encryption_key,
                now.timestamp(),
            ),
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    return jsonify(messages.USER_CREATED), 201


@app.get("/hash")
@cross_origin()
@csrf.exempt
def hash():
    username = request.args.get("username")
    dev_log(username)

    try:
        res = get_database_result(
            CREDENTIALS_DB,
            f"SELECT front_login_salt FROM {USERS_TABLE} WHERE username = (%s)",
            (username,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    # Username not found
    if res is None:
        return jsonify(messages.USERNAME_NOT_FOUND_ERROR), 404

    front_login_salt = res[0]
    message = messages.LOGIN_HASH
    message["data"] = {"front_login_salt": front_login_salt}
    return jsonify(message), 200


@app.get("/csrf")
@cross_origin()
@login_required
@csrf.exempt
def get_csrf():
    message = messages.CSRF_TOKEN_CREATED
    message["data"] = {"csrf_token": generate_csrf()}
    return jsonify(message), 200


@app.post("/login")
@cross_origin()
@csrf.exempt
def login():
    request_data = request.get_json()

    username = request_data.get("username")
    front_login_hash = request_data.get("front_login_hash")

    if len(username) > USERNAME_MAX_LEN:
        message = messages.INVALID_PARAMETERS_ERROR
        message["message"] = "Invalid character length of parameters"
        return jsonify(message), 400

    try:
        result = get_database_result(
            CREDENTIALS_DB,
            f"SELECT id, login_hash, encryption_salt, encrypted_encryption_key FROM {USERS_TABLE} WHERE username = (%s)",
            (username,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    # Username not found
    if result is None:
        # Hash a random password to introduce similar delay as in verify function
        hash_password(str(uuid.uuid4()))
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    user_id, login_hash, encryption_salt, encrypted_encryption_key = result
    if not verify_password(login_hash, front_login_hash):
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    session_token = secrets.token_hex(64)

    message = messages.LOGGED_IN
    message["data"] = {
        "encryption_salt": encryption_salt,
        "encrypted_encryption_key": encrypted_encryption_key,
    }

    now = datetime.datetime.now().replace(microsecond=0)

    try:
        get_database_result(
            CREDENTIALS_DB,
            f"""INSERT INTO {TOKENS_TABLE} (
                token,
                user_id,
                created_at
            )
            VALUES (%s, %s, %s);""",
            (
                session_token,
                user_id,
                now.timestamp(),
            ),
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    response = jsonify(message)
    response.set_cookie(SESSION_TOKEN, session_token, httponly=True)
    return response, 200


@app.post("/logout")
@cross_origin()
@login_required
def logout():
    session = request.cookies.get(SESSION_TOKEN)
    try:
        get_database_result(
            CREDENTIALS_DB, f"DELETE FROM {TOKENS_TABLE} WHERE token = (%s)", (session,)
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500
    message = messages.LOGGED_OUT
    response = jsonify(message)
    response.set_cookie(SESSION_TOKEN, "", expires=0, httponly=True)
    response.set_cookie("session", "", expires=0, httponly=True)
    return response, 200


@app.route("/notes", methods=["GET", "POST", "PUT"])
@cross_origin()
@login_required
def notes():
    method = request.method
    session = request.cookies.get(SESSION_TOKEN)
    res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT user_id FROM {TOKENS_TABLE} WHERE token =(%s)",
        (session,),
        fetch=True,
    )
    current_user = res[0]
    if method == "GET":
        try:
            res = get_database_result(
                CREDENTIALS_DB,
                f"SELECT note_id, created_at, modified_at, note_title, note_body FROM {NOTES_TABLE} WHERE owner_id = (%s)",
                (current_user,),
                fetch_all=True,
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500
        notes_list = []
        for result in res:
            note_id, created_at, modified_at, note_title, note_body = result
            notes_list.append(
                {
                    "note_id": note_id,
                    "created_at": created_at,
                    "modified_at": modified_at,
                    "note_title": base64.b64encode(note_title).decode("utf-8"),
                    "note_body": base64.b64encode(note_body).decode("utf-8"),
                }
            )
        message = messages.DATA_FETCHED
        message["data"] = {"notes": notes_list}
        return jsonify(message), 200
    if method == "POST":
        res = get_database_result(
        CREDENTIALS_DB,
        f"SELECT COUNT(*) FROM {NOTES_TABLE} WHERE owner_id =(%s)",
        (current_user,),
        fetch=True,
        )
        notes_amount = res[0]
        if notes_amount >= MAX_NOTES:
            return jsonify(messages.TOO_MANY_ERROR), 413
        request_data = request.get_json()
        try:
            original_note_title = request_data.get("note_title")
            original_note_body = request_data.get("note_body")
            note_title = base64.b64decode(original_note_title)
            note_body = base64.b64decode(original_note_body)
            uuid_value = str(uuid.uuid4())
        except ValueError:
            return jsonify(messages.INVALID_PARAMETERS_ERROR), 400
        now = datetime.datetime.now().replace(microsecond=0)
        title_size = len(note_title)
        body_size = len(note_body)
        if title_size + body_size > MAX_SIZE:
            return jsonify(messages.TOO_LARGE_ERROR), 413
        try:
            res = get_database_result(
                CREDENTIALS_DB,
                f"""INSERT INTO {NOTES_TABLE} (
                    note_id,
                    owner_id,
                    created_at,
                    modified_at,
                    note_title,
                    note_body
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING note_id;""",
                (
                    uuid_value,
                    current_user,
                    int(now.timestamp()),
                    int(now.timestamp()),
                    note_title,
                    note_body,
                ),
                fetch=True,
            )
            note_id = res[0]
            inserted_data = {
                "note_id": note_id,
                "created_at": int(now.timestamp()),
                "modified_at": int(now.timestamp()),
                "note_title": original_note_title,
                "note_body": original_note_body,
            }
            message = messages.NOTE_CREATED
            message["data"] = inserted_data
            return jsonify(message), 201
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500

    return jsonify({"message": "success"}), 200


# TODO: Remove this, as it's only a test
@app.route("/protected", methods=["GET"])
@cross_origin()
@login_required
def test_secret():
    return jsonify({"message": "success"}), 200


if __name__ == "__main__":
    if ENVIRONMENT == "prod":
        waitress.serve(app, host="0.0.0.0", port=PORT)
    else:
        app.run(host="0.0.0.0", debug=True, port=PORT)
