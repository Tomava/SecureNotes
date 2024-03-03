import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv('ENVIRONMENT')
SECRET_KEY = os.getenv('SECRET_KEY')
CREDENTIALS_DB = "credentials.db"
USERS_TABLE = "users"
MAX_PASSWORD_LENGTH = 128
