"""Unit tests for the search query parser and SQL builder."""

import pytest

from trak.core.search import SearchTerm, build_sql, parse_query


# ============================================================
# parse_query tests
# ============================================================


class TestParseQueryFieldValue:
    """Tests for field:value term parsing."""

    def test_single_field_value(self):
        terms = parse_query("status:open")
        assert len(terms) == 1
        assert terms[0].field == "status"
        assert terms[0].operator == "="
        assert terms[0].values == ["open"]

    def test_multiple_field_value_terms(self):
        terms = parse_query("status:open assignee:tom")
        assert len(terms) == 2
        assert terms[0].field == "status"
        assert terms[0].values == ["open"]
        assert terms[1].field == "assignee"
        assert terms[1].values == ["tom"]


class TestParseQueryCommaOR:
    """Tests for comma-separated OR values."""

    def test_comma_separated_values(self):
        terms = parse_query("status:todo,in_progress")
        assert len(terms) == 1
        assert terms[0].field == "status"
        assert terms[0].operator == "="
        assert terms[0].values == ["todo", "in_progress"]


class TestParseQueryFreeText:
    """Tests for bare text (free-text search)."""

    def test_bare_text(self):
        terms = parse_query("login bug")
        assert len(terms) == 1
        assert terms[0].field is None
        assert terms[0].operator == "LIKE"
        assert terms[0].values == ["login bug"]


class TestParseQueryDateComparison:
    """Tests for date comparison operators."""

    def test_date_greater_than(self):
        terms = parse_query("created:>2024-01-01")
        assert len(terms) == 1
        assert terms[0].field == "created_at"
        assert terms[0].operator == ">"
        assert terms[0].values == ["2024-01-01"]

    def test_date_less_than(self):
        terms = parse_query("updated:<2024-06-01")
        assert len(terms) == 1
        assert terms[0].field == "updated_at"
        assert terms[0].operator == "<"
        assert terms[0].values == ["2024-06-01"]


class TestParseQueryAliases:
    """Tests for field name aliases."""

    def test_created_alias(self):
        terms = parse_query("created:>2024-01-01")
        assert terms[0].field == "created_at"

    def test_updated_alias(self):
        terms = parse_query("updated:<2024-06-01")
        assert terms[0].field == "updated_at"

    def test_label_alias(self):
        terms = parse_query("label:backend")
        assert terms[0].field == "labels"


class TestParseQueryMixed:
    """Tests for mixed field terms and free text."""

    def test_mixed_field_and_free_text(self):
        terms = parse_query("status:open login bug")
        assert len(terms) == 2
        # Field term comes first
        assert terms[0].field == "status"
        assert terms[0].values == ["open"]
        # Free text is collected at the end
        assert terms[1].field is None
        assert terms[1].values == ["login bug"]


class TestParseQueryEmpty:
    """Tests for empty/blank queries."""

    def test_empty_string(self):
        assert parse_query("") == []

    def test_whitespace_only(self):
        assert parse_query("   ") == []


# ============================================================
# build_sql tests
# ============================================================


class TestBuildSqlEquality:
    """Tests for single equality term SQL generation."""

    def test_single_equality(self):
        terms = [SearchTerm(field="status", operator="=", values=["open"])]
        sql, params = build_sql(terms)
        assert "WHERE" in sql
        assert "i.status = ?" in sql
        assert params == ["open"]


class TestBuildSqlMultiValue:
    """Tests for multi-value OR SQL generation."""

    def test_multi_value_or(self):
        terms = [SearchTerm(field="status", operator="=", values=["todo", "in_progress"])]
        sql, params = build_sql(terms)
        assert "(i.status = ? OR i.status = ?)" in sql
        assert params == ["todo", "in_progress"]


class TestBuildSqlFreeText:
    """Tests for free-text LIKE SQL generation."""

    def test_free_text_like(self):
        terms = [SearchTerm(field=None, operator="LIKE", values=["login bug"])]
        sql, params = build_sql(terms)
        assert "(i.summary LIKE ? OR i.description LIKE ?)" in sql
        assert params == ["%login bug%", "%login bug%"]


class TestBuildSqlDateComparison:
    """Tests for date comparison SQL generation."""

    def test_date_greater_than(self):
        terms = [SearchTerm(field="created_at", operator=">", values=["2024-01-01"])]
        sql, params = build_sql(terms)
        assert "i.created_at > ?" in sql
        assert params == ["2024-01-01"]

    def test_date_less_than(self):
        terms = [SearchTerm(field="updated_at", operator="<", values=["2024-06-01"])]
        sql, params = build_sql(terms)
        assert "i.updated_at < ?" in sql
        assert params == ["2024-06-01"]


class TestBuildSqlProjectKey:
    """Tests for project_key filter."""

    def test_project_key_filter(self):
        terms = [SearchTerm(field="status", operator="=", values=["open"])]
        sql, params = build_sql(terms, project_key="MP")
        assert "p.key = ?" in sql
        assert "i.status = ?" in sql
        assert params == ["MP", "open"]


class TestBuildSqlLabel:
    """Tests for label LIKE matching."""

    def test_label_uses_like(self):
        terms = [SearchTerm(field="labels", operator="=", values=["backend"])]
        sql, params = build_sql(terms)
        assert "i.labels LIKE ?" in sql
        assert params == ["%backend%"]


class TestBuildSqlParamSafety:
    """Tests that all user values are parameterized, not interpolated."""

    def test_no_string_interpolation(self):
        terms = [
            SearchTerm(field="status", operator="=", values=["open"]),
            SearchTerm(field=None, operator="LIKE", values=["test"]),
            SearchTerm(field="created_at", operator=">", values=["2024-01-01"]),
        ]
        sql, params = build_sql(terms, project_key="MP")
        # No user values should appear literally in the SQL string
        assert "open" not in sql
        assert "test" not in sql
        assert "2024-01-01" not in sql
        assert "MP" not in sql
        # All values should be in the params list
        assert "MP" in params
        assert "open" in params
        assert "%test%" in params
        assert "2024-01-01" in params
