"""Configuration and database connectivity.

Every secret is read from .env — nothing is hardcoded, and .env is gitignored.
The only credential this module ever handles is the one the user puts in their
own .env file; it is never logged, only masked.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_DIR = PROJECT_ROOT / "sql"
QUERY_DIR = SQL_DIR / "queries"
REPORT_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or obviously a placeholder."""


def use_utf8_console() -> None:
    """Stop the Windows console from killing the run on a non-ASCII character.

    Python on Windows defaults stdout to the legacy cp1252 code page, so
    printing an em-dash or a status emoji raises UnicodeEncodeError and takes
    the whole pipeline down *after* the data has already loaded successfully.
    A reporting detail should never be able to fail a load, so re-encode as
    UTF-8 and degrade unmappable characters instead of raising.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # pragma: no cover - redirected stream
                pass


def get_database_url() -> str:
    """Return the SQLAlchemy URL, failing loudly rather than half-working."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ConfigError(
            "DATABASE_URL is not set.\n"
            f"  Copy {PROJECT_ROOT / '.env.example'} to .env and fill in your "
            "Supabase/RDS connection string."
        )
    if "user:password@host" in url:
        raise ConfigError(
            "DATABASE_URL is still the placeholder from .env.example. "
            "Replace it with your real connection string."
        )
    # psycopg2 is not installed (and has no Python 3.14 wheels); silently
    # upgrade the bare scheme to psycopg 3 so a copy-pasted Supabase URI works.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def mask_url(url: str) -> str:
    """Hide the password so a URL can appear in logs and screenshots safely."""
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:****@", url)


def get_engine(echo: bool = False) -> Engine:
    """Create a pooled engine.

    pool_pre_ping matters on Supabase: the connection pooler drops idle
    connections, and without it the first query after a pause dies with a
    stale-connection error instead of transparently reconnecting.
    """
    return create_engine(
        get_database_url(),
        echo=echo,
        pool_pre_ping=True,
        future=True,
        connect_args={"connect_timeout": 30},
    )


def get_raw_csv_path() -> Path:
    raw = os.getenv("RAW_CSV_PATH", "data/raw/superstore.csv")
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def get_chunk_size() -> int:
    try:
        return max(100, int(os.getenv("LOAD_CHUNK_SIZE", "1000")))
    except ValueError:
        return 1000
