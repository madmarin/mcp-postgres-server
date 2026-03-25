"""Tests for list_schemas, list_tables, and describe_table."""

import json
import pytest

from mcp_postgres.tools.schema import list_schemas, list_tables
from mcp_postgres.tools.introspect import describe_table
from mcp_postgres import exceptions as exc


@pytest.mark.asyncio
async def test_list_schemas_contains_public():
    schemas = json.loads(await list_schemas())
    names = [s["schema_name"] for s in schemas]
    assert "public" in names


@pytest.mark.asyncio
async def test_list_tables_returns_users(seed_tables):
    tables = json.loads(await list_tables("public"))
    names = [t["table_name"] for t in tables]
    assert "users" in names


@pytest.mark.asyncio
async def test_describe_table_columns(seed_tables):
    info = json.loads(await describe_table("users", "public"))
    col_names = [c["name"] for c in info["columns"]]
    assert "id" in col_names
    assert "name" in col_names
    assert "age" in col_names


@pytest.mark.asyncio
async def test_describe_table_primary_key(seed_tables):
    info = json.loads(await describe_table("users", "public"))
    assert "id" in info["primary_key"]


@pytest.mark.asyncio
async def test_describe_nonexistent_table():
    with pytest.raises(exc.QueryError, match="does not exist"):
        await describe_table("no_such_table", "public")
