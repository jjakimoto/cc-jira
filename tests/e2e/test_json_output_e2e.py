"""End-to-end tests verifying --json flag produces valid JSON for all commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


# --- Init ---


def test_json_init(tmp_project):
    """trak --json init returns valid JSON."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "init"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "status" in data


# --- Project ---


def test_json_project_create(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "project", "create", "Test", "--key", "TP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "TP"


def test_json_project_list(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "project", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_json_project_show(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "project", "show", "TP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "TP"
    assert "name" in data
    assert "created_at" in data


def test_json_project_delete(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "project", "delete", "TP", "--force"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "deleted"


# --- Issue ---


def test_json_issue_create(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "create", "Bug fix", "--project", "TP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "TP-1"


def test_json_issue_list(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_json_issue_show(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "show", "TP-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "comments" in data


def test_json_issue_update(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "update", "TP-1", "--status", "in_progress"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "in_progress"


def test_json_issue_delete(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "delete", "TP-1", "--force"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "deleted"


def test_json_issue_comment(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "issue", "comment", "TP-1", "Fixed it"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["body"] == "Fixed it"
    assert "author" in data


# --- Workflow ---


def test_json_workflow_list(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "workflow", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert any(w["name"] == "default" for w in data)


def test_json_workflow_show(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "workflow", "show", "default"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "statuses" in data
    assert "transitions" in data


def test_json_workflow_create(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--json", "workflow", "create", "kanban",
        "--statuses", "backlog,doing,done",
        "--transitions", '{"backlog":["doing"],"doing":["done"],"done":["backlog"]}',
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "kanban"


# --- Search ---


def test_json_search(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test", "--key", "TP"])
    runner.invoke(cli, ["issue", "create", "Bug fix", "--project", "TP"])
    result = runner.invoke(cli, ["--json", "search", "Bug"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


# --- Config ---


def test_json_config_set(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "config", "set", "default.project", "MP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "default.project"
    assert data["value"] == "MP"


def test_json_config_get(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "MP"])
    result = runner.invoke(cli, ["--json", "config", "get", "default.project"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "default.project"
    assert data["value"] == "MP"


def test_json_config_list(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "MP"])
    result = runner.invoke(cli, ["--json", "config", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
