"""MCP PostgreSQL Server — main entrypoint."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from loguru import logger
from mcp.server.fastmcp import FastMCP

from mcp_postgres import exceptions as exc
from mcp_postgres.config import settings
from mcp_postgres.db.pool import close_pool, init_pool
from mcp_postgres.tools.execute import execute as _execute
from mcp_postgres.tools.introspect import describe_table as _describe_table
from mcp_postgres.tools.query import query as _query
from mcp_postgres.tools.schema import list_schemas as _list_schemas
from mcp_postgres.tools.schema import list_tables as _list_tables


def _configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )


@asynccontextmanager
async def lifespan(_app: Any) -> AsyncIterator[None]:
    await init_pool(settings)
    try:
        yield
    finally:
        await close_pool()


mcp = FastMCP(settings.mcp_server_name, lifespan=lifespan)


# ── Tools ──────────────────────────────────────────────────────────────────────


@mcp.tool()
async def query(sql: str, params: list[Any] | None = None) -> str:
    """
    Execute a read-only SELECT query and return results as JSON.

    Args:
        sql: A SELECT statement or a CTE (WITH ... SELECT ...).
        params: Optional list of values for parameterized queries (e.g. ["Alice", 30]).

    Returns:
        JSON with keys: columns, rows, row_count, execution_time_ms.
    """
    try:
        return await _query(sql, params)
    except exc.MCPPostgresError as e:
        logger.error("query error: {}", e.detail or str(e))
        return f"Error: {e.user_message}"


@mcp.tool()
async def execute(sql: str, params: list[Any] | None = None) -> str:
    """
    Execute a write SQL statement (INSERT, UPDATE, DELETE, CREATE, DROP).

    Requires ALLOW_WRITE=true in the environment. Runs inside a transaction
    that rolls back automatically on error.

    Args:
        sql: A write SQL statement.
        params: Optional list of parameterized values.

    Returns:
        JSON with keys: rows_affected, status, execution_time_ms.
    """
    try:
        return await _execute(sql, params)
    except exc.MCPPostgresError as e:
        logger.error("execute error: {}", e.detail or str(e))
        return f"Error: {e.user_message}"


@mcp.tool()
async def list_schemas() -> str:
    """
    List all user-accessible schemas in the database (excludes pg_* and information_schema).

    Returns:
        JSON array of objects with keys: schema_name, owner.
    """
    try:
        return await _list_schemas()
    except exc.MCPPostgresError as e:
        logger.error("list_schemas error: {}", e.detail or str(e))
        return f"Error: {e.user_message}"


@mcp.tool()
async def list_tables(schema: str = "public") -> str:
    """
    List all tables and views in the given schema with row estimates and size.

    Args:
        schema: Schema name (default: public).

    Returns:
        JSON array of objects with keys: table_name, table_type, row_estimate, total_size.
    """
    try:
        return await _list_tables(schema)
    except exc.MCPPostgresError as e:
        logger.error("list_tables error: {}", e.detail or str(e))
        return f"Error: {e.user_message}"


@mcp.tool()
async def describe_table(table: str, schema: str = "public") -> str:
    """
    Return detailed schema information for a table.

    Args:
        table: The table name.
        schema: The schema that contains the table (default: public).

    Returns:
        JSON with keys: table, schema, columns, primary_key, foreign_keys, indexes.
    """
    try:
        return await _describe_table(table, schema)
    except exc.MCPPostgresError as e:
        logger.error("describe_table error: {}", e.detail or str(e))
        return f"Error: {e.user_message}"


# ── Entrypoint ─────────────────────────────────────────────────────────────────


def main() -> None:
    _configure_logging()
    logger.info("Starting {} (transport={})", settings.mcp_server_name, settings.mcp_transport)
    mcp.run(transport=settings.mcp_transport)


if __name__ == "__main__":
    main()
