"""
Populate Vector Database with 500+ Sample Resumes

Walks backend/data/resumes/{CATEGORY}/*.pdf, processes each one:
  parse → LLM extract → fuzzy normalize → embed → store in Supabase

Usage:
    cd backend
    python populate_vector_db.py

Prerequisites:
    pip install pymupdf4llm pymupdf asyncpg rapidfuzz sentence-transformers groq pydantic pydantic-settings
    GROQ_API_KEY must be set in matching-service/.env or as env var
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import asyncpg
from sentence_transformers import SentenceTransformer

# ── path setup so we can import directly from each service ──────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parser-service"))
sys.path.insert(0, str(ROOT / "normalization-service"))
sys.path.insert(0, str(ROOT / "matching-service"))

from app.parsers.pdf_parser import parse_pdf                      # noqa: E402
from app.extraction import extract_from_text                      # noqa: E402 (parser-service)

# We re-insert path so normalization-service's "app" module wins
sys.path.insert(0, str(ROOT / "normalization-service"))
from app.fuzzy_matcher import normalize_skills_via_fuzzy          # noqa: E402
from app.schemas import TaxonomyRecord                            # noqa: E402

# matching-service config has the DB URL
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings                               # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

RESUMES_DIR = ROOT / "data" / "resumes"
settings = get_settings()

# Load embedding model once (downloads ~90MB on first run)
logger.info("Loading sentence-transformers model...")
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
logger.info("Model loaded.")


# ── helpers ──────────────────────────────────────────────────────────────────

def embed(text: str) -> list[float]:
    if not text:
        return []
    return EMBEDDER.encode(text, convert_to_numpy=True).tolist()


async def load_taxonomy(conn: asyncpg.Connection) -> list[TaxonomyRecord]:
    rows = await conn.fetch(
        "SELECT canonical_name, aliases, category FROM skill_taxonomy;"
    )
    return [
        TaxonomyRecord(
            canonical_name=r["canonical_name"],
            aliases=r["aliases"] or [],
            category=r["category"],
        )
        for r in rows
    ]


async def store_candidate(
    conn: asyncpg.Connection,
    data: dict,
    embedding: list[float] | None,
    file_path: Path,
    category: str,
) -> str | None:
    embedding_str = (
        "[" + ",".join(str(v) for v in embedding) + "]" if embedding else None
    )

    query = """
        INSERT INTO candidates (
            name, email, phone, location, linkedin_url, portfolio_url, summary,
            work_experience, education, certifications, projects,
            raw_skills, canonical_skills, skill_proficiencies,
            embedding, source_file_url, file_type, processing_status
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,
            $8::jsonb,$9::jsonb,$10::jsonb,$11::jsonb,
            $12,$13,$14::jsonb,
            $16::vector,$17,$18,'complete'
        )
        ON CONFLICT DO NOTHING
        RETURNING id::text;
    """
    # Note: $15 skipped intentionally (embedding_str is $16 positionally via rewrite below)
    # Rewriting cleanly:
    query = """
        INSERT INTO candidates (
            name, email, phone, location, linkedin_url, portfolio_url, summary,
            work_experience, education, certifications, projects,
            raw_skills, canonical_skills, skill_proficiencies,
            embedding, source_file_url, file_type, processing_status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7,
            $8::jsonb, $9::jsonb, $10::jsonb, $11::jsonb,
            $12, $13, $14::jsonb,
            $15::vector, $16, $17, 'complete'
        )
        RETURNING id::text;
    """

    return await conn.fetchval(
        query,
        data.get("name"),
        data.get("email"),
        data.get("phone"),
        data.get("location"),
        data.get("linkedin_url"),
        data.get("portfolio_url"),
        data.get("summary"),
        json.dumps(data.get("work_experience", [])),
        json.dumps(data.get("education", [])),
        json.dumps(data.get("certifications", [])),
        json.dumps(data.get("projects", [])),
        data.get("raw_skills", []),
        data.get("canonical_skills", []),
        json.dumps(data.get("skill_proficiencies", {})),
        embedding_str,
        str(file_path),
        file_path.suffix.lower().lstrip("."),
    )


# ── main pipeline ─────────────────────────────────────────────────────────────

async def main():
    # Collect all PDF files across category folders
    all_files: list[tuple[Path, str]] = []
    for category_dir in sorted(RESUMES_DIR.iterdir()):
        if category_dir.is_dir():
            for pdf in sorted(category_dir.glob("*.pdf")):
                all_files.append((pdf, category_dir.name))

    if not all_files:
        logger.error(f"No PDFs found under {RESUMES_DIR}")
        return

    logger.info(f"Found {len(all_files)} resumes across {len(set(c for _, c in all_files))} categories")

    conn = await asyncpg.connect(settings.database_url, ssl="require")
    logger.info("Connected to database")

    try:
        taxonomy = await load_taxonomy(conn)
        logger.info(f"Loaded {len(taxonomy)} skills from taxonomy")

        success, failed, skipped = 0, 0, 0

        for i, (pdf_path, category) in enumerate(all_files, 1):
            logger.info(f"[{i}/{len(all_files)}] {category}/{pdf_path.name}")
            try:
                # 1. Parse PDF → raw text
                file_bytes = pdf_path.read_bytes()
                raw_text = parse_pdf(file_bytes)
                if not raw_text.strip():
                    logger.warning("  Empty text, skipping")
                    skipped += 1
                    continue

                # 2. LLM extraction
                parsed = extract_from_text(raw_text)
                if parsed.confidence_score < 0.3:
                    logger.warning(f"  Low confidence ({parsed.confidence_score:.2f}), skipping")
                    skipped += 1
                    continue

                # 3. Skill normalization (fuzzy only, no Redis needed)
                normalized, unresolved = normalize_skills_via_fuzzy(
                    parsed.raw_skills, taxonomy
                )
                canonical_skills = [n.canonical_name for n in normalized]
                skill_proficiencies = {n.canonical_name: "Intermediate" for n in normalized}

                data = {
                    **parsed.model_dump(),
                    "canonical_skills": canonical_skills,
                    "skill_proficiencies": skill_proficiencies,
                }

                # 4. Embed (use raw_text; summary if available)
                embed_input = parsed.summary or raw_text[:2000]
                embedding = embed(embed_input)

                # 5. Store
                candidate_id = await store_candidate(conn, data, embedding, pdf_path, category)
                if candidate_id:
                    logger.info(f"  ✓ {parsed.name or 'Unknown'} → {candidate_id}")
                    success += 1
                else:
                    logger.info("  ⟳ Already exists (skipped)")
                    skipped += 1

            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                failed += 1
                continue

            # Small pause every 10 resumes to respect Groq rate limits
            if i % 10 == 0:
                await asyncio.sleep(1)

        logger.info(f"\n{'='*60}")
        logger.info(f"Done! Success: {success} | Skipped: {skipped} | Failed: {failed}")
        logger.info(f"{'='*60}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
