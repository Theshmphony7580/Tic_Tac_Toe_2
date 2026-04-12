"""
main.py — Orchestrator Service FastAPI entrypoint.

Endpoints:
    POST /process           — Accepts a resume file path, creates a job,
                              enqueues Celery pipeline task, returns job_id.
    GET  /status/{job_id}   — Polls batch_jobs table for current job status.
    GET  /health            — Simple health probe.
"""

import logging
import uuid

import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from app.config import get_settings
from app.workers import process_resume_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="TalentIntel Orchestrator Service",
    description=(
        "Central pipeline coordinator. Accepts resume jobs, enqueues them to "
        "Celery workers running the LangGraph state machine (parse → normalize → store)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Request / Response Schemas ────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    file_url: str
    file_type: str = "pdf"
    job_description: str | None = None
    required_skills: list[str] | None = None
    nice_to_have_skills: list[str] | None = None
    threshold: float = 0.0
    top_k: int = 5

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"pdf", "docx", "txt"}:
            raise ValueError("file_type must be 'pdf', 'docx', or 'txt'")
        return v


class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    processed_files: int
    failed_files: int
    completed_at: str | None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/process", response_model=ProcessResponse, status_code=202)
async def process_resume(req: ProcessRequest) -> ProcessResponse:
    """
    1. Validates the incoming request.
    2. Creates a tracking row in batch_jobs (status='queued').
    3. Enqueues the Celery pipeline task asynchronously.
    4. Returns immediately with the job_id for polling.
    """
    job_id = str(uuid.uuid4())

    # Insert job record into batch_jobs before enqueuing
    try:
        conn: asyncpg.Connection = await asyncpg.connect(settings.database_url, ssl="require")
        try:
            await conn.execute(
                """
                INSERT INTO batch_jobs (id, total_files, processed_files, failed_files, status)
                VALUES ($1, 1, 0, 0, 'queued')
                """,
                uuid.UUID(job_id),
            )
        finally:
            await conn.close()
    except Exception as exc:
        logger.error(f"Failed to insert batch_job record for {job_id}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable — could not create job record.",
        )

    import asyncio
    from app.graph import resume_graph
    from app.state import ResumeProcessingState
    import time

    # User requested to bypass the queue locally entirely! 
    # Just run LangGraph natively as a background async task.
    initial_state: ResumeProcessingState = {
        "job_id": job_id,
        "file_url": req.file_url,
        "file_type": req.file_type,
        "parsed_resume": None,
        "raw_skills": None,
        "parse_error": None,
        "parse_retries": 0,
        "normalized_skills": None,
        "normalization_error": None,
        "normalize_retries": 0,
        "job_description": req.job_description,
        "required_skills": req.required_skills,
        "nice_to_have_skills": req.nice_to_have_skills,
        "threshold": req.threshold,
        "top_k": req.top_k,
        "candidate_id": None,
        "embedding_stored": False,
        "store_error": None,
        "match_result": None,
        "match_error": None,
        "match_processing_time_ms": None,
        "status": "parsing",
        "start_time": time.time(),
        "end_time": None,
        "latency_ms": None,
    }
    try:
        # We are awaiting the graph directly! This means the HTTP request will 
        # WAIT until the ENTIRE pipeline (parse -> normalize -> match) is done!
        await resume_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ProcessResponse(
        job_id=job_id,
        status="queued",
        message=f"Resume processing started. Poll GET /status/{job_id} for updates.",
    )


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(job_id: str) -> StatusResponse:
    """
    Queries the batch_jobs table and returns the current status of a pipeline job.
    """
    # Validate that job_id is a valid UUID
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format (must be UUID).")

    try:
        conn: asyncpg.Connection = await asyncpg.connect(settings.database_url, ssl="require")
        try:
            row = await conn.fetchrow(
                """
                SELECT status, processed_files, failed_files, completed_at
                FROM batch_jobs
                WHERE id = $1
                """,
                uuid.UUID(job_id),
            )
        finally:
            await conn.close()
    except Exception as exc:
        logger.error(f"DB error fetching status for job {job_id}: {exc}")
        raise HTTPException(status_code=503, detail=f"Database error: {exc}")

    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return StatusResponse(
        job_id=job_id,
        status=row["status"],
        processed_files=row["processed_files"] or 0,
        failed_files=row["failed_files"] or 0,
        completed_at=str(row["completed_at"]) if row["completed_at"] else None,
    )


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.service_name}