"""End-to-end tests for error handling across all commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


# --- Missing database errors (use tmp_project — no trak init) ---


def test_missing_db_project_list(tmp_project):
    """trak project list without .trak/ shows helpful error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list"])
    assert result.exit_code != 0
    assert "trak init" in result.output


def test_missing_db_issue_list(tmp_project):
    """trak issue list without .trak/ shows helpful error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["issue", "list"])
    assert result.exit_code != 0
    assert "trak init" in result.output


def test_missing_db_search(tmp_project):
    """trak search without .trak/ shows helpful error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "foo"])
    assert result.exit_code != 0
    assert "trak init" in result.output


def test_missing_db_config_get(tmp_project):
    """trak config get without .trak/ shows helpful error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "get", "x"])
    assert result.exit_code != 0
    assert "trak init" in result.output


# --- Invalid input errors (use initialized_project) ---


def test_invalid_project_key(initialized_project):
    """Lowercase project key fails with uppercase error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "create", "Bad", "--key", "mp"])
    assert result.exit_code != 0
    assert "uppercase" in result.output


def test_issue_create_nonexistent_project(initialized_project):
    """Creating issue for nonexistent project fails."""
    runner = CliRunner()
    result = runner.invoke(cli, ["issue", "create", "Foo", "--project", "NOPE"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_issue_update_nonexistent(initialized_project):
    """Updating nonexistent issue fails."""
    runner = CliRunner()
    result = runner.invoke(cli, ["issue", "update", "NOPE-1", "--status", "todo"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_issue_invalid_transition(initialized_project):
    """Invalid status transition fails with error listing valid transitions."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "MP"])
    runner.invoke(cli, ["issue", "create", "Test issue", "--project", "MP"])

    result = runner.invoke(cli, ["issue", "update", "MP-1", "--status", "done"])
    assert result.exit_code != 0
    assert "Cannot transition" in result.output


def test_workflow_show_nonexistent(initialized_project):
    """Showing nonexistent workflow fails."""
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "show", "nope"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_workflow_create_invalid_transitions(initialized_project):
    """Creating workflow with invalid transition references fails."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "workflow", "create", "bad",
        "--statuses", "a,b",
        "--transitions", '{"a":["c"]}',
    ])
    assert result.exit_code != 0
    assert "unknown status" in result.output.lower() or "error" in result.output.lower()


def test_issue_delete_no_force(initialized_project):
    """Deleting issue without --force shows error."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "MP"])
    runner.invoke(cli, ["issue", "create", "Test", "--project", "MP"])

    result = runner.invoke(cli, ["issue", "delete", "MP-1"])
    assert result.exit_code != 0
    assert "--force" in result.output


def test_project_delete_no_force(initialized_project):
    """Deleting project without --force shows error."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "MP"])

    result = runner.invoke(cli, ["project", "delete", "MP"])
    assert result.exit_code != 0
    assert "--force" in result.output
