"""Configuration via environment variables and .env files."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Connection ---
    database_url: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # --- Server ---
    mcp_server_name: str = "mcp-postgres"
    mcp_transport: Literal["stdio", "sse"] = "stdio"
    log_level: str = "INFO"

    # --- Pool ---
    pool_min_size: int = 2
    pool_max_size: int = 10
    query_timeout: float = 30.0

    # --- Safety ---
    allow_write: bool = False

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self

    @property
    def psycopg_conninfo(self) -> str:
        """Return a conninfo string compatible with psycopg (no SQLAlchemy prefix)."""
        url = self.database_url
        if url.startswith("postgresql+psycopg://"):
            url = url.replace("postgresql+psycopg://", "postgresql://", 1)
        return url


settings = Settings()
