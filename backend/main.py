import os
import random
import sqlite3
import uuid
from flask import Flask, request, jsonify
import waitress
from config import ENVIRONMENT, SECRET_KEY, CREDENTIALS_DB, USERS_TABLE, MAX_PASSWORD_LENGTH
import messages as messages
import argon2

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


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


@app.post("/signup")
def sign_up():
    request_data = request.form
    username = request_data.get("username")
    password = request_data.get("password")
    # TODO: SQL injection here from 'username'. FIX: User prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'SELECT username FROM {USERS_TABLE} WHERE username == "{username}"',
    )
    # Username already taken
    if res.fetchone() is not None:
        return jsonify(messages.USERNAME_TAKEN_ERROR), 409

    password_hash = hash_password(password)
    uuid_value = uuid.uuid4()
    # TODO: SQL injection here from 'username'. FIX: User prepared statement
    res = get_database_result(
        CREDENTIALS_DB,
        f'''INSERT INTO {USERS_TABLE}(id, username, login_hash)
        VALUES ("{uuid_value}", "{username}", "{password_hash}");''',
    )

    return jsonify(messages.USER_CREATED), 201


@app.post("/login")
def login():
    request_data = request.form
    username = request_data.get("username")
    password = request_data.get("password")

    # TODO: SQL injection here from 'username'. FIX: User prepared statement
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

    return jsonify(messages.LOGGED_IN), 200


if __name__ == "__main__":
    if ENVIRONMENT == "prod":
        waitress.serve(app, host="0.0.0.0", port=8080)
    else:
        app.run(debug=True)
