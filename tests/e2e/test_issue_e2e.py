"""End-to-end tests for trak issue commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


def _create_project(runner, name="My Project", key="MP"):
    """Helper to create a project for issue tests."""
    result = runner.invoke(cli, ["project", "create", name, "--key", key])
    assert result.exit_code == 0
    return result


def test_issue_create(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    result = runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    assert result.exit_code == 0
    assert "MP-1" in result.output


def test_issue_create_auto_numbering(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    r1 = runner.invoke(cli, ["issue", "create", "First issue", "--project", "MP"])
    assert r1.exit_code == 0
    assert "MP-1" in r1.output
    r2 = runner.invoke(cli, ["issue", "create", "Second issue", "--project", "MP"])
    assert r2.exit_code == 0
    assert "MP-2" in r2.output


def test_issue_list_table(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["issue", "list"])
    assert result.exit_code == 0
    assert "MP-1" in result.output


def test_issue_list_json(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["--json", "issue", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["key"] == "MP-1"


def test_issue_list_project_filter(initialized_project):
    runner = CliRunner()
    _create_project(runner, "Project A", "PA")
    _create_project(runner, "Project B", "PB")
    runner.invoke(cli, ["issue", "create", "PA issue", "--project", "PA"])
    runner.invoke(cli, ["issue", "create", "PB issue", "--project", "PB"])
    result = runner.invoke(cli, ["--json", "issue", "list", "--project", "PA"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["key"] == "PA-1"


def test_issue_show(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["issue", "show", "MP-1"])
    assert result.exit_code == 0
    assert "MP-1" in result.output


def test_issue_show_json(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP", "--type", "bug", "--priority", "p1"])
    result = runner.invoke(cli, ["--json", "issue", "show", "MP-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "MP-1"
    assert data["summary"] == "Fix bug"
    assert data["type"] == "bug"
    assert data["priority"] == "p1"


def test_issue_update(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(
        cli, ["--json", "issue", "update", "MP-1", "--status", "in_progress", "--assignee", "tom"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "in_progress"
    assert data["assignee"] == "tom"


def test_issue_delete_without_force(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["issue", "delete", "MP-1"])
    assert result.exit_code != 0
    assert "--force" in result.output


def test_issue_delete_with_force(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["issue", "delete", "MP-1", "--force"])
    assert result.exit_code == 0
    # Verify issue is gone
    show_result = runner.invoke(cli, ["issue", "show", "MP-1"])
    assert show_result.exit_code != 0


def test_issue_comment(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    result = runner.invoke(cli, ["issue", "comment", "MP-1", "Fixed in commit abc"])
    assert result.exit_code == 0
    assert "Comment added" in result.output


def test_issue_show_includes_comment(initialized_project):
    runner = CliRunner()
    _create_project(runner)
    runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "MP"])
    runner.invoke(cli, ["issue", "comment", "MP-1", "Fixed in commit abc"])
    result = runner.invoke(cli, ["--json", "issue", "show", "MP-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["comments"]) == 1
    assert data["comments"][0]["body"] == "Fixed in commit abc"


def test_issue_create_invalid_project(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["issue", "create", "Fix bug", "--project", "NOPE"])
    assert result.exit_code != 0
    assert "not found" in result.output
