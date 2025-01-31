from dotenv import load_dotenv
import os

load_dotenv()

APP_ID = os.getenv('APP_ID')
APP_SECRET = os.getenv('APP_SECRET')
ENCRYPT_KEY = os.getenv('ENCRYPT_KEY')
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
