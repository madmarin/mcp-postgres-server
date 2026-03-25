"""Async connection pool management (singleton per process)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import psycopg
from loguru import logger
from psycopg_pool import AsyncConnectionPool

from mcp_postgres import exceptions as exc
from mcp_postgres.config import Settings

_pool: AsyncConnectionPool | None = None


async def init_pool(settings: Settings) -> None:
    global _pool
    if _pool is not None:
        return
    try:
        logger.info(
            "Initializing connection pool (min={}, max={})",
            settings.pool_min_size,
            settings.pool_max_size,
        )
        _pool = AsyncConnectionPool(
            conninfo=settings.psycopg_conninfo,
            min_size=settings.pool_min_size,
            max_size=settings.pool_max_size,
            open=False,
        )
        await _pool.open()
        logger.info("Connection pool ready")
    except Exception as e:
        raise exc.ConnectionError(
            "Could not connect to the database. Check your connection settings.",
            detail=str(e),
        ) from e


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise exc.ConnectionError("Database pool is not initialized. Start the server first.")
    return _pool


@asynccontextmanager
async def acquire() -> AsyncIterator[psycopg.AsyncConnection]:
    pool = get_pool()
    async with pool.connection() as conn:
        yield conn
