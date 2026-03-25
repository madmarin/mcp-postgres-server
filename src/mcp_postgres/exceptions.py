"""Custom exception hierarchy for mcp-postgres."""


class MCPPostgresError(Exception):
    """Base exception. Always includes a safe user-facing message."""

    def __init__(self, user_message: str, *, detail: str = "") -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail  # logged internally, never sent to the model


class ConnectionError(MCPPostgresError):  # noqa: A001
    """Failed to acquire or open a database connection."""


class QueryError(MCPPostgresError):
    """SQL execution error."""

    def __init__(self, user_message: str, *, sql: str = "", detail: str = "") -> None:
        super().__init__(user_message, detail=detail)
        self.sql = sql


class PermissionError(MCPPostgresError):  # noqa: A001
    """Write operation attempted when ALLOW_WRITE=false."""


class TimeoutError(MCPPostgresError):  # noqa: A001
    """Query exceeded QUERY_TIMEOUT."""
