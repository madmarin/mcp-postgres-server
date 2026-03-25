"""Tool: describe_table — full schema introspection for a single table."""

from __future__ import annotations

import json

from mcp_postgres.db.pool import acquire
from mcp_postgres import exceptions as exc


async def describe_table(table: str, schema: str = "public") -> str:
    """
    Return detailed schema information for a table: columns, primary key, foreign keys, and indexes.

    Args:
        table: The table name.
        schema: The schema that contains the table (default: public).

    Returns:
        JSON object with keys: table, schema, columns, primary_key, foreign_keys, indexes.
    """
    columns_sql = """
        SELECT
            column_name,
            ordinal_position,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """

    pk_sql = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name = tc.constraint_name
         AND kcu.table_schema    = tc.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = %s
          AND tc.table_name   = %s
        ORDER BY kcu.ordinal_position
    """

    fk_sql = """
        SELECT
            kcu.column_name,
            ccu.table_schema AS foreign_schema,
            ccu.table_name   AS foreign_table,
            ccu.column_name  AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name = tc.constraint_name
         AND kcu.table_schema    = tc.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = %s
          AND tc.table_name   = %s
    """

    idx_sql = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = %s AND tablename = %s
        ORDER BY indexname
    """

    try:
        async with acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(columns_sql, [schema, table])
                col_rows = await cur.fetchall()

                await cur.execute(pk_sql, [schema, table])
                pk_rows = await cur.fetchall()

                await cur.execute(fk_sql, [schema, table])
                fk_rows = await cur.fetchall()

                await cur.execute(idx_sql, [schema, table])
                idx_rows = await cur.fetchall()
    except exc.MCPPostgresError:
        raise
    except Exception as e:
        raise exc.QueryError(
            f"Failed to describe table '{schema}.{table}'.", detail=str(e)
        ) from e

    if not col_rows:
        raise exc.QueryError(
            f"Table '{schema}.{table}' does not exist or you do not have access to it."
        )

    result = {
        "table": table,
        "schema": schema,
        "columns": [
            {
                "name": r[0],
                "position": r[1],
                "type": r[2],
                "max_length": r[3],
                "nullable": r[4] == "YES",
                "default": r[5],
            }
            for r in col_rows
        ],
        "primary_key": [r[0] for r in pk_rows],
        "foreign_keys": [
            {
                "column": r[0],
                "references": f"{r[1]}.{r[2]}.{r[3]}",
            }
            for r in fk_rows
        ],
        "indexes": [{"name": r[0], "definition": r[1]} for r in idx_rows],
    }
    return json.dumps(result, indent=2)
