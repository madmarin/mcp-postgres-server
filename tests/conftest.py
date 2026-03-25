"""Pytest fixtures — spins up a real Postgres via testcontainers."""

from __future__ import annotations

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from mcp_postgres.config import Settings
from mcp_postgres.db import pool as pool_mod


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def test_settings(postgres_container) -> Settings:
    return Settings(
        database_url=postgres_container.get_connection_url().replace(
            "postgresql+psycopg2://", "postgresql+psycopg://"
        ),
        allow_write=True,
        log_level="DEBUG",
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_pool(test_settings):
    await pool_mod.init_pool(test_settings)
    yield
    await pool_mod.close_pool()


@pytest_asyncio.fixture()
async def seed_tables():
    """Create and seed sample tables for query tests."""
    from mcp_postgres.db.pool import acquire

    async with acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id   SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                age  INT
            )
        """)
        await conn.execute("DELETE FROM users")
        await conn.execute("""
            INSERT INTO users (name, age) VALUES
                ('Alice', 30),
                ('Bob', 25),
                ('Carol', 35)
        """)
    yield
    async with acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS users CASCADE")
