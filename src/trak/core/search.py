"""Search query parser and SQL builder for trak."""

from dataclasses import dataclass, field


_FIELD_ALIASES = {
    "created": "created_at",
    "updated": "updated_at",
    "label": "labels",
}


@dataclass
class SearchTerm:
    field: str | None
    operator: str
    values: list[str] = field(default_factory=list)


def parse_query(query_string: str) -> list[SearchTerm]:
    """Parse a search query string into structured search terms.

    Supports:
    - field:value pairs (e.g. status:open)
    - comma-separated OR values (e.g. priority:p0,p1)
    - date comparisons (e.g. created:>2024-01-01)
    - bare text for title+description search
    """
    if not query_string or not query_string.strip():
        return []

    tokens = query_string.strip().split()
    terms: list[SearchTerm] = []
    free_text_parts: list[str] = []

    for token in tokens:
        if ":" in token:
            field_name, value = token.split(":", 1)
            field_name = _FIELD_ALIASES.get(field_name, field_name)

            if value.startswith(">"):
                terms.append(SearchTerm(field=field_name, operator=">", values=[value[1:]]))
            elif value.startswith("<"):
                terms.append(SearchTerm(field=field_name, operator="<", values=[value[1:]]))
            elif "," in value:
                terms.append(SearchTerm(field=field_name, operator="=", values=value.split(",")))
            else:
                terms.append(SearchTerm(field=field_name, operator="=", values=[value]))
        else:
            free_text_parts.append(token)

    if free_text_parts:
        terms.append(SearchTerm(field=None, operator="LIKE", values=[" ".join(free_text_parts)]))

    return terms


def build_sql(
    terms: list[SearchTerm],
    project_key: str | None = None,
) -> tuple[str, list]:
    """Build a parameterized SQL query from parsed search terms.

    Returns (sql_string, params_list).
    """
    query = (
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
            # Free-text search across summary and description
            conditions.append("(i.summary LIKE ? OR i.description LIKE ?)")
            params.append(f"%{term.values[0]}%")
            params.append(f"%{term.values[0]}%")
        elif term.field == "labels":
            # Labels are stored as comma-separated text, use LIKE
            if len(term.values) > 1:
                or_parts = ["i.labels LIKE ?" for _ in term.values]
                conditions.append(f"({' OR '.join(or_parts)})")
                for v in term.values:
                    params.append(f"%{v}%")
            else:
                conditions.append("i.labels LIKE ?")
                params.append(f"%{term.values[0]}%")
        elif term.operator in (">", "<"):
            conditions.append(f"i.{term.field} {term.operator} ?")
            params.append(term.values[0])
        elif len(term.values) > 1:
            or_parts = [f"i.{term.field} = ?" for _ in term.values]
            conditions.append(f"({' OR '.join(or_parts)})")
            params.extend(term.values)
        else:
            conditions.append(f"i.{term.field} = ?")
            params.append(term.values[0])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY i.created_at DESC"
    return query, params
