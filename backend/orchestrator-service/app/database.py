import json
import logging
import uuid
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


async def insert_candidate(
    conn: asyncpg.Connection,
    parsed_data: dict,
    canonical_skills: list[str],
    embedding: list[float],
    file_url: str,
    file_type: str,
) -> str:
    """
    Insert a new candidate row into the candidates table.
    Returns the UUID of the inserted row as a string.

    parsed_data: the "data" sub-dict from ParseResponse (a ParsedCandidate).
    canonical_skills: list of canonical skill name strings from Normalizer.
    embedding: 384-dimensional float vector from sentence-transformers.
    """
    candidate_id = str(uuid.uuid4())

    # Serialize JSONB fields
    work_experience_json = json.dumps(parsed_data.get("work_experience") or [])
    education_json = json.dumps(parsed_data.get("education") or [])
    certifications_json = json.dumps(parsed_data.get("certifications") or [])
    projects_json = json.dumps(parsed_data.get("projects") or [])

    # Format embedding as a Postgres vector literal string: '[0.1,0.2,...]'
    pg_vector_str = "[" + ",".join(str(v) for v in embedding) + "]"

    raw_skills: list[str] = parsed_data.get("raw_skills") or []

    await conn.execute(
        """
        INSERT INTO candidates (
            id,
            name,
            email,
            phone,
            location,
            linkedin_url,
            portfolio_url,
            summary,
            work_experience,
            education,
            certifications,
            projects,
            raw_skills,
            canonical_skills,
            skill_proficiencies,
            inferred_skills,
            embedding,
            source_file_url,
            file_type,
            processing_status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8,
            $9::jsonb, $10::jsonb, $11::jsonb, $12::jsonb,
            $13, $14, $15::jsonb, $16,
            $17::vector,
            $18, $19, 'complete'
        )
        ON CONFLICT DO NOTHING
        """,
        uuid.UUID(candidate_id),          # $1  id
        parsed_data.get("name"),           # $2  name
        parsed_data.get("email"),          # $3  email
        parsed_data.get("phone"),          # $4  phone
        parsed_data.get("location"),       # $5  location
        parsed_data.get("linkedin_url"),   # $6  linkedin_url
        parsed_data.get("portfolio_url"),  # $7  portfolio_url
        parsed_data.get("summary"),        # $8  summary
        work_experience_json,              # $9  work_experience
        education_json,                    # $10 education
        certifications_json,               # $11 certifications
        projects_json,                     # $12 projects
        raw_skills,                        # $13 raw_skills (text[])
        canonical_skills,                  # $14 canonical_skills (text[])
        "{}",                              # $15 skill_proficiencies (empty jsonb)
        [],                                # $16 inferred_skills (text[])
        pg_vector_str,                     # $17 embedding (vector)
        file_url,                          # $18 source_file_url
        file_type,                         # $19 file_type
    )

    logger.info(f"Candidate {candidate_id} inserted successfully.")
    return candidate_id


async def update_job_status(
    conn: asyncpg.Connection,
    job_id: str,
    status: str,
    candidate_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    Update the batch_jobs row for this job_id with the latest status.
    Also updates processed_files / failed_files counters and completed_at timestamp.
    """
    await conn.execute(
        """
        UPDATE batch_jobs
        SET
            status           = $2,
            processed_files  = CASE WHEN $2 = 'complete' THEN 1 ELSE 0 END,
            failed_files     = CASE WHEN $2 = 'failed'   THEN 1 ELSE 0 END,
            completed_at     = CASE WHEN $2 IN ('complete', 'failed') THEN NOW() ELSE NULL END
        WHERE id = $1
        """,
        uuid.UUID(job_id),
        status,
    )
    logger.info(f"Job {job_id} status updated to '{status}'.")
