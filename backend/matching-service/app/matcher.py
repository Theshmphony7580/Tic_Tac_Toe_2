import hashlib
import logging
import time
from typing import Any

from app.database import get_pool
from app.embedder import embed_text
from app.gap_analysis import compute_gaps
from app.schemas import MatchRequest, MatchResult, CandidateMatch

logger = logging.getLogger(__name__)

PROFICIENCY_SCORES = {"Expert": 1.0, "Intermediate": 0.6, "Beginner": 0.3}


async def run_match(request: MatchRequest) -> MatchResult:
    start = time.perf_counter()
    pool = get_pool()

    # 1. Embed the JD
    jd_vector = embed_text(request.job_description)
    jd_hash = hashlib.md5(request.job_description.encode()).hexdigest()

    # Format vector as Postgres literal: '[0.1, 0.2, ...]'
    pg_vector_str = "[" + ",".join(str(v) for v in jd_vector) + "]"

    # 2. pgvector cosine similarity query
    query = """
        SELECT
            id::text,
            name,
            COALESCE(canonical_skills, ARRAY[]::text[]) AS canonical_skills,
            COALESCE(skill_proficiencies, '{}') AS skill_proficiencies,
            COALESCE(work_experience, '[]'::jsonb) AS work_experience,
            COALESCE(education, '[]'::jsonb) AS education,
            1 - (embedding <=> $1::vector) AS semantic_similarity
        FROM candidates
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> $1::vector) >= $2
        ORDER BY semantic_similarity DESC
        LIMIT $3;
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, pg_vector_str, request.threshold, request.top_k)

    total_scanned_query = "SELECT COUNT(*) FROM candidates WHERE embedding IS NOT NULL;"
    async with pool.acquire() as conn:
        total = await conn.fetchval(total_scanned_query)

    # 3. Score each candidate
    results: list[CandidateMatch] = []
    for row in rows:
        candidate_skills: list[str] = list(row["canonical_skills"] or [])
        proficiency_map: dict = dict(row["skill_proficiencies"] or {})
        
        # Skill match score
        skill_score = _compute_skill_score(
            candidate_skills, request.required_skills, request.nice_to_have_skills
        )
        
        # Experience depth score
        exp_score = _compute_experience_score(proficiency_map, request.required_skills)

        # Education relevance score (simple: does any degree field match JD keywords?)
        edu_score = _compute_education_score(row["education"], request.job_description)

        # Composite
        w = request.weights
        composite = (
            w.skill_match * skill_score
            + w.experience_depth * exp_score
            + w.education_relevance * edu_score
        )

        # Matched / missing skills
        matched = [s for s in request.required_skills if s in candidate_skills]
        gaps = compute_gaps(candidate_skills, request.required_skills, request.nice_to_have_skills)

        results.append(CandidateMatch(
            candidate_id=row["id"],
            candidate_name=row["name"] or "Unknown",
            semantic_similarity=round(row["semantic_similarity"], 4),
            skill_match_score=round(skill_score, 4),
            experience_score=round(exp_score, 4),
            education_score=round(edu_score, 4),
            composite_score=round(composite, 4),
            matched_skills=matched,
            missing_skills=gaps,
            proficiency_breakdown=proficiency_map,
        ))

    results.sort(key=lambda c: c.composite_score, reverse=True)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return MatchResult(
        job_description_hash=jd_hash,
        total_candidates_scanned=total or 0,
        threshold_used=request.threshold,
        results=results,
        processing_time_ms=elapsed_ms,
    )


def _compute_skill_score(
    candidate_skills: list[str],
    required: list[str],
    nice: list[str],
) -> float:
    if not required and not nice:
        return 0.0
    
    lowered = {s.lower() for s in candidate_skills}
    req_matched = sum(1 for s in required if s.lower() in lowered)
    nice_matched = sum(1 for s in nice if s.lower() in lowered)

    req_score = (req_matched / len(required)) if required else 0.0
    nice_score = (nice_matched / len(nice)) if nice else 0.0

    return req_score * 0.8 + nice_score * 0.2


def _compute_experience_score(
    proficiency_map: dict[str, str], required_skills: list[str]
) -> float:
    if not required_skills:
        return 0.0
    scores = []
    lowered_map = {k.lower(): v for k, v in proficiency_map.items()}
    for skill in required_skills:
        prof = lowered_map.get(skill.lower(), None)
        scores.append(PROFICIENCY_SCORES.get(prof, 0.1))
    return sum(scores) / len(scores)


def _compute_education_score(education_jsonb: Any, job_description: str) -> float:
    """Simple heuristic: if any education institution/degree keywords overlap with JD."""
    if not education_jsonb:
        return 0.5  # neutral
    jd_lower = job_description.lower()
    tech_keywords = ["engineer", "computer", "data", "science", "software", "information", "math"]
    if any(kw in jd_lower for kw in tech_keywords):
        # Check if candidate has a technical degree
        for edu in education_jsonb:
            # handle cases where edu is string instead of dict
            if isinstance(edu, dict):
                field = str(edu.get("field_of_study", "")).lower()
                degree = str(edu.get("degree", "")).lower()
            else:
                field = ""
                degree = str(edu).lower()
            if any(kw in field or kw in degree for kw in tech_keywords):
                return 1.0
        return 0.5
    return 0.5
