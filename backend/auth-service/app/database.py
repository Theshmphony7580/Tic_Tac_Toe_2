import asyncpg
from app.config import DATABASE_URL

pool: asyncpg.Pool | None = None


async def init_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    print("[database] Connection pool created")


async def close_pool():
    global pool
    if pool:
        await pool.close()
        print("[database] Connection pool closed")


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool
