"""Project management CLI commands."""

import click

from trak.core.formatting import output, render_table
from trak.db.connection import get_connection
from trak.models.project import Project


@click.group()
def project():
    """Manage projects."""


@project.command("create")
@click.argument("name")
@click.option("--key", required=True, help="Unique project key (2-10 uppercase letters).")
@click.option("--description", default=None, help="Project description.")
@click.pass_context
def project_create(ctx, name, key, description):
    """Create a new project."""
    conn = get_connection()
    try:
        proj = Project.create(conn, key=key, name=name, description=description)
    except ValueError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise click.ClickException(f"Project key '{key}' already exists.")
        raise

    output(
        proj.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_project_detail(d),
    )


@project.command("list")
@click.pass_context
def project_list(ctx):
    """List all projects."""
    conn = get_connection()
    projects = Project.list_all(conn)
    data = [p.to_dict() for p in projects]

    output(
        data,
        ctx.obj["json"],
        table_fn=lambda d: render_table(
            columns=[("Key", "key"), ("Name", "name"), ("Created", "created_at")],
            rows=d,
            title="Projects",
        ),
    )


@project.command("show")
@click.argument("key")
@click.pass_context
def project_show(ctx, key):
    """Show project details."""
    conn = get_connection()
    proj = Project.get_by_key(conn, key)
    if proj is None:
        raise click.ClickException(f"Project '{key}' not found.")

    output(
        proj.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_project_detail(d),
    )


@project.command("delete")
@click.argument("key")
@click.option("--force", is_flag=True, help="Confirm deletion.")
@click.pass_context
def project_delete(ctx, key, force):
    """Delete a project."""
    if not force:
        raise click.ClickException(
            f"Use --force to confirm deletion of project '{key}'."
        )

    conn = get_connection()
    try:
        Project.delete(conn, key)
    except KeyError as e:
        raise click.ClickException(str(e))

    output(
        {"status": "deleted", "key": key},
        ctx.obj["json"],
        table_fn=lambda d: click.echo(f"Deleted project '{key}'."),
    )


def _print_project_detail(data: dict) -> None:
    """Print a single project as a Rich table."""
    render_table(
        columns=[
            ("Key", "key"),
            ("Name", "name"),
            ("Description", "description"),
            ("Created", "created_at"),
            ("Updated", "updated_at"),
        ],
        rows=[data],
    )
