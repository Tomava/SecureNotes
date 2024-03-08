from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT")
SECRET_KEY = os.getenv("SECRET_KEY")
PORT = os.getenv("PORT")
CREDENTIALS_DB = "credentials.db"
USERS_TABLE = "users"
TOKENS_TABLE = "tokens"
MAX_PASSWORD_LENGTH = 128
ACCESS_EXPIRES = timedelta(hours=1)
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")
