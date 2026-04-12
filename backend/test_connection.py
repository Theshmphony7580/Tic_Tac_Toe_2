"""Test Supabase connection"""
import asyncio
import asyncpg
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings

async def test():
    settings = get_settings()
    print(f"Testing connection to: {settings.database_url[:50]}...")

    try:
        # Try with ssl="require"
        conn = await asyncpg.connect(settings.database_url, ssl="require", timeout=10)
        result = await conn.fetchval("SELECT 1;")
        print(f"✓ Connected! Query result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed with ssl='require': {e}")

    try:
        # Try without ssl
        conn = await asyncpg.connect(settings.database_url, timeout=10)
        result = await conn.fetchval("SELECT 1;")
        print(f"✓ Connected (no SSL)! Query result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed without ssl: {e}")
        return False

asyncio.run(test())
