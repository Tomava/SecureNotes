import base64
import datetime
import secrets
import sqlite3
import uuid
import psycopg2
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
import waitress
from config import *
import messages as messages
import argon2
import pyotp


def create_app():
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = SECRET_KEY
    return flask_app


app = create_app()
csrf = CSRFProtect(app)
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)


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


def get_current_user_id(given_request):
    session_token = given_request.cookies.get(SESSION_TOKEN)
    try:
        res = get_database_result(
            CREDENTIALS_DB,
            f"SELECT user_id FROM {TOKENS_TABLE} WHERE token = (%s)",
            (session_token,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return None
    current_user_id = res[0]
    return current_user_id


def get_current_user(user_id):
    try:
        res = get_database_result(
            CREDENTIALS_DB,
            f"SELECT username FROM {USERS_TABLE} WHERE id = (%s)",
            (user_id,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return None
    current_user = res[0]
    return current_user


def hash_password(password):
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


@app.route("/otp", methods=["GET", "POST", "DELETE"])
@login_required
def otp():
    otp_secret = pyotp.random_base32()
    current_user_id = get_current_user_id(request)
    current_username = get_current_user(current_user_id)

    if request.method == "GET":
        try:
            res = get_database_result(
                CREDENTIALS_DB,
                f"""SELECT otp_secret
                    FROM {USERS_TABLE}
                    WHERE id = %s
                    AND NOT (otp_secret IS NULL OR otp_secret = '');""",
                (current_user_id,),
                fetch=True,
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500
        if res is None:
            return jsonify(messages.NOT_FOUND_ERROR), 404
        return jsonify(messages.OK), 200
    elif request.method == "DELETE":
        try:
            get_database_result(
                CREDENTIALS_DB,
                f"""UPDATE {USERS_TABLE}
                    SET otp_secret = NULL
                    WHERE id = %s;""",
                (
                    current_user_id,
                ),
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500
        return jsonify(messages.OK), 200
    elif request.method == "POST":
        try:
            get_database_result(
                CREDENTIALS_DB,
                f"""UPDATE {USERS_TABLE}
                    SET otp_secret = %s
                    WHERE id = %s;""",
                (
                    otp_secret,
                    current_user_id,
                ),
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500

        otp_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(
            name=current_username, issuer_name="SecureNotes"
        )

        message = messages.OTP_ADDED
        message["data"] = {"otp_secret": otp_secret, "otp_uri": otp_uri}

        return jsonify(message), 201


@app.post("/signup")
@csrf.exempt
def sign_up():
    request_data = request.get_json()
    username = request_data.get("username")
    front_login_hash = request_data.get("front_login_hash")
    front_login_salt = request_data.get("front_login_salt")
    encryption_salt = request_data.get("encryption_salt")
    encrypted_encryption_key = request_data.get("encrypted_encryption_key")

    if (
        len(username) > USERNAME_MAX_LEN
        or len(front_login_hash) != FRONT_LOGIN_HASH_LEN
        or len(front_login_salt) != FRONT_LOGIN_SALT_LEN
        or len(encryption_salt) != ENCRYPTION_SALT_LEN
        or len(encrypted_encryption_key) != ENCRYPTED_ENCRYPTION_KEY_LEN
    ):
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

    peppered_front_login_hash = f"{front_login_hash}{DATABASE_PEPPER}"
    password_hash = hash_password(peppered_front_login_hash)
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
        return jsonify(messages.NOT_FOUND_ERROR), 404

    front_login_salt = res[0]
    message = messages.LOGIN_HASH
    message["data"] = {"front_login_salt": front_login_salt}
    return jsonify(message), 200


@app.get("/csrf")
@login_required
@csrf.exempt
def get_csrf():
    message = messages.CSRF_TOKEN_CREATED
    message["data"] = {"csrf_token": generate_csrf()}
    return jsonify(message), 200


@app.post("/login")
@csrf.exempt
def login():
    request_data = request.get_json()

    username = request_data.get("username")
    front_login_hash = request_data.get("front_login_hash")
    request_otp_code = request_data.get("otp_code")

    if (
        len(username) > USERNAME_MAX_LEN
        or len(front_login_hash) != FRONT_LOGIN_HASH_LEN
    ):
        message = messages.INVALID_PARAMETERS_ERROR
        message["message"] = "Invalid character length of parameters"
        return jsonify(message), 400

    try:
        result = get_database_result(
            CREDENTIALS_DB,
            f"SELECT id, login_hash, encryption_salt, encrypted_encryption_key, otp_secret FROM {USERS_TABLE} WHERE username = (%s)",
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

    user_id, login_hash, encryption_salt, encrypted_encryption_key, otp_secret = result
    peppered_front_login_hash = f"{front_login_hash}{DATABASE_PEPPER}"

    if not verify_password(login_hash, peppered_front_login_hash):
        return jsonify(messages.INVALID_CREDENTIALS_ERROR), 401

    if otp_secret is not None:
        totp = pyotp.TOTP(otp_secret)
        if (
            not request_otp_code
            or len(request_otp_code) != 6
            or not totp.verify(request_otp_code, valid_window=2)
        ):
            return jsonify(messages.INVALID_OTP_ERROR), 401

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


@app.get("/session")
@login_required
def session():
    current_user = get_current_user_id(request)
    if current_user is None:
        return jsonify(messages.SERVER_ERROR), 500

    try:
        res2 = get_database_result(
            CREDENTIALS_DB,
            f"SELECT COUNT(*) FROM {TOKENS_TABLE} WHERE user_id =(%s)",
            (current_user,),
            fetch=True,
        )
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500
    sessions = res2[0]
    message = messages.DATA_FETCHED
    message["data"] = {"sessions": sessions}
    return jsonify(message), 200


@app.post("/logout")
@login_required
def logout():
    session_token = request.cookies.get(SESSION_TOKEN)
    current_user = get_current_user_id(request)
    if current_user is None:
        return jsonify(messages.SERVER_ERROR), 500
    query_string = f"DELETE FROM {TOKENS_TABLE} WHERE token = (%s)"
    query_params = (session_token,)
    if request.args.get("all"):
        query_string = f"DELETE FROM {TOKENS_TABLE} WHERE user_id = (%s)"
        query_params = (current_user,)

    try:
        get_database_result(CREDENTIALS_DB, query_string, query_params)
    except psycopg2.Error as e:
        dev_log(e)
        return jsonify(messages.SERVER_ERROR), 500

    message = messages.LOGGED_OUT
    response = jsonify(message)
    response.set_cookie(SESSION_TOKEN, "", expires=0, httponly=True)
    response.set_cookie("session", "", expires=0, httponly=True)
    return response, 200


@app.route("/notes", methods=["GET", "POST", "PUT"])
@login_required
def notes():
    method = request.method
    current_user = get_current_user_id(request)
    if current_user is None:
        return jsonify(messages.SERVER_ERROR), 500

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
        try:
            res = get_database_result(
                CREDENTIALS_DB,
                f"SELECT COUNT(*) FROM {NOTES_TABLE} WHERE owner_id =(%s)",
                (current_user,),
                fetch=True,
            )
        except psycopg2.Error as e:
            dev_log(e)
            return jsonify(messages.SERVER_ERROR), 500
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


if __name__ == "__main__":
    if ENVIRONMENT == "prod":
        waitress.serve(app, host="0.0.0.0", port=PORT)
    else:
        app.run(host="0.0.0.0", debug=True, port=PORT)
