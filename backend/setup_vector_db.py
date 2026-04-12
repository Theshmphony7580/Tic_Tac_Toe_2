"""
Initialize Vector Database Schema on Supabase

Steps:
1. Applies init.sql (creates tables + pgvector + skill_embeddings)
2. Applies seed_taxonomy.sql (loads 54 canonical skills)
3. Generates and stores 384-dim embeddings for all 54 skills
   so semantically similar skills cluster together in vector space

Usage:
    cd backend
    python setup_vector_db.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import asyncpg
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings  # noqa: E402

settings = get_settings()


async def run_sql_file(conn: asyncpg.Connection, sql_file: Path) -> bool:
    """Execute a SQL file statement by statement."""
    if not sql_file.exists():
        logger.error(f"SQL file not found: {sql_file}")
        return False

    logger.info(f"Running {sql_file.name}...")
    sql = sql_file.read_text(encoding="utf-8")

    # Split on semicolons but skip empty chunks
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    ok, warn = 0, 0
    for stmt in statements:
        try:
            await conn.execute(stmt)
            ok += 1
        except Exception as e:
            logger.warning(f"  skipped: {str(e)[:120]}")
            warn += 1

    logger.info(f"✓ {sql_file.name} — {ok} ok, {warn} skipped")
    return True


async def embed_skills(conn: asyncpg.Connection, model: SentenceTransformer):
    """
    Generate 384-dim embeddings for every skill in skill_taxonomy
    and store them in skill_embeddings table.

    Embedding input = canonical_name + aliases + description
    so synonyms map into the same region of vector space.
    """
    rows = await conn.fetch(
        """
        SELECT st.id, st.canonical_name, st.aliases, st.description, st.parent_skills
        FROM skill_taxonomy st
        LEFT JOIN skill_embeddings se ON se.skill_id = st.id
        WHERE se.id IS NULL;   -- only embed skills not already done
        """
    )

    if not rows:
        logger.info("All skills already embedded — nothing to do")
        return

    logger.info(f"Embedding {len(rows)} skills...")

    for row in rows:
        # Build rich text: canonical + aliases + description + parent skills
        parts = [row["canonical_name"]]
        if row["aliases"]:
            parts.extend(row["aliases"])
        if row["description"]:
            parts.append(row["description"])
        if row["parent_skills"]:
            parts.extend(row["parent_skills"])

        embed_text = " | ".join(parts)
        vector = model.encode(embed_text, convert_to_numpy=True).tolist()
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"

        await conn.execute(
            """
            INSERT INTO skill_embeddings (skill_id, canonical_name, embedding)
            VALUES ($1, $2, $3::vector)
            ON CONFLICT (canonical_name) DO NOTHING;
            """,
            row["id"],
            row["canonical_name"],
            vector_str,
        )
        logger.info(f"  ✓ {row['canonical_name']}")

    logger.info(f"✓ Embedded {len(rows)} skills into skill_embeddings")


async def main():
    logger.info(f"Connecting to: {settings.database_url[:40]}...")
    try:
        conn = await asyncpg.connect(settings.database_url, ssl="require")
        logger.info("✓ Connected")
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        logger.error("Check: 1) Supabase project is not paused  2) URL is correct")
        return False

    try:
        db_dir = ROOT / "core-infrastructure" / "database"

        # Step 1: Schema
        if not await run_sql_file(conn, db_dir / "init.sql"):
            return False

        # Step 2: Seed taxonomy (54 canonical skills)
        if not await run_sql_file(conn, db_dir / "seed_taxonomy.sql"):
            return False

        # Step 3: Embed all skills
        logger.info("\nLoading sentence-transformers model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model ready")
        await embed_skills(conn, model)

        # Summary
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
        )
        skill_count   = await conn.fetchval("SELECT COUNT(*) FROM skill_taxonomy;")
        embed_count   = await conn.fetchval("SELECT COUNT(*) FROM skill_embeddings;")
        pgvec_ok      = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname='vector';")

        logger.info("\n" + "="*60)
        logger.info("Vector DB Setup Complete!")
        logger.info(f"  Tables created : {len(tables)}")
        logger.info(f"  pgvector       : {'✓' if pgvec_ok else '✗'}")
        logger.info(f"  Taxonomy skills: {skill_count}")
        logger.info(f"  Skill vectors  : {embed_count}")
        logger.info("="*60)
        return True

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
