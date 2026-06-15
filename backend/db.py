"""
Database connection — MySQL (RA database)
Reads credentials from .env via config.py
Compatible with both:
  - Running from project root: uvicorn backend.main:app
  - Running scripts directly from backend/: python seed_faculty.py
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)


def _build_url():
    """
    Tries to import config from backend.config (when running from project root)
    and falls back to reading .env directly (when running from backend/ dir).
    """
    try:
        from backend.config import config
        return config.DATABASE_URL, config.DB_NAME
    except ModuleNotFoundError:
        pass

    # Fallback: read .env manually
    from pathlib import Path
    from urllib.parse import quote_plus

    env_path = Path(__file__).parent / ".env"
    env_vars = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                env_vars[key.strip()] = val.strip()

    db_user     = env_vars.get("DB_USER", "root")
    db_password = env_vars.get("DB_PASSWORD", "")
    db_host     = env_vars.get("DB_HOST", "127.0.0.1")
    db_port     = env_vars.get("DB_PORT", "3306")
    db_name     = env_vars.get("DB_NAME", "RA")

    url = (
        f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    return url, db_name


DATABASE_URL, DB_NAME = _build_url()

# -----------------------------------------------------------------------
# Engine & Session
# -----------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # auto-reconnect on stale connections
    pool_recycle=3600,      # recycle connections every hour
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_connection():
    """Call once at startup to confirm MySQL is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ MySQL connection verified — database: %s", DB_NAME)
        return True
    except Exception as e:
        logger.error("❌ MySQL connection FAILED: %s", e)
        return False
