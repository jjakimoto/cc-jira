"""SQLite connection manager for trak."""

import sqlite3
from pathlib import Path

import click

TRAK_DIR = ".trak"
DB_NAME = "trak.db"


def get_db_path() -> Path:
    """Walk upward from CWD to find the nearest .trak/trak.db."""
    current = Path.cwd().resolve()
    while True:
        candidate = current / TRAK_DIR / DB_NAME
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            raise click.ClickException(
                "Not a trak project (no .trak/trak.db found in any parent directory). "
                "Run 'trak init' to create one."
            )
        current = parent


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a SQLite connection with Row factory, WAL mode, and foreign keys."""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
