"""Tool: query — execute read-only SELECT statements."""

from __future__ import annotations

import json
import re
import time
from decimal import Decimal
from datetime import date, datetime, time as dt_time
from typing import Any
from uuid import UUID

from loguru import logger

from mcp_postgres.db.pool import acquire
from mcp_postgres import exceptions as exc

# Only allow statements that start with SELECT or a CTE (WITH ... SELECT)
_ALLOWED_PATTERN = re.compile(r"^\s*(WITH\b|SELECT\b)", re.IGNORECASE)


def _to_json_safe(value: Any) -> Any:
    """Convert Postgres types that are not JSON-serializable."""
    if isinstance(value, (datetime, date, dt_time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, memoryview):
        return bytes(value).hex()
    return value


async def query(sql: str, params: list[Any] | None = None) -> str:
    """
    Execute a read-only SQL SELECT statement and return results as JSON.

    Args:
        sql: A SELECT statement (or a CTE that resolves to SELECT).
        params: Optional list of parameterized query values (prevents SQL injection).

    Returns:
        JSON string with keys: columns, rows, row_count, execution_time_ms.
    """
    if not _ALLOWED_PATTERN.match(sql):
        raise exc.QueryError(
            "Only SELECT statements (or CTEs) are allowed in the query tool. "
            "Use the execute tool for write operations.",
            sql=sql,
        )

    logger.debug("Executing query: {}", sql[:200])
    start = time.perf_counter()

    try:
        async with acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params or [])
                rows_raw = await cur.fetchall()
                columns = [desc.name for desc in cur.description or []]
    except exc.MCPPostgresError:
        raise
    except Exception as e:
        raise exc.QueryError(
            f"Query failed: {e}",
            sql=sql,
            detail=str(e),
        ) from e

    elapsed_ms = (time.perf_counter() - start) * 1000
    rows = [[_to_json_safe(v) for v in row] for row in rows_raw]

    result = {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "execution_time_ms": round(elapsed_ms, 2),
    }
    logger.info("Query returned {} rows in {:.1f}ms", len(rows), elapsed_ms)
    return json.dumps(result, default=str)
