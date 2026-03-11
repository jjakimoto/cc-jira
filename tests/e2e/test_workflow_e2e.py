"""End-to-end tests for trak workflow commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


def test_workflow_list(initialized_project):
    """trak workflow list shows the default workflow."""
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "list"])
    assert result.exit_code == 0
    assert "default" in result.output


def test_workflow_list_json(initialized_project):
    """trak --json workflow list returns JSON array with default workflow."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "workflow", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1
    names = [w["name"] for w in data]
    assert "default" in names


def test_workflow_show_default(initialized_project):
    """trak workflow show default displays statuses and transitions."""
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "show", "default"])
    assert result.exit_code == 0
    assert "todo" in result.output
    assert "in_progress" in result.output
    assert "in_review" in result.output
    assert "done" in result.output
    # Should show transitions
    assert "->" in result.output


def test_workflow_show_json(initialized_project):
    """JSON output of workflow show includes statuses and transitions."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "workflow", "show", "default"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "statuses" in data
    assert "transitions" in data
    assert "todo" in data["statuses"]
    assert "in_progress" in data["statuses"]
    assert "in_review" in data["statuses"]
    assert "done" in data["statuses"]
    assert "cancelled" in data["statuses"]
    # Check transitions dict
    assert "todo" in data["transitions"]
    assert "in_progress" in data["transitions"]["todo"]


def test_workflow_create_custom(initialized_project):
    """Create a kanban workflow and verify it appears in list."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "workflow", "create", "kanban",
        "--statuses", "backlog,doing,done",
        "--transitions", '{"backlog":["doing"],"doing":["done"],"done":["backlog"]}',
    ])
    assert result.exit_code == 0

    # Verify it appears in list
    list_result = runner.invoke(cli, ["--json", "workflow", "list"])
    assert list_result.exit_code == 0
    data = json.loads(list_result.output)
    names = [w["name"] for w in data]
    assert "kanban" in names


def test_issue_valid_transition(initialized_project):
    """Issue status update todo->in_progress succeeds."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Test issue", "--project", "TP"])

    result = runner.invoke(cli, ["--json", "issue", "update", "TP-1", "--status", "in_progress"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "in_progress"


def test_issue_invalid_transition(initialized_project):
    """Issue status update todo->done fails with error message."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Test issue", "--project", "TP"])

    result = runner.invoke(cli, ["issue", "update", "TP-1", "--status", "done"])
    assert result.exit_code != 0
    assert "Cannot transition" in result.output


def test_issue_transition_chain(initialized_project):
    """Full transition chain todo->in_progress->in_review->done works."""
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Chain test", "--project", "TP"])

    # todo -> in_progress
    result = runner.invoke(cli, ["issue", "update", "TP-1", "--status", "in_progress"])
    assert result.exit_code == 0

    # in_progress -> in_review
    result = runner.invoke(cli, ["issue", "update", "TP-1", "--status", "in_review"])
    assert result.exit_code == 0

    # in_review -> done
    result = runner.invoke(cli, ["issue", "update", "TP-1", "--status", "done"])
    assert result.exit_code == 0


def test_workflow_show_nonexistent(initialized_project):
    """Show for nonexistent workflow returns error."""
    runner = CliRunner()
    result = runner.invoke(cli, ["workflow", "show", "nonexistent"])
    assert result.exit_code != 0
