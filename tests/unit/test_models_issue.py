"""Unit tests for the Issue and Comment models."""

import sqlite3
import time

import pytest

from trak.db.schema import create_tables, seed_default_transitions, seed_default_workflow
from trak.models.comment import Comment
from trak.models.issue import Issue
from trak.models.project import Project


@pytest.fixture
def db_conn():
    """In-memory SQLite database with trak schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    create_tables(conn)
    seed_default_workflow(conn)
    seed_default_transitions(conn)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def project_mp(db_conn):
    """Create a project with key MP for issue tests."""
    return Project.create(db_conn, key="MP", name="My Project")


@pytest.fixture
def project_other(db_conn):
    """Create a second project with key OTHER."""
    return Project.create(db_conn, key="OTHER", name="Other Project")


# --- Issue.create ---


def test_create_returns_correct_fields(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Fix bug")
    assert issue.id is not None
    assert issue.project_id == project_mp.id
    assert issue.number == 1
    assert issue.summary == "Fix bug"
    assert issue.type == "task"
    assert issue.status == "todo"
    assert issue.priority == "p2"
    assert issue.description is None
    assert issue.assignee is None
    assert issue.labels is None
    assert issue.created_at is not None
    assert issue.updated_at is not None


def test_create_with_all_fields(db_conn, project_mp):
    issue = Issue.create(
        db_conn,
        project_id=project_mp.id,
        summary="Important bug",
        type="bug",
        description="Detailed description",
        priority="p1",
        assignee="tom",
        labels="backend,urgent",
    )
    assert issue.type == "bug"
    assert issue.description == "Detailed description"
    assert issue.priority == "p1"
    assert issue.assignee == "tom"
    assert issue.labels == "backend,urgent"


# --- Auto-numbering ---


def test_auto_increment_per_project(db_conn, project_mp, project_other):
    i1 = Issue.create(db_conn, project_id=project_mp.id, summary="First MP")
    i2 = Issue.create(db_conn, project_id=project_mp.id, summary="Second MP")
    i3 = Issue.create(db_conn, project_id=project_other.id, summary="First OTHER")

    assert i1.number == 1
    assert i2.number == 2
    # Different project resets numbering
    assert i3.number == 1


def test_key_generation(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Test key")
    # After create, _project_key is not set, so we retrieve via get_by_key
    fetched = Issue.get_by_key(db_conn, "MP-1")
    assert fetched is not None
    assert fetched.key == "MP-1"


# --- Issue.get_by_key ---


def test_get_by_key_parses_and_retrieves(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="Find me")
    issue = Issue.get_by_key(db_conn, "MP-1")
    assert issue is not None
    assert issue.summary == "Find me"
    assert issue.key == "MP-1"
    assert issue.project_id == project_mp.id
    assert issue.number == 1


def test_get_by_key_returns_none_for_nonexistent(db_conn, project_mp):
    assert Issue.get_by_key(db_conn, "MP-999") is None


def test_get_by_key_returns_none_for_bad_format(db_conn):
    assert Issue.get_by_key(db_conn, "NOPE") is None
    assert Issue.get_by_key(db_conn, "MP-abc") is None


# --- Issue.list_all ---


def test_list_all_returns_all_issues(db_conn, project_mp, project_other):
    Issue.create(db_conn, project_id=project_mp.id, summary="A")
    Issue.create(db_conn, project_id=project_mp.id, summary="B")
    Issue.create(db_conn, project_id=project_other.id, summary="C")

    issues = Issue.list_all(db_conn)
    assert len(issues) == 3


def test_list_all_filter_by_project(db_conn, project_mp, project_other):
    Issue.create(db_conn, project_id=project_mp.id, summary="MP issue")
    Issue.create(db_conn, project_id=project_other.id, summary="OTHER issue")

    issues = Issue.list_all(db_conn, project_key="MP")
    assert len(issues) == 1
    assert issues[0].key == "MP-1"


def test_list_all_filter_by_status(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="Open issue")
    Issue.update(db_conn, "MP-1", status="in_progress")

    issues = Issue.list_all(db_conn, status="in_progress")
    assert len(issues) == 1
    assert issues[0].key == "MP-1"


def test_list_all_filter_by_priority(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="P1", priority="p1")
    Issue.create(db_conn, project_id=project_mp.id, summary="P2", priority="p2")

    issues = Issue.list_all(db_conn, priority="p1")
    assert len(issues) == 1
    assert issues[0].summary == "P1"


def test_list_all_filter_by_assignee(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="Tom's", assignee="tom")
    Issue.create(db_conn, project_id=project_mp.id, summary="Unassigned")

    issues = Issue.list_all(db_conn, assignee="tom")
    assert len(issues) == 1
    assert issues[0].summary == "Tom's"


# --- Issue.update ---


def test_update_modifies_fields(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="Original")
    updated = Issue.update(db_conn, "MP-1", status="in_progress", assignee="tom")

    assert updated.status == "in_progress"
    assert updated.assignee == "tom"


def test_update_bumps_updated_at(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Watch time")
    original_updated = issue.updated_at

    # Small delay to ensure timestamp differs
    time.sleep(0.01)
    updated = Issue.update(db_conn, "MP-1", summary="New summary")

    assert updated.updated_at > original_updated
    assert updated.summary == "New summary"


def test_update_raises_for_nonexistent(db_conn):
    with pytest.raises(KeyError):
        Issue.update(db_conn, "NOPE-1", status="closed")


# --- Issue.delete ---


def test_delete_removes_issue(db_conn, project_mp):
    Issue.create(db_conn, project_id=project_mp.id, summary="Delete me")
    Issue.delete(db_conn, "MP-1")
    assert Issue.get_by_key(db_conn, "MP-1") is None


def test_delete_raises_for_nonexistent(db_conn):
    with pytest.raises(KeyError):
        Issue.delete(db_conn, "NOPE-1")


def test_delete_cascades_to_comments(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="With comments")
    Comment.add(db_conn, issue_id=issue.id, body="A comment", author="tester")
    Comment.add(db_conn, issue_id=issue.id, body="Another comment", author="tester")

    # Verify comments exist
    assert len(Comment.list_for_issue(db_conn, issue.id)) == 2

    Issue.delete(db_conn, "MP-1")

    # Comments should be cascade-deleted
    assert len(Comment.list_for_issue(db_conn, issue.id)) == 0


# --- Comment.add ---


def test_comment_add(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Commentable")
    comment = Comment.add(db_conn, issue_id=issue.id, body="Fixed in commit abc", author="tom")

    assert comment.id is not None
    assert comment.issue_id == issue.id
    assert comment.author == "tom"
    assert comment.body == "Fixed in commit abc"
    assert comment.created_at is not None


def test_comment_add_default_author(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Auto author")
    comment = Comment.add(db_conn, issue_id=issue.id, body="No explicit author")

    # Default author is the OS user
    assert comment.author is not None
    assert len(comment.author) > 0


# --- Comment.list_for_issue ---


def test_comment_list_for_issue(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="Multi-comment")
    Comment.add(db_conn, issue_id=issue.id, body="First", author="alice")
    Comment.add(db_conn, issue_id=issue.id, body="Second", author="bob")

    comments = Comment.list_for_issue(db_conn, issue.id)
    assert len(comments) == 2
    assert comments[0].body == "First"
    assert comments[1].body == "Second"


def test_comment_list_for_issue_empty(db_conn, project_mp):
    issue = Issue.create(db_conn, project_id=project_mp.id, summary="No comments")
    comments = Comment.list_for_issue(db_conn, issue.id)
    assert comments == []
