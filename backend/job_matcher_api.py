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

    # 1. Embed job description
    jd_embedding = model.encode(req.job_description, convert_to_numpy=True)
    jd_vector_str = "[" + ",".join(str(v) for v in jd_embedding) + "]"

    # 2. Connect to DB
    conn = await asyncpg.connect(settings.database_url, ssl="require")

    try:
        # 3. Query candidates with pgvector
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

        if not rows:
            logger.info("No candidates found above threshold")
            return []

        # 4. Score each candidate
        results = []
        for row in rows:
            candidate_skills = set(row["canonical_skills"] or [])
            required_set = set(req.required_skills)
            nice_set = set(req.nice_to_have_skills)

            # Semantic similarity (from pgvector)
            semantic_sim = float(row["semantic_similarity"])

            # Skill match score
            matched_required = len(candidate_skills & required_set)
            matched_nice = len(candidate_skills & nice_set)
            total_required = len(required_set)

            if total_required > 0:
                skill_score = (matched_required / total_required) * 0.8
                if nice_set:
                    skill_score += (matched_nice / len(nice_set)) * 0.2
            else:
                skill_score = 0.5  # Neutral if no required skills

            # Composite score (weighted average)
            composite = (semantic_sim * 0.6) + (skill_score * 0.4)

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

        # Sort by composite score
        results.sort(key=lambda c: c.composite_score, reverse=True)
        return results

    finally:
        await conn.close()


# ── API Endpoint ──────────────────────────────────────────────────────────────
@app.post("/match-job", response_model=List[CandidateMatch])
async def match_job_endpoint(req: MatchJobRequest):
    """Match job description to best candidates."""
    try:
        results = await match_job_to_candidates(req)
        logger.info(f"Returned {len(results)} candidates")
        return results
    except Exception as e:
        logger.error(f"Match failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "job-matcher"}

# ── Run Server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
