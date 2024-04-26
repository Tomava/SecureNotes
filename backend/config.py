from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
SECRET_KEY = os.getenv("SECRET_KEY")
PORT = os.getenv("PORT") or 5000
TEST_HOST = os.getenv("TEST_HOST") or "localhost"
CREDENTIALS_DB = "credentials.db"
USERS_TABLE = "users"
TOKENS_TABLE = "tokens"
NOTES_TABLE = "notes"
MAX_PASSWORD_LENGTH = 128
ACCESS_EXPIRES = timedelta(hours=1)
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")
DATABASE_PEPPER = os.getenv("DATABASE_PEPPER")
SESSION_TOKEN = "session_token"

USERNAME_MAX_LEN = 20
FRONT_LOGIN_HASH_LEN = 60
LOGIN_HASH_LEN = 97
FRONT_LOGIN_SALT_LEN = 29
ENCRYPTION_SALT_LEN = 29
ENCRYPTED_ENCRYPTION_KEY_LEN = 128
MAX_SIZE = 5_000_000
MAX_NOTES = 200
