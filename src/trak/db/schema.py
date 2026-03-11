"""Database schema definitions and seed data for trak."""

import sqlite3
from pathlib import Path

from trak.db.connection import get_connection

_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    number INTEGER NOT NULL,
    type TEXT NOT NULL DEFAULT 'task',
    summary TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'p2',
    assignee TEXT,
    labels TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, number)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'default',
    status TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    is_default INTEGER NOT NULL DEFAULT 0,
    UNIQUE(name, status)
);

CREATE TABLE IF NOT EXISTS workflow_transitions (
    id INTEGER PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    UNIQUE(workflow_name, from_status, to_status)
);

CREATE TABLE IF NOT EXISTS config (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_DEFAULT_WORKFLOW = [
    ("default", "todo", 0, 1),
    ("default", "in_progress", 1, 0),
    ("default", "in_review", 2, 0),
    ("default", "done", 3, 0),
    ("default", "cancelled", 4, 0),
]

_DEFAULT_TRANSITIONS = [
    ("default", "todo", "in_progress"),
    ("default", "in_progress", "in_review"),
    ("default", "in_review", "done"),
    ("default", "todo", "cancelled"),
    ("default", "in_progress", "cancelled"),
    ("default", "in_review", "cancelled"),
    ("default", "done", "cancelled"),
]


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all trak tables if they don't exist."""
    conn.executescript(_TABLES_SQL)


def seed_default_workflow(conn: sqlite3.Connection) -> None:
    """Insert default workflow statuses if the workflows table is empty."""
    row = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()
    if row[0] == 0:
        conn.executemany(
            "INSERT INTO workflows (name, status, position, is_default) VALUES (?, ?, ?, ?)",
            _DEFAULT_WORKFLOW,
        )


def seed_default_transitions(conn: sqlite3.Connection) -> None:
    """Insert default workflow transitions if the table is empty."""
    row = conn.execute("SELECT COUNT(*) FROM workflow_transitions").fetchone()
    if row[0] == 0:
        conn.executemany(
            "INSERT INTO workflow_transitions (workflow_name, from_status, to_status) VALUES (?, ?, ?)",
            _DEFAULT_TRANSITIONS,
        )


def init_db(db_path: Path) -> None:
    """Create tables and seed default data."""
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        seed_default_workflow(conn)
        seed_default_transitions(conn)
        conn.commit()
    finally:
        conn.close()
