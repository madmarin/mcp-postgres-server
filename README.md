# mcp-postgres-server

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants (Claude, etc.) direct, safe access to your PostgreSQL database.

[![CI](https://github.com/madmarin/mcp-postgres-server/actions/workflows/ci.yml/badge.svg)](https://github.com/madmarin/mcp-postgres-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-postgres-server)](https://pypi.org/project/mcp-postgres-server/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-postgres-server)](https://pypi.org/project/mcp-postgres-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it does

`mcp-postgres-server` exposes five tools to any MCP-compatible client:

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
pip install mcp-postgres-server
```

Or install from source:

```bash
git clone https://github.com/madmarin/mcp-postgres-server
cd mcp-postgres-server
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

If your password contains special characters (for example `@`, `:`, `/`, `#`, `%`), URL-encode it in `DATABASE_URL`.

Example:

```env
# Raw password: p@ss:w0rd/with#chars%
DATABASE_URL=postgresql+psycopg://postgres:p%40ss%3Aw0rd%2Fwith%23chars%25@localhost:5432/mydb
```

You can encode safely with Python:

```bash
python3 -c "import urllib.parse; print(urllib.parse.quote('p@ss:w0rd/with#chars%', safe=''))"
```

### 3. Run

```bash
mcp-postgres-server
```

The server starts in `stdio` mode by default, ready to be used by any MCP client.

---

## Add to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "postgres": {
      "command": "mcp-postgres-server",
      "env": {
        "DATABASE_URL": "postgresql+psycopg://user:password@localhost:5432/mydb"
      }
    }
  }
}
```

> **macOS note:** Claude Desktop uses a restricted PATH and may not find the command by name. If you get a `Server disconnected` error, use the full path instead:
>
> ```bash
> which mcp-postgres-server
> # e.g. /Library/Frameworks/Python.framework/Versions/3.14/bin/mcp-postgres-server
> ```
>
> Then use that full path as the `"command"` value in the config above.

Restart Claude Desktop — you will see the PostgreSQL tools available.

---

## Add to Claude Code (CLI)

```bash
claude mcp add postgres -- mcp-postgres-server
```

Then set the environment variable:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/mydb"
```

---

## Use with Docker (no Python required)

If you have Docker installed, you can run the server without installing Python or any dependencies.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "postgres": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "DATABASE_URL",
        "-e",
        "ALLOW_WRITE",
        "-e",
        "QUERY_TIMEOUT",
        "madmarin/mcp-postgres-server"
      ],
      "env": {
        "DATABASE_URL": "postgresql+psycopg://user:password@localhost:5432/mydb",
        "ALLOW_WRITE": "false",
        "QUERY_TIMEOUT": "30.0"
      }
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add postgres -- docker run -i --rm \
  -e DATABASE_URL \
  -e ALLOW_WRITE \
  madmarin/mcp-postgres-server
```

Then set the environment variable:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/mydb"
```

> **Docker MCP Toolkit:** This server is also available in the [Docker MCP Toolkit](https://hub.docker.com/r/madmarin/mcp-postgres-server) catalog. You can add it directly from Docker Desktop without any manual configuration.

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
| `MCP_SERVER_NAME` | `mcp-postgres-server` | Name reported to MCP clients (logical MCP server name, not the CLI command) |
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
git clone https://github.com/madmarin/mcp-postgres-server
cd mcp-postgres-server
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
