"""Search query parser and SQL builder for trak."""

from dataclasses import dataclass, field


# Field name aliases: user-friendly names → actual DB column names
_FIELD_ALIASES: dict[str, str] = {
    "created": "created_at",
    "updated": "updated_at",
    "label": "labels",
}


@dataclass
class SearchTerm:
    """A single parsed search term."""

    field: str | None  # None for free-text search
    operator: str  # "=", ">", "<", "LIKE"
    values: list[str] = field(default_factory=list)


def parse_query(query_string: str) -> list[SearchTerm]:
    """Parse a query string into a list of SearchTerm objects.

    Supports:
    - field:value pairs (status:open, assignee:tom)
    - Comma-separated OR values (status:todo,in_progress)
    - Date comparisons with > or < prefix (created:>2024-01-01)
    - Bare text for free-text search (login bug)
    - Field name aliases (created → created_at, label → labels)
    """
    if not query_string or not query_string.strip():
        return []

    tokens = query_string.strip().split()
    terms: list[SearchTerm] = []
    free_text_parts: list[str] = []

    for token in tokens:
        if ":" in token:
            field_name, _, value = token.partition(":")
            # Resolve aliases
            field_name = _FIELD_ALIASES.get(field_name, field_name)

            # Check for date comparison operators
            if value.startswith(">"):
                terms.append(SearchTerm(
                    field=field_name,
                    operator=">",
                    values=[value[1:]],
                ))
            elif value.startswith("<"):
                terms.append(SearchTerm(
                    field=field_name,
                    operator="<",
                    values=[value[1:]],
                ))
            else:
                # Comma-separated OR values
                values = value.split(",")
                terms.append(SearchTerm(
                    field=field_name,
                    operator="=",
                    values=values,
                ))
        else:
            free_text_parts.append(token)

    if free_text_parts:
        terms.append(SearchTerm(
            field=None,
            operator="LIKE",
            values=[" ".join(free_text_parts)],
        ))

    return terms


def build_sql(
    terms: list[SearchTerm],
    project_key: str | None = None,
) -> tuple[str, list]:
    """Build a parameterized SQL SELECT from search terms.

    Returns:
        Tuple of (sql_string, params_list).
    """
    base = (
        "SELECT i.id, i.project_id, i.number, i.type, i.summary, i.description, "
        "i.status, i.priority, i.assignee, i.labels, i.created_at, i.updated_at, "
        "p.key AS project_key "
        "FROM issues i JOIN projects p ON i.project_id = p.id"
    )

    conditions: list[str] = []
    params: list = []

    if project_key is not None:
        conditions.append("p.key = ?")
        params.append(project_key)

    for term in terms:
        if term.field is None:
            # Free-text search: match against summary and description
            conditions.append("(i.summary LIKE ? OR i.description LIKE ?)")
            params.append(f"%{term.values[0]}%")
            params.append(f"%{term.values[0]}%")
        elif term.operator in (">", "<"):
            conditions.append(f"i.{term.field} {term.operator} ?")
            params.append(term.values[0])
        elif term.field == "labels":
            # Labels are comma-separated text; use LIKE for matching
            if len(term.values) == 1:
                conditions.append("i.labels LIKE ?")
                params.append(f"%{term.values[0]}%")
            else:
                or_parts = ["i.labels LIKE ?" for _ in term.values]
                conditions.append(f"({' OR '.join(or_parts)})")
                params.extend(f"%{v}%" for v in term.values)
        else:
            # Standard equality (with multi-value OR support)
            if len(term.values) == 1:
                conditions.append(f"i.{term.field} = ?")
                params.append(term.values[0])
            else:
                or_parts = [f"i.{term.field} = ?" for _ in term.values]
                conditions.append(f"({' OR '.join(or_parts)})")
                params.extend(term.values)

    if conditions:
        base += " WHERE " + " AND ".join(conditions)

    base += " ORDER BY i.created_at DESC"

    return base, params
