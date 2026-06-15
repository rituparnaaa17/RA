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
    Build the SQLAlchemy database URL.
    Priority:
      1. DATABASE_URL env var (set manually in Railway Variables tab)
      2. Railway's auto-injected MYSQLHOST / MYSQLUSER / etc. env vars
      3. Read .env file (local dev fallback)
    """
    from urllib.parse import quote_plus

    # ── 1. Explicit DATABASE_URL ──────────────────────────────────────────────
    raw = os.getenv("DATABASE_URL", "")
    if raw:
        # Railway/PlanetScale give "mysql://" but SQLAlchemy needs "mysql+pymysql://"
        if raw.startswith("mysql://"):
            raw = raw.replace("mysql://", "mysql+pymysql://", 1)
        logger.info("Using DATABASE_URL from environment.")
        return raw, ""

    # ── 2. Railway auto-injected individual vars ──────────────────────────────
    mysql_host = os.getenv("MYSQLHOST", "")
    if mysql_host:
        user     = quote_plus(os.getenv("MYSQLUSER",     "root"))
        password = quote_plus(os.getenv("MYSQLPASSWORD", ""))
        host     = os.getenv("MYSQLHOST",     "127.0.0.1")
        port     = os.getenv("MYSQLPORT",     "3306")
        db_name  = os.getenv("MYSQLDATABASE", "railway")
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"
        logger.info("Using Railway MYSQL* env vars. host=%s db=%s", host, db_name)
        return url, db_name

    # ── 3. Read .env file (local development) ────────────────────────────────
    from pathlib import Path
    env_path = Path(__file__).parent / ".env"
    env_vars: dict = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                env_vars[key.strip()] = val.strip()

    db_user     = env_vars.get("DB_USER",     "root")
    db_password = env_vars.get("DB_PASSWORD", "")
    db_host     = env_vars.get("DB_HOST",     "127.0.0.1")
    db_port     = env_vars.get("DB_PORT",     "3306")
    db_name     = env_vars.get("DB_NAME",     "RA")

    url = (
        f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    logger.info("Using .env file for DB config. host=%s db=%s", db_host, db_name)
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
