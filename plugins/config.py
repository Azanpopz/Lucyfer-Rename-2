import os
from os import path
from os import getenv
from dotenv import load_dotenv

if os.path.exists("local.env"):
    load_dotenv("local.env")

que = {}
BOT_TOKEN = getenv("BOT_TOKEN")

admins = {}
API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH")
DURATION_LIMIT = int(getenv("DURATION_LIMIT", "15"))
