"""End-to-end tests for trak project commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


def test_project_create(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    assert result.exit_code == 0
    assert "TP" in result.output


def test_project_list_shows_created(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["project", "list"])
    assert result.exit_code == 0
    assert "TP" in result.output


def test_project_list_json(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "project", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["key"] == "TP"


def test_project_show(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["project", "show", "TP"])
    assert result.exit_code == 0
    assert "TP" in result.output


def test_project_show_json(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["--json", "project", "show", "TP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "TP"
    assert data["name"] == "Test Project"


def test_project_show_nonexistent(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "show", "NOPE"])
    assert result.exit_code != 0


def test_project_delete_without_force(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["project", "delete", "TP"])
    assert result.exit_code != 0
    assert "--force" in result.output


def test_project_delete_with_force(initialized_project):
    runner = CliRunner()
    runner.invoke(cli, ["project", "create", "Test Project", "--key", "TP"])
    result = runner.invoke(cli, ["project", "delete", "TP", "--force"])
    assert result.exit_code == 0
    # Verify project is gone
    show_result = runner.invoke(cli, ["project", "show", "TP"])
    assert show_result.exit_code != 0


def test_project_create_invalid_key(initialized_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["project", "create", "Bad Project", "--key", "mp"])
    assert result.exit_code != 0
    assert "uppercase" in result.output
