"""Tests for the query tool."""

import json
import pytest

from mcp_postgres.tools.query import query
from mcp_postgres import exceptions as exc


@pytest.mark.asyncio
async def test_select_returns_rows(seed_tables):
    result = json.loads(await query("SELECT name, age FROM users ORDER BY name"))
    assert result["row_count"] == 3
    assert result["columns"] == ["name", "age"]
    assert result["rows"][0] == ["Alice", 30]


@pytest.mark.asyncio
async def test_parameterized_query(seed_tables):
    result = json.loads(await query("SELECT name FROM users WHERE age = %s", [30]))
    assert result["row_count"] == 1
    assert result["rows"][0][0] == "Alice"


@pytest.mark.asyncio
async def test_rejects_non_select():
    with pytest.raises(exc.QueryError, match="Only SELECT statements"):
        await query("DELETE FROM users")


@pytest.mark.asyncio
async def test_rejects_insert():
    with pytest.raises(exc.QueryError):
        await query("INSERT INTO users (name) VALUES ('X')")


@pytest.mark.asyncio
async def test_cte_is_allowed(seed_tables):
    sql = "WITH top AS (SELECT name FROM users LIMIT 2) SELECT * FROM top"
    result = json.loads(await query(sql))
    assert result["row_count"] == 2


@pytest.mark.asyncio
async def test_returns_execution_time(seed_tables):
    result = json.loads(await query("SELECT 1"))
    assert "execution_time_ms" in result
    assert result["execution_time_ms"] >= 0
