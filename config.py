from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DOWNLOAD_DIR = BASE_DIR / "downloads"
TOKEN_FILE = BASE_DIR / "token.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
DATABASE_FILE = DATA_DIR / "nexora.db"

DATA_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)


# Gmail permission
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


# تعداد ایمیل‌هایی که در هر اجرا بررسی می‌شوند
MAX_EMAILS = 100