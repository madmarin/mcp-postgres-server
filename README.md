# mcp-postgres

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants (Claude, etc.) direct, safe access to your PostgreSQL database.

[![CI](https://github.com/madmarin/mcp-postgres/actions/workflows/ci.yml/badge.svg)](https://github.com/madmarin/mcp-postgres/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-postgres)](https://pypi.org/project/mcp-postgres/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-postgres)](https://pypi.org/project/mcp-postgres/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

`mcp-postgres` exposes five tools to any MCP-compatible client:

| Tool | Description |
|------|-------------|
| `query` | Execute a read-only `SELECT` statement and get JSON results |
| `execute` | Run a write statement (`INSERT`, `UPDATE`, `DELETE`, DDL) — requires `ALLOW_WRITE=true` |
| `list_schemas` | List all user schemas in the database |
| `list_tables` | List tables/views in a schema with row estimates and sizes |
| `describe_table` | Get columns, primary key, foreign keys, and indexes for a table |

---

## Quickstart

### 1. Install

```bash
pip install mcp-postgres
```

Or install from source:

```bash
git clone https://github.com/madmarin/mcp-postgres
cd mcp-postgres
pip install -e .
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your connection details:

```bash
cp .env.example .env
```

Minimum required:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/mydb
```

### 3. Run

```bash
mcp-postgres
```

The server starts in `stdio` mode by default, ready to be used by any MCP client.

---

## Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "postgres": {
      "command": "mcp-postgres",
      "env": {
        "DATABASE_URL": "postgresql+psycopg://user:password@localhost:5432/mydb"
      }
    }
  }
}
```

Restart Claude Desktop — you will see the PostgreSQL tools available.

---

## Add to Claude Code (CLI)

```bash
claude mcp add postgres -- mcp-postgres
```

Then set the environment variable:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/mydb"
```

---

## Configuration Reference

All settings are read from environment variables or a `.env` file in the working directory.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Full connection string (`postgresql+psycopg://...`). Takes priority over individual fields. |
| `POSTGRES_HOST` | `localhost` | Host (used if `DATABASE_URL` is not set) |
| `POSTGRES_PORT` | `5432` | Port |
| `POSTGRES_DB` | `postgres` | Database name |
| `POSTGRES_USER` | `postgres` | Username |
| `POSTGRES_PASSWORD` | — | Password |
| `MCP_SERVER_NAME` | `mcp-postgres` | Name reported to MCP clients |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `sse` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ALLOW_WRITE` | `false` | Set to `true` to enable the `execute` tool |
| `POOL_MIN_SIZE` | `2` | Minimum connections in pool |
| `POOL_MAX_SIZE` | `10` | Maximum connections in pool |
| `QUERY_TIMEOUT` | `30.0` | Per-statement timeout in seconds |

---

## Tool Reference

### `query(sql, params?)`

Execute a read-only SELECT statement.

```
Input:
  sql     — SELECT statement or CTE
  params  — optional list of values for parameterized queries

Output (JSON):
  {
    "columns": ["id", "name", "age"],
    "rows": [[1, "Alice", 30], [2, "Bob", 25]],
    "row_count": 2,
    "execution_time_ms": 3.14
  }
```

**Always use `params` for user-supplied values** — never interpolate them into the SQL string.

```python
# Safe
query("SELECT * FROM users WHERE name = %s", ["Alice"])

# Never do this
query(f"SELECT * FROM users WHERE name = '{user_input}'")
```

---

### `execute(sql, params?)`

Run a write statement. Requires `ALLOW_WRITE=true`.

```
Output (JSON):
  {
    "rows_affected": 1,
    "status": "INSERT 0 1",
    "execution_time_ms": 2.5
  }
```

---

### `list_schemas()`

```
Output (JSON):
  [
    {"schema_name": "public", "owner": "postgres"},
    {"schema_name": "analytics", "owner": "alice"}
  ]
```

---

### `list_tables(schema?)`

```
Output (JSON):
  [
    {
      "table_name": "users",
      "table_type": "BASE TABLE",
      "row_estimate": 12345,
      "total_size": "2048 kB"
    }
  ]
```

---

### `describe_table(table, schema?)`

```
Output (JSON):
  {
    "table": "users",
    "schema": "public",
    "columns": [
      {"name": "id", "type": "integer", "nullable": false, "default": "nextval(...)"},
      {"name": "name", "type": "text", "nullable": false, "default": null}
    ],
    "primary_key": ["id"],
    "foreign_keys": [],
    "indexes": [
      {"name": "users_pkey", "definition": "CREATE UNIQUE INDEX ..."}
    ]
  }
```

---

## Security Model

- **Read-only by default**: the `execute` tool is disabled unless you explicitly set `ALLOW_WRITE=true`. This prevents accidental mutations.
- **Parameterized queries**: all tools use psycopg's parameterized query API. SQL is never built by string concatenation.
- **Denylist**: even with `ALLOW_WRITE=true`, certain destructive patterns (`DROP DATABASE`, `ALTER SYSTEM`, etc.) are blocked.
- **Error isolation**: internal error details (stack traces, SQL) are logged to stderr and never returned to the LLM.

---

## Development

```bash
git clone https://github.com/madmarin/mcp-postgres
cd mcp-postgres
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test]"
pre-commit install
```

Run the tests (requires Docker for testcontainers):

```bash
pytest
```

Lint and format:

```bash
ruff check src tests
ruff format src tests
mypy src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to add new tools or submit a PR.

---

## License

[MIT](LICENSE)
