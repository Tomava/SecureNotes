import base64
import time
import pyotp
import requests
import unittest
from config import *
import main

BASE_URI = f"http://{TEST_HOST}:{PORT}"
HASH_PATH = "/hash"
SIGNUP_PATH = "/signup"
LOGIN_PATH = "/login"
LOGOUT_PATH = "/logout"
NOTES_PATH = "/notes"
CSRF_PATH = "/csrf"
OTP_PATH = "/otp"
NON_EXISTING_USER_HASH_PARAMS = {"username": "test2"}
EXISTING_USER_HASH_PARAMS = {"username": "test"}
EXISTING_USER_SIGNUP_PAYLOAD = {
    "username": "test",
    "front_login_hash": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.x3HpsdUHm6tqpzREuBTiQ2pUAzx1Mfa",
    "front_login_salt": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.",
    "encryption_salt": "$2a$10$M9T.i43MfST71mCoWCImEe",
    "encrypted_encryption_key": "U2FsdGVkX1+/Sn8pToAU+nb2BRzZ8j8DyAKNkX4+3dsUIhjBgcjKQEa4SMSjLr282+e72pVWyihVakITL5WXfZybjwqWYGHLMSfvYOd23awuIQ5h2Yq5+a/9ZKWfkriV",
}
NON_EXISTING_USER_SIGNUP_PAYLOAD = {
    "username": "test2",
    "front_login_hash": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.x3HpsdUHm6tqpzREuBTiQ2pUAzx1Mfa",
    "front_login_salt": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.",
    "encryption_salt": "$2a$10$M9T.i43MfST71mCoWCImEe",
    "encrypted_encryption_key": "U2FsdGVkX1+/Sn8pToAU+nb2BRzZ8j8DyAKNkX4+3dsUIhjBgcjKQEa4SMSjLr282+e72pVWyihVakITL5WXfZybjwqWYGHLMSfvYOd23awuIQ5h2Yq5+a/9ZKWfkriV",
}
EXISTING_USER_LOGIN_PAYLOAD = {
    "username": "test",
    "front_login_hash": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.x3HpsdUHm6tqpzREuBTiQ2pUAzx1Mfa",
}
NON_EXISTING_USER_LOGIN_PAYLOAD = {
    "username": "test2",
    "front_login_hash": "$2a$10$siW6Yeb4y1YMPMWC5tjM8.x3HpsdUHm6tqpzREuBTiQ2pUAzx1Mfa",
}
NOTE_PAYLOAD = {"note_title": "EjRWeA==", "note_body": "EjRWeA=="}
REQUEST_TIMEOUT = 10
TRUNCATE_ALL_TABLES = f"TRUNCATE {USERS_TABLE} CASCADE;"


class TestBackend(unittest.TestCase):
    def test_hashing(self):
        hashed_pw = main.hash_password("password")
        self.assertEqual(len(hashed_pw), LOGIN_HASH_LEN)
        self.assertTrue(hashed_pw.startswith("$argon2id$v=19$m=65536,t=3,p=4$"))

    def test_verify(self):
        password = "password"
        hashed_pw = main.hash_password(password)
        self.assertTrue(main.verify_password(hashed_pw, password))


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        time.sleep(3)

    def setUp(self):
        main.get_database_result("", TRUNCATE_ALL_TABLES, ())
        self.session = requests.Session()
        requests.post(
            f"{BASE_URI}/signup",
            json=EXISTING_USER_SIGNUP_PAYLOAD,
            timeout=REQUEST_TIMEOUT,
        )
        # Get session cookie
        self.session.post(
            f"{BASE_URI}{LOGIN_PATH}",
            json=EXISTING_USER_LOGIN_PAYLOAD,
            timeout=REQUEST_TIMEOUT,
        )
        # Get CSRF token
        response = self.session.get(f"{BASE_URI}{CSRF_PATH}", timeout=REQUEST_TIMEOUT)
        self.csrf_token = response.json().get("data").get("csrf_token")
        self.headers = {"X-CSRF-Token": self.csrf_token}
        self.otp_secret = None

    def tearDown(self):
        # Remove OTP
        self.session.delete(
            f"{BASE_URI}{OTP_PATH}", headers=self.headers, timeout=REQUEST_TIMEOUT
        )

    def post_test(self, path, payload, status, use_session=False, headers=None):
        if use_session:
            response = self.session.post(
                f"{BASE_URI}{path}",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        else:
            response = requests.post(
                f"{BASE_URI}{path}",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        self.assertEqual(response.status_code, status)
        return response

    def get_test(self, path, params, status, use_session=False, headers=None):
        if use_session:
            response = self.session.get(
                f"{BASE_URI}{path}",
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        else:
            response = requests.get(
                f"{BASE_URI}{path}",
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
        self.assertEqual(response.status_code, status)
        return response

    def test_hash_non_existing_user(self):
        self.get_test(HASH_PATH, NON_EXISTING_USER_HASH_PARAMS, 404)

    def test_hash_existing_user(self):
        self.get_test(HASH_PATH, EXISTING_USER_HASH_PARAMS, 200)

    def test_signup_non_existing_user(self):
        self.post_test(SIGNUP_PATH, NON_EXISTING_USER_SIGNUP_PAYLOAD, 201)

    def test_signup_existing_user(self):
        self.post_test(SIGNUP_PATH, EXISTING_USER_SIGNUP_PAYLOAD, 409)

    def test_signup_too_long_username(self):
        payload = NON_EXISTING_USER_SIGNUP_PAYLOAD.copy()
        payload["username"] = "a" * (USERNAME_MAX_LEN + 1)
        self.post_test(SIGNUP_PATH, payload, 400)

    def test_signup_invalid_front_login_hash(self):
        payload = NON_EXISTING_USER_SIGNUP_PAYLOAD.copy()
        payload["front_login_hash"] = "a" * 1000
        self.post_test(SIGNUP_PATH, payload, 400)

    def test_signup_invalid_front_login_salt(self):
        payload = NON_EXISTING_USER_SIGNUP_PAYLOAD.copy()
        payload["front_login_salt"] = "a" * 1000
        self.post_test(SIGNUP_PATH, payload, 400)

    def test_signup_invalid_encryption_salt(self):
        payload = NON_EXISTING_USER_SIGNUP_PAYLOAD.copy()
        payload["encryption_salt"] = "a" * 1000
        self.post_test(SIGNUP_PATH, payload, 400)

    def test_signup_invalid_encrypted_encryption_key(self):
        payload = NON_EXISTING_USER_SIGNUP_PAYLOAD.copy()
        payload["encrypted_encryption_key"] = "a" * 1000
        self.post_test(SIGNUP_PATH, payload, 400)

    def test_login_non_existing_user(self):
        self.post_test(LOGIN_PATH, NON_EXISTING_USER_LOGIN_PAYLOAD, 401)

    def test_login_existing_user(self):
        self.post_test(LOGIN_PATH, EXISTING_USER_LOGIN_PAYLOAD, 200)

    def test_csrf_without_session(self):
        response = requests.get(f"{BASE_URI}{CSRF_PATH}", timeout=REQUEST_TIMEOUT)
        self.assertEqual(response.status_code, 401)

    def test_csrf_with_session(self):
        response = self.session.get(f"{BASE_URI}{CSRF_PATH}", timeout=REQUEST_TIMEOUT)
        self.assertEqual(response.status_code, 200)

    def test_notes_get_without_session(self):
        response = requests.get(f"{BASE_URI}{NOTES_PATH}", timeout=REQUEST_TIMEOUT)
        self.assertEqual(response.status_code, 401)

    def test_notes_get_with_session(self):
        response = self.session.get(f"{BASE_URI}{NOTES_PATH}", timeout=REQUEST_TIMEOUT)
        self.assertEqual(response.status_code, 200)

    def test_notes_post_without_session(self):
        self.post_test(NOTES_PATH, NOTE_PAYLOAD, 400)

    def test_notes_post_with_session_without_csrf(self):
        self.post_test(NOTES_PATH, NOTE_PAYLOAD, 400, True)

    def test_notes_post_with_session_with_csrf(self):
        self.post_test(NOTES_PATH, NOTE_PAYLOAD, 201, True, self.headers)

    # def test_notes_post_too_many(self):
    #     for _ in range(MAX_NOTES):
    #         self.post_test(NOTES_PATH, NOTE_PAYLOAD, 201, True, self.headers)
    #     self.post_test(NOTES_PATH, NOTE_PAYLOAD, 413, True, self.headers)

    def test_too_large_note(self):
        payload = NOTE_PAYLOAD.copy()
        payload["note_title"] = ""
        payload["note_body"] = base64.b64encode(bytearray([1] * (MAX_SIZE))).decode("utf-8")
        self.post_test(NOTES_PATH, payload, 201, True, self.headers)
        payload["note_body"] = base64.b64encode(bytearray([1] * (MAX_SIZE + 1))).decode("utf-8")
        self.post_test(NOTES_PATH, payload, 413, True, self.headers)

        payload["note_body"] = ""
        payload["note_title"] = base64.b64encode(bytearray([1] * (MAX_SIZE))).decode("utf-8")
        self.post_test(NOTES_PATH, payload, 201, True, self.headers)
        payload["note_title"] = base64.b64encode(bytearray([1] * (MAX_SIZE + 1))).decode("utf-8")
        self.post_test(NOTES_PATH, payload, 413, True, self.headers)

    def test_logout_without_session(self):
        self.post_test(LOGOUT_PATH, {}, 400)

    def test_logout_with_session_without_csrf(self):
        self.post_test(LOGOUT_PATH, {}, 400, True)

    def test_logout_with_session_with_csrf(self):
        self.post_test(LOGOUT_PATH, {}, 200, True, self.headers)

    def test_otp_post_without_session(self):
        self.post_test(OTP_PATH, {}, 400)

    def test_otp_post_with_session_without_csrf(self):
        self.post_test(OTP_PATH, {}, 400, True)

    def test_otp_post_with_session_with_csrf(self):
        # Add OTP
        response = self.post_test(OTP_PATH, {}, 201, True, self.headers)
        self.otp_secret = response.json().get("data").get("otp_secret")

    def test_otp_get_without_session(self):
        self.get_test(OTP_PATH, {}, 401)

    def test_otp_get_with_session_not_added(self):
        self.get_test(OTP_PATH, {}, 404, True)

    def test_otp_with_session(self):
        # Add OTP
        self.test_otp_post_with_session_with_csrf()
        self.get_test(OTP_PATH, {}, 200, True)

    def test_login_existing_user_without_correct_otp(self):
        # Add OTP
        self.test_otp_post_with_session_with_csrf()
        payload = EXISTING_USER_LOGIN_PAYLOAD.copy()
        payload["otp_code"] = "9999999"
        self.post_test(LOGIN_PATH, payload, 401)

    def test_login_existing_user_with_missing_otp(self):
        # Add OTP
        self.test_otp_post_with_session_with_csrf()
        self.post_test(LOGIN_PATH, EXISTING_USER_LOGIN_PAYLOAD, 401)

    def test_login_existing_user_with_correct_otp(self):
        # Add OTP
        self.test_otp_post_with_session_with_csrf()
        payload = EXISTING_USER_LOGIN_PAYLOAD.copy()
        payload["otp_code"] = pyotp.totp.TOTP(self.otp_secret).now()
        self.post_test(LOGIN_PATH, payload, 200)

    def test_invalid_csrf(self):
        headers = {"X-CSRF-Token": "abcd"}
        self.post_test(NOTES_PATH, NOTE_PAYLOAD, 400, True, headers)


if __name__ == "__main__":
    unittest.main()
