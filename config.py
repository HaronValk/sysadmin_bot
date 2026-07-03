import os

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
INITIAL_BALANCE = 4.0
MINI_APP_URL = "https://syssrgmlg.duckdns.org"
LESSONS_PER_PAGE = 10
MAX_PART = 3500
DB_PATH = "cache.db"
