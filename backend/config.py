
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class Config:
    # Database
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "RA")
    
    # Construct MySQL URL if env vars exist, else fallback or use what is set in DATABASE_URL
    # Priority: Constructed MySQL URL > Explicit DATABASE_URL > SQLite default
    from urllib.parse import quote_plus
    _MYSQL_URL = f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # If users provide specific DATABASE_URL in env, use that, otherwise use constructed MySQL string
    DATABASE_URL = os.getenv("DATABASE_URL", _MYSQL_URL)
    
    # Auuth
    AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "mysupersecret")
    AUTH_DISABLED = os.getenv("AUTH_DISABLED", "false").lower() == "true"
    
    # Paths
    UPLOAD_DIR = os.path.join(os.getcwd(), "backend", "uploads")
    
    # Create upload directory if it doesn't exist
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

config = Config()
