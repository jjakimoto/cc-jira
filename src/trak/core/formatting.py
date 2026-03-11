"""Shared output formatting for trak CLI."""

import json
from typing import Any, Callable

import click
from rich.console import Console
from rich.table import Table


_console = Console()


def render_table(
    columns: list[tuple[str, str]],
    rows: list[dict],
    title: str | None = None,
) -> None:
    """Render rows as a Rich table.

    Args:
        columns: List of (header, key) tuples.
        rows: List of dicts (or sqlite3.Row objects).
        title: Optional table title.
    """
    table = Table(title=title)
    for header, _key in columns:
        table.add_column(header)
    for row in rows:
        table.add_row(*(str(row.get(key, "")) if isinstance(row, dict) else str(row[key]) for _header, key in columns))
    _console.print(table)


def output(
    data: Any,
    json_mode: bool,
    table_fn: Callable[[Any], None] | None = None,
) -> None:
    """Dispatch output to JSON or Rich table rendering."""
    if json_mode:
        click.echo(json.dumps(data, indent=2, default=str))
    elif table_fn is not None:
        table_fn(data)


class TrakSystemError(click.ClickException):
    """System-level error (exit code 2)."""

    exit_code = 2

    def format_message(self) -> str:
        return f"System error: {self.message}"
