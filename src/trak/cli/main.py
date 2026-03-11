"""CLI entry point for trak."""

import json
from pathlib import Path

import click

from trak.cli.issue import issue
from trak.cli.project import project
from trak.db.schema import init_db


@click.group()
@click.option("--json", "use_json", is_flag=True, help="Output in JSON format.")
@click.pass_context
def cli(ctx: click.Context, use_json: bool) -> None:
    """trak — a local-first issue tracker."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json


cli.add_command(project)
cli.add_command(issue)


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new trak project in the current directory."""
    trak_dir = Path.cwd() / ".trak"
    db_path = trak_dir / "trak.db"

    if db_path.exists():
        if ctx.obj["json"]:
            click.echo(json.dumps({"status": "already_initialized", "path": str(trak_dir)}))
        else:
            click.echo(f"Already initialized: {trak_dir}")
        return

    trak_dir.mkdir(exist_ok=True)
    init_db(db_path)

    if ctx.obj["json"]:
        click.echo(json.dumps({"status": "initialized", "path": str(trak_dir)}))
    else:
        click.echo(f"Initialized trak project in {trak_dir}")
