"""End-to-end tests for trak search command."""

import json

from click.testing import CliRunner

from trak.cli.main import cli


def _setup_test_data(runner):
    """Create a project and several issues with varying attributes for search tests."""
    runner.invoke(cli, ["project", "create", "My Project", "--key", "MP"])

    # Issue 1: open bug, p0, assigned to tom, label=backend
    runner.invoke(
        cli,
        [
            "issue", "create", "Fix login bug",
            "--project", "MP",
            "--type", "bug",
            "--priority", "p0",
            "--assignee", "tom",
            "--labels", "backend",
            "--description", "Fix the login page authentication flow",
        ],
    )

    # Issue 2: in_progress task, p1, assigned to alice, label=frontend
    runner.invoke(
        cli,
        [
            "issue", "create", "Build dashboard",
            "--project", "MP",
            "--type", "task",
            "--priority", "p1",
            "--assignee", "alice",
            "--labels", "frontend",
            "--description", "Create the main dashboard view",
        ],
    )

    # Issue 3: open story, p2, assigned to tom, label=backend,api
    runner.invoke(
        cli,
        [
            "issue", "create", "Add API endpoint",
            "--project", "MP",
            "--type", "story",
            "--priority", "p2",
            "--assignee", "tom",
            "--labels", "backend,api",
            "--description", "A detailed description text for searching",
        ],
    )

    # Update issue 2 status to in_progress
    runner.invoke(cli, ["issue", "update", "MP-2", "--status", "in_progress"])

    # Issue 4: resolved bug, p1, no assignee, label=frontend
    runner.invoke(
        cli,
        [
            "issue", "create", "Fix CSS alignment",
            "--project", "MP",
            "--type", "bug",
            "--priority", "p1",
            "--labels", "frontend",
        ],
    )
    # Update status to resolved
    runner.invoke(cli, ["issue", "update", "MP-4", "--status", "resolved"])

    # Issue 5: open task, p3, assigned to bob, no labels
    runner.invoke(
        cli,
        [
            "issue", "create", "Write documentation",
            "--project", "MP",
            "--type", "task",
            "--priority", "p3",
            "--assignee", "bob",
        ],
    )


def test_search_status_filter(initialized_project):
    """trak search "status:open" returns only open issues."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "status:open"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3
    for issue in data:
        assert issue["status"] == "open"


def test_search_priority_comma_or(initialized_project):
    """trak search "priority:p0,p1" returns issues with either priority."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "priority:p0,p1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3
    priorities = {d["priority"] for d in data}
    assert priorities <= {"p0", "p1"}


def test_search_combined_filters(initialized_project):
    """trak search "type:bug status:open" combines filters with AND."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "type:bug status:open"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["type"] == "bug"
    assert data[0]["status"] == "open"
    assert data[0]["summary"] == "Fix login bug"


def test_search_free_text_summary(initialized_project):
    """trak search "login" matches issue with "login" in summary."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "login"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert "login" in data[0]["summary"].lower()


def test_search_free_text_description(initialized_project):
    """trak search "detailed description text" matches issue with text in description."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "detailed description text"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert "detailed description text" in data[0]["description"].lower()


def test_search_date_range(initialized_project):
    """trak search "created:>2020-01-01" returns all issues (all created after that date)."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "created:>2020-01-01"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 5


def test_search_project_scope(initialized_project):
    """trak search "assignee:tom" --project MP scopes to project."""
    runner = CliRunner()
    _setup_test_data(runner)

    # Create a second project with an issue assigned to tom
    runner.invoke(cli, ["project", "create", "Other Project", "--key", "OP"])
    runner.invoke(
        cli,
        [
            "issue", "create", "OP task",
            "--project", "OP",
            "--assignee", "tom",
        ],
    )

    # Search with project scope should only return MP issues
    result = runner.invoke(cli, ["--json", "search", "assignee:tom", "--project", "MP"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    for issue in data:
        assert issue["key"].startswith("MP-")

    # Without project scope, should include OP issue too
    result_all = runner.invoke(cli, ["--json", "search", "assignee:tom"])
    assert result_all.exit_code == 0
    data_all = json.loads(result_all.output)
    assert len(data_all) == 3


def test_search_no_results(initialized_project):
    """trak search "nonexistent_term" returns empty result."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "nonexistent_term"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_json_output(initialized_project):
    """trak --json search "status:open" returns valid JSON array with expected keys."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "status:open"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    expected_keys = {"id", "key", "project_id", "number", "type", "summary",
                     "description", "status", "priority", "assignee", "labels",
                     "created_at", "updated_at"}
    for issue in data:
        assert expected_keys <= set(issue.keys())


def test_search_label_filter(initialized_project):
    """trak search "label:backend" matches issues with that label."""
    runner = CliRunner()
    _setup_test_data(runner)

    result = runner.invoke(cli, ["--json", "search", "label:backend"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    for issue in data:
        assert "backend" in issue["labels"]
