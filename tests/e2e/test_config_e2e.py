"""End-to-end tests for trak config commands."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


def test_config_set_and_get(initialized_project):
    """Set default.project to MP, then get it, verify output contains MP."""
    runner = CliRunner()
    set_result = runner.invoke(cli, ["config", "set", "default.project", "MP"])
    assert set_result.exit_code == 0

    get_result = runner.invoke(cli, ["config", "get", "default.project"])
    assert get_result.exit_code == 0
    assert "MP" in get_result.output


def test_config_set_and_get_json(initialized_project):
    """Set and get with --json, verify JSON output has key and value fields."""
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "MP"])

    result = runner.invoke(cli, ["--json", "config", "get", "default.project"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "default.project"
    assert data["value"] == "MP"


def test_config_get_nonexistent(initialized_project):
    """Get a key that was never set, verify exit_code != 0 and error message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "get", "nonexistent.key"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_config_set_overwrites(initialized_project):
    """Set same key twice with different values, verify second value is returned."""
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "OLD"])
    runner.invoke(cli, ["config", "set", "default.project", "NEW"])

    result = runner.invoke(cli, ["--json", "config", "get", "default.project"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["value"] == "NEW"


def test_config_list(initialized_project):
    """Set multiple config keys, verify config list shows all of them."""
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "MP"])
    runner.invoke(cli, ["config", "set", "default.assignee", "tom"])

    result = runner.invoke(cli, ["config", "list"])
    assert result.exit_code == 0
    assert "default.assignee" in result.output
    assert "default.project" in result.output


def test_config_list_json(initialized_project):
    """Set multiple config keys, verify JSON array output."""
    runner = CliRunner()
    runner.invoke(cli, ["config", "set", "default.project", "MP"])
    runner.invoke(cli, ["config", "set", "default.assignee", "tom"])

    result = runner.invoke(cli, ["--json", "config", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    keys = {d["key"] for d in data}
    assert keys == {"default.assignee", "default.project"}


def test_config_list_empty(initialized_project):
    """Verify config list works when no config is set (empty result)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--json", "config", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 0
