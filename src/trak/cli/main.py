"""CLI entry point for trak."""

import json
import sqlite3
from pathlib import Path

import click

from trak.cli.config_cmd import config
from trak.cli.issue import issue
from trak.cli.project import project
from trak.cli.search import search
from trak.cli.workflow import workflow
from trak.core.formatting import TrakSystemError
from trak.db.schema import init_db


class TrakGroup(click.Group):
    """Custom Click group that catches system errors."""

    def invoke(self, ctx: click.Context) -> None:
        try:
            return super().invoke(ctx)
        except click.exceptions.Exit:
            raise
        except click.ClickException:
            raise
        except (sqlite3.OperationalError, OSError) as e:
            raise TrakSystemError(str(e))


@click.group(cls=TrakGroup)
@click.option("--json", "use_json", is_flag=True, help="Output in JSON format.")
@click.pass_context
def cli(ctx: click.Context, use_json: bool) -> None:
    """trak — a local-first issue tracker."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json


cli.add_command(config)
cli.add_command(project)
cli.add_command(issue)
cli.add_command(search)
cli.add_command(workflow)


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
