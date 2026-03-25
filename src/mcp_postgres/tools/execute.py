"""Tool: execute — run write operations (INSERT, UPDATE, DELETE, DDL)."""

from __future__ import annotations

import json
import re
import time
from typing import Any

from loguru import logger

from mcp_postgres.config import settings
from mcp_postgres.db.pool import acquire
from mcp_postgres import exceptions as exc

# Block the most dangerous DDL regardless of ALLOW_WRITE
_DENYLIST = re.compile(
    r"\b(DROP\s+DATABASE|TRUNCATE\s+pg_|DROP\s+SCHEMA\s+pg_catalog|ALTER\s+SYSTEM)\b",
    re.IGNORECASE,
)


async def execute(sql: str, params: list[Any] | None = None) -> str:
    """
    Execute a write SQL statement (INSERT, UPDATE, DELETE, CREATE, DROP, etc.).

    Requires the ALLOW_WRITE environment variable to be set to 'true'.
    Runs inside a transaction that is automatically rolled back on error.

    Args:
        sql: A SQL write statement.
        params: Optional list of parameterized query values.

    Returns:
        JSON string with keys: rows_affected, status, execution_time_ms.
    """
    if not settings.allow_write:
        raise exc.PermissionError(
            "Write operations are disabled. Set ALLOW_WRITE=true in your environment to enable them."
        )

    if _DENYLIST.search(sql):
        raise exc.PermissionError(
            "This statement is blocked for safety reasons. "
            "Statements affecting system catalogs or dropping databases are not allowed."
        )

    logger.warning("Executing write statement: {}", sql[:200])
    start = time.perf_counter()

    try:
        async with acquire() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute(sql, params or [])
                    rows_affected = cur.rowcount
                    status = cur.statusmessage or "OK"
    except exc.MCPPostgresError:
        raise
    except Exception as e:
        raise exc.QueryError(
            f"Execute failed: {e}",
            sql=sql,
            detail=str(e),
        ) from e

    elapsed_ms = (time.perf_counter() - start) * 1000
    result = {
        "rows_affected": rows_affected,
        "status": status,
        "execution_time_ms": round(elapsed_ms, 2),
    }
    logger.info("Execute completed: {} ({:.1f}ms)", status, elapsed_ms)
    return json.dumps(result)
