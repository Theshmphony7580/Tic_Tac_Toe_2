"""Test connection using IPv4 address instead of hostname"""
import asyncio
import asyncpg

async def test():
    # Use the IPv4 address directly instead of hostname
    url = 'postgresql://postgres:ipQSzoJqgTyjM2mK@49.44.79.236:5432/postgres'
    print(f"Testing with IPv4: 49.44.79.236...")

    try:
        conn = await asyncpg.connect(url, ssl='require', timeout=10)
        result = await conn.fetchval('SELECT 1;')
        print(f'✓ Success with IPv4! Result: {result}')
        await conn.close()
        return True
    except Exception as e:
        import traceback
        print(f'✗ Failed: {e}')
        traceback.print_exc()
        return False

asyncio.run(test())
