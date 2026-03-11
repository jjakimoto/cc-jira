"""Search CLI command for trak."""

import click

from trak.core.formatting import output, render_table
from trak.core.search import build_sql, parse_query
from trak.db.connection import get_connection
from trak.models.issue import Issue


@click.command()
@click.argument("query")
@click.option("--project", default=None, help="Scope search to a project key.")
@click.pass_context
def search(ctx, query, project):
    """Search issues with a query string."""
    terms = parse_query(query)
    sql, params = build_sql(terms, project_key=project)
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()

    issues = []
    for r in rows:
        d = dict(r)
        pkey = d.pop("project_key")
        iss = Issue(**d)
        iss._set_project_key(pkey)
        issues.append(iss)

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
            title="Search Results",
        ),
    )
