from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv('ENVIRONMENT')
SECRET_KEY = os.getenv('SECRET_KEY')
PORT = os.getenv('PORT')
CREDENTIALS_DB = "credentials.db"
USERS_TABLE = "users"
TOKENS_TABLE = "tokens"
MAX_PASSWORD_LENGTH = 128
ACCESS_EXPIRES = timedelta(hours=1)
