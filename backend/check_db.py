"""
Quick connectivity check for Supabase pgvector.
Run from: f:\Tic_Tac_Toe_2\backend
  python check_db.py
"""
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:ipQSzoJqgTyjM2mK@db.gwsfdlnfrdasntqyffdo.supabase.co:5432/postgres"
)

async def main():
    print(f"🔌 Connecting to: {DATABASE_URL[:40]}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL, ssl="require", timeout=10)

        # 1. Basic connectivity
        version = await conn.fetchval("SELECT version();")
        print(f"✅ Connected! PostgreSQL: {version[:60]}")

        # 2. pgvector extension present?
        pgvector = await conn.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
        )
        if pgvector:
            print(f"✅ pgvector extension found (v{pgvector})")
        else:
            print("⚠️  pgvector extension NOT installed in this database.")

        # 3. List relevant tables
        tables = await conn.fetch(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
            """
        )
        if tables:
            print(f"📋 Tables in public schema: {[t['tablename'] for t in tables]}")
        else:
            print("⚠️  No tables found in public schema (migrations not run yet?)")

        await conn.close()
        print("\n🎉 Vector DB check complete.")

    except Exception as e:
        print(f"❌ Connection FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
