import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SQL_URL = (
    os.getenv("SQL")
    if os.getenv("SQL") is not None
    else "sqlite+aiosqlite:///./deadlines.sqlite"
)
