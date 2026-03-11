"""Config management CLI commands."""

import click

from trak.core.formatting import output, render_table
from trak.db.connection import get_connection
from trak.models.config import Config


@click.group()
def config():
    """Manage configuration settings."""


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    conn = get_connection()
    cfg = Config.set_value(conn, key, value)

    output(
        cfg.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: click.echo(f"Set '{d['key']}' = '{d['value']}'"),
    )


@config.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key):
    """Get a configuration value."""
    conn = get_connection()
    cfg = Config.get(conn, key)
    if cfg is None:
        raise click.ClickException(f"Config key '{key}' not found.")

    output(
        cfg.to_dict(),
        ctx.obj["json"],
        table_fn=lambda d: click.echo(d["value"]),
    )


@config.command("list")
@click.pass_context
def config_list(ctx):
    """List all configuration settings."""
    conn = get_connection()
    configs = Config.list_all(conn)
    data = [c.to_dict() for c in configs]

    output(
        data,
        ctx.obj["json"],
        table_fn=lambda d: render_table(
            columns=[("Key", "key"), ("Value", "value"), ("Updated", "updated_at")],
            rows=d,
            title="Configuration",
        ),
    )
