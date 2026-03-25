"""Tools: list_schemas and list_tables."""

from __future__ import annotations

import json

from mcp_postgres import exceptions as exc
from mcp_postgres.db.pool import acquire


async def list_schemas() -> str:
    """
    List all user-accessible schemas in the database (excludes pg_* and information_schema).

    Returns:
        JSON array of objects with keys: schema_name, owner.
    """
    sql = """
        SELECT
            schema_name,
            schema_owner AS owner
        FROM information_schema.schemata
        WHERE schema_name NOT LIKE 'pg_%'
          AND schema_name != 'information_schema'
        ORDER BY schema_name
    """
    try:
        async with acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql)
                rows = await cur.fetchall()
    except exc.MCPPostgresError:
        raise
    except Exception as e:
        raise exc.QueryError("Failed to list schemas.", detail=str(e)) from e

    schemas = [{"schema_name": row[0], "owner": row[1]} for row in rows]
    return json.dumps(schemas)


async def list_tables(schema: str = "public") -> str:
    """
    List all tables and views in the given schema with row estimates and size.

    Args:
        schema: The schema name to inspect (default: public).

    Returns:
        JSON array of objects with keys: table_name, table_type, row_estimate, total_size.
    """
    sql = """
        SELECT
            t.table_name,
            t.table_type,
            COALESCE(s.n_live_tup, -1)           AS row_estimate,
            pg_size_pretty(
                pg_total_relation_size(
                    (t.table_schema || '.' || t.table_name)::regclass
                )
            )                                     AS total_size
        FROM information_schema.tables t
        LEFT JOIN pg_stat_user_tables s
               ON s.schemaname = t.table_schema
              AND s.relname     = t.table_name
        WHERE t.table_schema = %s
        ORDER BY t.table_name
    """
    try:
        async with acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, [schema])
                rows = await cur.fetchall()
    except exc.MCPPostgresError:
        raise
    except Exception as e:
        raise exc.QueryError(f"Failed to list tables in schema '{schema}'.", detail=str(e)) from e

    tables = [
        {
            "table_name": row[0],
            "table_type": row[1],
            "row_estimate": row[2],
            "total_size": row[3],
        }
        for row in rows
    ]
    return json.dumps(tables)
