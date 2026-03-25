# Contributing to mcp-postgres

Thank you for your interest in contributing! This document explains how to set up your environment, the project conventions, and how to submit a pull request.

---

## Development Setup

**Requirements:** Python 3.11+, Docker (for integration tests)

```bash
# 1. Fork and clone the repo
git clone https://github.com/your-username/mcp-postgres
cd mcp-postgres

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install with all dev dependencies
pip install -e ".[dev,test]"

# 4. Install pre-commit hooks
pre-commit install
```

---

## Running Tests

Tests use [testcontainers](https://testcontainers-python.readthedocs.io) to spin up a real PostgreSQL instance via Docker — no manual setup needed.

```bash
# Run all tests
pytest

# Run a specific file
pytest tests/test_query.py

# Run with verbose output
pytest -v

# Run without coverage (faster)
pytest --no-cov
```

---

## Lint & Type Check

```bash
ruff check src tests        # lint
ruff format src tests       # format
mypy src                    # type check
```

The pre-commit hooks run these automatically on every commit. To run them manually:

```bash
pre-commit run --all-files
```

---

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, released code |
| `develop` | Integration branch for upcoming release |
| `feat/your-feature` | Your feature or fix |

Always branch from `develop`:

```bash
git checkout develop
git pull
git checkout -b feat/my-new-tool
```

Open PRs targeting `develop`, not `main`.

---

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add resource for table browsing
fix: handle NULL values in JSON serialization
docs: add SSE transport example to README
test: add parameterized query injection test
chore: bump psycopg to 3.2.0
```

---

## Pull Request Checklist

Before opening a PR, make sure:

- [ ] All tests pass: `pytest`
- [ ] No lint errors: `ruff check src tests`
- [ ] Passes type check: `mypy src`
- [ ] New features have tests
- [ ] Public-facing changes are documented in `README.md`

---

## How to Add a New Tool

1. **Create the implementation** in `src/mcp_postgres/tools/your_tool.py`

   ```python
   async def your_tool(arg: str) -> str:
       """Docstring shown to the LLM — be precise."""
       ...
       return json.dumps(result)
   ```

2. **Register it** in `src/mcp_postgres/server.py`:

   ```python
   from mcp_postgres.tools.your_tool import your_tool as _your_tool

   @mcp.tool()
   async def your_tool(arg: str) -> str:
       """Same docstring — this is what the LLM sees."""
       try:
           return await _your_tool(arg)
       except exc.MCPPostgresError as e:
           return f"Error: {e.user_message}"
   ```

3. **Add tests** in `tests/test_your_tool.py`

4. **Document it** in the Tool Reference section of `README.md`

---

## Reporting Issues

Use [GitHub Issues](https://github.com/madmarin/mcp-postgres/issues). Please include:

- Python version
- PostgreSQL version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (set `LOG_LEVEL=DEBUG`)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
