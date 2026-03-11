"""Issue management CLI commands."""

import click

from trak.core.formatting import output, render_table
from trak.db.connection import get_connection
from trak.models.comment import Comment
from trak.models.issue import Issue
from trak.models.project import Project


@click.group()
def issue():
    """Manage issues."""


@issue.command("create")
@click.argument("summary")
@click.option("--project", required=True, help="Project key (e.g. MP).")
@click.option("--type", "issue_type", default="task", help="Issue type (task, bug, story, epic).")
@click.option("--priority", default="p2", help="Priority (p0, p1, p2, p3).")
@click.option("--description", default=None, help="Issue description.")
@click.option("--assignee", default=None, help="Assignee username.")
@click.option("--labels", default=None, help="Comma-separated labels.")
@click.pass_context
def issue_create(ctx, summary, project, issue_type, priority, description, assignee, labels):
    """Create a new issue."""
    conn = get_connection()
    proj = Project.get_by_key(conn, project)
    if proj is None:
        raise click.ClickException(f"Project '{project}' not found.")

    iss = Issue.create(
        conn,
        project_id=proj.id,
        summary=summary,
        type=issue_type,
        description=description,
        priority=priority,
        assignee=assignee,
        labels=labels,
    )
    iss._set_project_key(proj.key)

    output(
        iss.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_issue_detail(d),
    )


@issue.command("list")
@click.option("--project", default=None, help="Filter by project key.")
@click.option("--status", default=None, help="Filter by status.")
@click.option("--assignee", default=None, help="Filter by assignee.")
@click.option("--label", default=None, help="Filter by label.")
@click.option("--priority", default=None, help="Filter by priority.")
@click.pass_context
def issue_list(ctx, project, status, assignee, label, priority):
    """List issues."""
    conn = get_connection()
    issues = Issue.list_all(
        conn,
        project_key=project,
        status=status,
        assignee=assignee,
        label=label,
        priority=priority,
    )
    data = [i.to_dict() for i in issues]

    output(
        data,
        ctx.obj["json"],
        table_fn=lambda d: render_table(
            columns=[
                ("Key", "key"),
                ("Type", "type"),
                ("Summary", "summary"),
                ("Status", "status"),
                ("Priority", "priority"),
                ("Assignee", "assignee"),
            ],
            rows=d,
            title="Issues",
        ),
    )


@issue.command("show")
@click.argument("key")
@click.pass_context
def issue_show(ctx, key):
    """Show issue details."""
    conn = get_connection()
    iss = Issue.get_by_key(conn, key)
    if iss is None:
        raise click.ClickException(f"Issue '{key}' not found.")

    comments = Comment.list_for_issue(conn, iss.id)
    data = iss.to_dict()
    data["comments"] = [c.to_dict() for c in comments]

    output(
        data,
        ctx.obj["json"],
        table_fn=lambda d: _print_issue_detail_with_comments(d),
    )


@issue.command("update")
@click.argument("key")
@click.option("--status", default=None, help="New status.")
@click.option("--assignee", default=None, help="New assignee.")
@click.option("--priority", default=None, help="New priority.")
@click.option("--summary", default=None, help="New summary.")
@click.option("--type", "issue_type", default=None, help="New type.")
@click.option("--labels", default=None, help="New labels.")
@click.pass_context
def issue_update(ctx, key, status, assignee, priority, summary, issue_type, labels):
    """Update an issue."""
    conn = get_connection()
    try:
        iss = Issue.update(
            conn, key,
            status=status,
            assignee=assignee,
            priority=priority,
            summary=summary,
            type=issue_type,
            labels=labels,
        )
    except KeyError as e:
        raise click.ClickException(str(e))

    output(
        iss.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_issue_detail(d),
    )


@issue.command("delete")
@click.argument("key")
@click.option("--force", is_flag=True, help="Confirm deletion.")
@click.pass_context
def issue_delete(ctx, key, force):
    """Delete an issue."""
    if not force:
        raise click.ClickException(
            f"Use --force to confirm deletion of issue '{key}'."
        )

    conn = get_connection()
    try:
        Issue.delete(conn, key)
    except KeyError as e:
        raise click.ClickException(str(e))

    output(
        {"status": "deleted", "key": key},
        ctx.obj["json"],
        table_fn=lambda d: click.echo(f"Deleted issue '{key}'."),
    )


@issue.command("comment")
@click.argument("key")
@click.argument("body")
@click.pass_context
def issue_comment(ctx, key, body):
    """Add a comment to an issue."""
    conn = get_connection()
    iss = Issue.get_by_key(conn, key)
    if iss is None:
        raise click.ClickException(f"Issue '{key}' not found.")

    comment = Comment.add(conn, issue_id=iss.id, body=body)

    output(
        comment.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: click.echo(
            f"Comment added to {key} by {d['author']}."
        ),
    )


def _print_issue_detail(data: dict) -> None:
    render_table(
        columns=[
            ("Key", "key"),
            ("Type", "type"),
            ("Summary", "summary"),
            ("Status", "status"),
            ("Priority", "priority"),
            ("Assignee", "assignee"),
            ("Labels", "labels"),
            ("Created", "created_at"),
            ("Updated", "updated_at"),
        ],
        rows=[data],
    )


def _print_issue_detail_with_comments(data: dict) -> None:
    _print_issue_detail(data)
    comments = data.get("comments", [])
    if comments:
        click.echo()
        render_table(
            columns=[
                ("Author", "author"),
                ("Comment", "body"),
                ("Date", "created_at"),
            ],
            rows=comments,
            title="Comments",
        )
