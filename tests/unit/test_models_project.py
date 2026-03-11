"""Unit tests for the Project model."""

import sqlite3

import pytest

from trak.db.schema import create_tables, seed_default_workflow
from trak.models.project import Project


@pytest.fixture
def db_conn():
    """In-memory SQLite database with trak schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    create_tables(conn)
    seed_default_workflow(conn)
    conn.commit()
    yield conn
    conn.close()


def test_create_returns_correct_fields(db_conn):
    proj = Project.create(db_conn, key="TEST", name="Test Project", description="A test")
    assert proj.key == "TEST"
    assert proj.name == "Test Project"
    assert proj.description == "A test"
    assert proj.id is not None
    assert proj.created_at is not None
    assert proj.updated_at is not None


def test_get_by_key_returns_project(db_conn):
    Project.create(db_conn, key="FIND", name="Find Me")
    proj = Project.get_by_key(db_conn, "FIND")
    assert proj is not None
    assert proj.key == "FIND"
    assert proj.name == "Find Me"


def test_get_by_key_returns_none_for_nonexistent(db_conn):
    proj = Project.get_by_key(db_conn, "NOPE")
    assert proj is None


def test_list_all_returns_all_projects(db_conn):
    Project.create(db_conn, key="AA", name="First")
    Project.create(db_conn, key="BB", name="Second")
    projects = Project.list_all(db_conn)
    assert len(projects) == 2
    keys = {p.key for p in projects}
    assert keys == {"AA", "BB"}


def test_delete_removes_project(db_conn):
    Project.create(db_conn, key="DEL", name="Delete Me")
    Project.delete(db_conn, "DEL")
    assert Project.get_by_key(db_conn, "DEL") is None


def test_delete_raises_for_nonexistent(db_conn):
    with pytest.raises(KeyError):
        Project.delete(db_conn, "NOPE")


def test_key_validation_rejects_lowercase(db_conn):
    with pytest.raises(ValueError, match="uppercase"):
        Project.create(db_conn, key="bad", name="Bad")


def test_key_validation_rejects_too_short(db_conn):
    with pytest.raises(ValueError, match="2-10"):
        Project.create(db_conn, key="A", name="Short")


def test_key_validation_rejects_too_long(db_conn):
    with pytest.raises(ValueError, match="2-10"):
        Project.create(db_conn, key="ABCDEFGHIJK", name="Long")


def test_duplicate_key_raises(db_conn):
    Project.create(db_conn, key="DUP", name="First")
    with pytest.raises(sqlite3.IntegrityError):
        Project.create(db_conn, key="DUP", name="Second")
