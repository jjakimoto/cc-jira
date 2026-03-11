"""End-to-end tests for trak init."""

import json
import sqlite3

from click.testing import CliRunner

from trak.cli.main import cli


def test_init_creates_db(tmp_project):
    """trak init creates .trak/trak.db."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert (tmp_project / ".trak" / "trak.db").exists()


def test_init_creates_all_tables(initialized_project):
    """All 4 tables exist after init."""
    db_path = initialized_project / ".trak" / "trak.db"
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    table_names = [r[0] for r in rows]
    assert "projects" in table_names
    assert "issues" in table_names
    assert "comments" in table_names
    assert "workflows" in table_names


def test_init_seeds_default_workflow(initialized_project):
    """Default workflow has 5 statuses after init."""
    db_path = initialized_project / ".trak" / "trak.db"
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT status, position, is_default FROM workflows WHERE name='default' ORDER BY position"
    ).fetchall()
    conn.close()
    assert len(rows) == 5
    assert rows[0] == ("todo", 0, 1)
    assert rows[1] == ("in_progress", 1, 0)
    assert rows[2] == ("in_review", 2, 0)
    assert rows[3] == ("done", 3, 0)
    assert rows[4] == ("cancelled", 4, 0)


def test_init_already_initialized(initialized_project):
    """Running init twice shows already-initialized message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Already initialized" in result.output


def test_help_exits_zero(tmp_project):
    """trak --help exits with code 0."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_init_json_output(tmp_project):
    """trak --json init outputs JSON confirmation."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "init"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "initialized"
    assert "path" in data


def test_init_already_initialized_json(initialized_project):
    """trak --json init on existing project returns JSON with already_initialized."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "init"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "already_initialized"
