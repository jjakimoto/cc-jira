"""Workflow management CLI commands."""

import json as json_lib

import click

from trak.core.formatting import output, render_table
from trak.db.connection import get_connection
from trak.models.workflow import Workflow


@click.group()
def workflow():
    """Manage workflows."""


@workflow.command("list")
@click.pass_context
def workflow_list(ctx):
    """List all workflows."""
    conn = get_connection()
    workflows = Workflow.list_all(conn)
    data = [w.to_dict() for w in workflows]

    output(
        data,
        ctx.obj["json"],
        table_fn=lambda d: render_table(
            columns=[
                ("Name", "name"),
                ("Statuses", "statuses"),
            ],
            rows=[{"name": w["name"], "statuses": ", ".join(w["statuses"])} for w in d],
            title="Workflows",
        ),
    )


@workflow.command("show")
@click.argument("name")
@click.pass_context
def workflow_show(ctx, name):
    """Show workflow details."""
    conn = get_connection()
    wf = Workflow.get_by_name(conn, name)
    if wf is None:
        raise click.ClickException(f"Workflow '{name}' not found.")

    output(
        wf.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_workflow_detail(d),
    )


@workflow.command("create")
@click.argument("name")
@click.option("--statuses", required=True, help="Comma-separated list of statuses.")
@click.option("--transitions", required=True, help="JSON string of transitions map.")
@click.pass_context
def workflow_create(ctx, name, statuses, transitions):
    """Create a custom workflow."""
    status_list = [s.strip() for s in statuses.split(",")]

    try:
        transitions_dict = json_lib.loads(transitions)
    except json_lib.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON for transitions: {e}")

    conn = get_connection()
    try:
        wf = Workflow.create(conn, name=name, statuses=status_list, transitions=transitions_dict)
    except ValueError as e:
        raise click.ClickException(str(e))

    output(
        wf.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: _print_workflow_detail(d),
    )


def _print_workflow_detail(data: dict) -> None:
    """Print workflow statuses and transitions."""
    click.echo(f"Workflow: {data['name']}")
    click.echo()
    render_table(
        columns=[("Position", "position"), ("Status", "status")],
        rows=[{"position": str(i), "status": s} for i, s in enumerate(data["statuses"])],
        title="Statuses",
    )
    click.echo()
    transitions = data.get("transitions", {})
    trans_rows = []
    for from_s, to_list in sorted(transitions.items()):
        for to_s in to_list:
            trans_rows.append({"from": from_s, "to": to_s})
    render_table(
        columns=[("From", "from"), ("To", "to")],
        rows=trans_rows,
        title="Transitions",
    )
