import asyncpg
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: Optional[asyncpg.Pool] = None

async def create_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        settings.database_url,
        ssl="require",          # Supabase requires SSL on all connections
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    logger.info("Database connection pool created.")

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call create_pool() first.")
    return _pool
