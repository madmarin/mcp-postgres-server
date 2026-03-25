"""Tests for the execute tool."""

import json
import pytest

from unittest.mock import patch
from mcp_postgres.tools.execute import execute
from mcp_postgres import exceptions as exc


@pytest.mark.asyncio
async def test_execute_blocked_by_default():
    with patch("mcp_postgres.tools.execute.settings") as mock_settings:
        mock_settings.allow_write = False
        with pytest.raises(exc.PermissionError, match="ALLOW_WRITE"):
            await execute("INSERT INTO users (name) VALUES ('X')")


@pytest.mark.asyncio
async def test_insert_and_delete(seed_tables):
    result = json.loads(
        await execute("INSERT INTO users (name, age) VALUES (%s, %s)", ["Dave", 40])
    )
    assert result["rows_affected"] == 1

    result = json.loads(await execute("DELETE FROM users WHERE name = %s", ["Dave"]))
    assert result["rows_affected"] == 1


@pytest.mark.asyncio
async def test_denylist_blocks_drop_database():
    with pytest.raises(exc.PermissionError, match="blocked for safety"):
        await execute("DROP DATABASE postgres")


@pytest.mark.asyncio
async def test_rollback_on_error(seed_tables):
    from mcp_postgres.tools.query import query

    before = json.loads(await query("SELECT COUNT(*) FROM users"))["rows"][0][0]

    with pytest.raises(exc.QueryError):
        await execute("INSERT INTO nonexistent_table (x) VALUES (1)")

    after = json.loads(await query("SELECT COUNT(*) FROM users"))["rows"][0][0]
    assert before == after
