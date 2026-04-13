"""
Job Description Matcher — Find Best Candidates for a Role

Given a job description, this service:
1. Embeds the JD using sentence-transformers
2. Queries Supabase with pgvector to find similar candidates
3. Scores candidates using weighted metrics
4. Returns ranked list with gap analysis

Usage:
    POST /match-job
    {
        "job_description": "Looking for a Python developer with ML experience...",
        "required_skills": ["Python", "Machine Learning"],
        "nice_to_have_skills": ["TensorFlow", "AWS"]
    }

Returns:
    [
        {
            "candidate_id": "uuid",
            "name": "John Doe",
            "composite_score": 0.85,
            "semantic_similarity": 0.78,
            "skill_match_score": 0.92,
            "missing_skills": ["TensorFlow"]
        }
    ]
"""

import asyncio
import logging
import sys
from pathlib import Path

import asyncpg
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# ── Setup ─────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "matching-service"))
from app.config import get_settings  # noqa: E402

settings = get_settings()
model = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI(
    title="TalentIntel Job Matcher",
    description="Match job descriptions to candidates using semantic similarity",
    version="1.0.0"
)

# ── Models ────────────────────────────────────────────────────────────────────
class MatchJobRequest(BaseModel):
    job_description: str = Field(..., description="Full job description text")
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    top_k: int = Field(default=10, ge=1, le=100)

class SkillGap(BaseModel):
    skill_name: str
    importance: str  # "required" | "nice_to_have"

class CandidateMatch(BaseModel):
    candidate_id: str
    name: str
    email: Optional[str]
    composite_score: float
    semantic_similarity: float
    skill_match_score: float
    missing_skills: List[SkillGap]
    matched_skills: List[str]
    confidence: str  # "High" | "Medium" | "Low"

# ── Core Logic ────────────────────────────────────────────────────────────────
async def match_job_to_candidates(req: MatchJobRequest) -> List[CandidateMatch]:
    """Main matching logic."""
    logger.info(f"Matching job: {req.job_description[:50]}...")

    try:
        # 1. Embed job description
        logger.info("Generating job description embedding...")
        jd_embedding = model.encode(req.job_description, convert_to_numpy=True)
        jd_vector_str = "[" + ",".join(str(v) for v in jd_embedding) + "]"
        logger.info(f"✓ JD embedding generated ({len(jd_embedding)} dims)")

        # 2. Connect to DB
        logger.info("Connecting to database...")
        conn = await asyncpg.connect(settings.database_url, ssl="require")
        logger.info("✓ Connected to database")

        try:
            # 3. Query candidates with pgvector
            logger.info("Querying candidates with pgvector...")
            query = """
                SELECT
                    id::text,
                    name,
                    email,
                    canonical_skills,
                    skill_proficiencies,
                    1 - (embedding <=> $1::vector) AS semantic_similarity
                FROM candidates
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> $1::vector) >= $2
                ORDER BY semantic_similarity DESC
                LIMIT $3;
            """

            rows = await conn.fetch(
                query,
                jd_vector_str,
                req.threshold,
                req.top_k
            )
            logger.info(f"✓ Found {len(rows)} candidates")

            if not rows:
                logger.info("No candidates found above threshold")
                return []

            # 4. Score each candidate
            results = []
            for i, row in enumerate(rows):
                try:
                    logger.info(f"Scoring candidate {i+1}/{len(rows)}: {row['name']}")
                    candidate_skills = set(row["canonical_skills"] or [])
                    required_set = set(req.required_skills)
                    nice_set = set(req.nice_to_have_skills)

                    # Semantic similarity (from pgvector)
                    semantic_sim = float(row["semantic_similarity"])

                    # Skill match score
                    matched_required = len(candidate_skills & required_set)
                    matched_nice = len(candidate_skills & nice_set)
                    total_required = len(required_set)
                    total_nice = len(nice_set)

                    # Avoid division by zero
                    if total_required > 0:
                        skill_score_req = matched_required / total_required
                    else:
                        skill_score_req = 0.0

                    if total_nice > 0:
                        skill_score_nice = matched_nice / total_nice
                    else:
                        skill_score_nice = 0.0

                    # Weighted skill score (80% required, 20% nice-to-have)
                    skill_score = (skill_score_req * 0.8) + (skill_score_nice * 0.2)

                    # Composite score (weighted average)
                    # Handle NaN/inf values
                    if not (0 <= semantic_sim <= 1):
                        semantic_sim = 0.0
                    if not (0 <= skill_score <= 1):
                        skill_score = 0.0

                    composite = (semantic_sim * 0.6) + (skill_score * 0.4)

                    # Ensure valid range
                    composite = max(0.0, min(1.0, composite))

                    # Missing skills
                    missing_required = required_set - candidate_skills
                    missing_nice = nice_set - candidate_skills
                    missing_skills = [
                        SkillGap(skill_name=s, importance="required") for s in missing_required
                    ] + [
                        SkillGap(skill_name=s, importance="nice_to_have") for s in missing_nice
                    ]

                    # Matched skills
                    matched_skills = list(candidate_skills & (required_set | nice_set))

                    # Confidence level
                    if composite >= 0.8:
                        confidence = "High"
                    elif composite >= 0.6:
                        confidence = "Medium"
                    else:
                        confidence = "Low"

                    results.append(CandidateMatch(
                        candidate_id=row["id"],
                        name=row["name"] or "Unknown",
                        email=row["email"],
                        composite_score=round(composite, 4),
                        semantic_similarity=round(semantic_sim, 4),
                        skill_match_score=round(skill_score, 4),
                        missing_skills=missing_skills,
                        matched_skills=matched_skills,
                        confidence=confidence
                    ))
                except Exception as e:
                    logger.error(f"Error scoring candidate {row.get('name', 'Unknown')}: {e}")
                    continue

            # Sort by composite score
            results.sort(key=lambda c: c.composite_score, reverse=True)
            logger.info(f"✓ Ranked {len(results)} candidates")
            return results

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Match job failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── API Endpoint ──────────────────────────────────────────────────────────────
@app.post("/match-job", response_model=List[CandidateMatch])
async def match_job_endpoint(req: MatchJobRequest):
    """Match job description to best candidates."""
    try:
        logger.info(f"Incoming match request: {req.job_description[:50]}...")
        results = await match_job_to_candidates(req)
        logger.info(f"Returning {len(results)} candidates")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "job-matcher"}

# ── Run Server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)