"""
Database connection — MySQL (RA database)
Reads credentials from .env via python-dotenv locally,
and from Render's env var UI in production.

SSL:
  Set DB_SSL_CA to the path of Aiven's downloaded ca.pem to enable SSL.
  On Render, upload ca.pem as a Secret File and set DB_SSL_CA to its path.

pool_recycle=280:
  Aiven free-tier (and Render free-tier) both drop idle connections after
  ~300 s.  Recycling at 280 s prevents "MySQL server has gone away" errors.
"""
import logging
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# ── Load .env for local development (no-op in production) ────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)


# ── Build database URL ────────────────────────────────────────────────────────
def _build_url() -> tuple[str, dict]:
    """
    Build (DATABASE_URL, connect_args).

    Priority:
      1. MYSQL_PUBLIC_URL or DATABASE_URL  (Railway / PlanetScale style)
      2. Individual DB_* env vars          (Aiven / Render style)
    Returns connect_args with SSL dict when DB_SSL_CA is set.
    """
    # 1. Explicit full URL
    raw = os.getenv("MYSQL_PUBLIC_URL") or os.getenv("DATABASE_URL", "")
    if raw:
        if raw.startswith("mysql://"):
            raw = raw.replace("mysql://", "mysql+pymysql://", 1)
        logger.info("Using DATABASE_URL/MYSQL_PUBLIC_URL from environment.")
        return raw, _ssl_args()

    # 2. Individual DB_* vars (Aiven / Render env var tab)
    db_user     = os.getenv("DB_USER",     "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host     = os.getenv("DB_HOST",     "127.0.0.1")
    db_port     = os.getenv("DB_PORT",     "3306")
    db_name     = os.getenv("DB_NAME",     "RA")

    url = (
        f"mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    logger.info("Using DB_* env vars. host=%s db=%s", db_host, db_name)
    return url, _ssl_args()


def _ssl_args() -> dict:
    """Return connect_args dict with SSL CA if DB_SSL_CA is set."""
    ca = os.getenv("DB_SSL_CA", "")
    if ca and Path(ca).exists():
        logger.info("SSL enabled with CA: %s", ca)
        return {"ssl": {"ca": ca}}
    if ca:
        logger.warning("DB_SSL_CA is set to '%s' but file not found — SSL skipped.", ca)
    return {}


DATABASE_URL, _connect_args = _build_url()

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,    # detect stale connections before use
    pool_recycle=280,      # recycle before Aiven/Render 300 s idle timeout
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


def verify_connection() -> bool:
    """Call once at startup to confirm MySQL is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ MySQL connection verified.")
        return True
    except Exception as e:
        logger.error("❌ MySQL connection FAILED: %s", e)
        return False
