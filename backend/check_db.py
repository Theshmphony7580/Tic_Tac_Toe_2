"""Check what's actually in the candidates table"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings
import asyncpg

async def check_db():
    settings = get_settings()

    print("Connecting to database...")
    conn = await asyncpg.connect(settings.database_url, ssl="require")

    try:
        # Check total candidates
        count = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        print(f"Total candidates: {count}")

        # Check one candidate
        row = await conn.fetchrow("""
            SELECT
                id, name, email, canonical_skills, skill_proficiencies, embedding
            FROM candidates
            LIMIT 1
        """)

        if row:
            print(f"\nSample candidate:")
            print(f"  ID: {row['id']}")
            print(f"  Name: {row['name']}")
            print(f"  Email: {row['email']}")
            print(f"  Canonical skills: {row['canonical_skills']}")
            print(f"  Skill proficiencies: {row['skill_proficiencies']}")
            print(f"  Embedding: {type(row['embedding'])} ({len(row['embedding']) if row['embedding'] else 0} dims)")
        else:
            print("No candidates found!")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_db())
