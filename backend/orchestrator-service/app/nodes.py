"""
nodes.py — All LangGraph node functions and edge router functions.

Node execution flow:
    parse ──(success)──► normalize ──(success)──► store ──► END
      │                       │
   (fail/retry)          (fail/retry)
      │                       │
      └──(max retries)──► handle_error ──► END
                              │
                    normalize fail (max) ──► store (graceful)
"""

import logging
import time
from pathlib import Path

import asyncpg
import httpx

from app.config import get_settings
from app.database import insert_candidate, update_job_status
from app.embedder import embed_text
from app.state import ResumeProcessingState

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


# ─────────────────────────────────────────────────────────────────────────────
# NODE A: call_parser
# ─────────────────────────────────────────────────────────────────────────────

async def call_parser(state: ResumeProcessingState) -> dict:
    """
    Sends the resume file to the Parser Service via multipart HTTP POST.

    Parser endpoint: POST {parser_url}/internal/parse
    Form field: file (UploadFile)
    Response: { success: bool, data: ParsedCandidate, processing_time_ms: int }
    """
    settings = get_settings()
    file_path = state["file_url"]
    job_id = state["job_id"]

    logger.info(f"[{job_id}] Calling Parser Service (attempt {state['parse_retries'] + 1}) ...")

    try:
        path_obj = Path(file_path)

        # Determine MIME type by extension
        suffix = path_obj.suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
        }
        mime_type = mime_map.get(suffix, "application/octet-stream")

        async with httpx.AsyncClient(timeout=settings.parser_timeout_seconds) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{settings.parser_url}/internal/parse",
                    files={"file": (path_obj.name, f, mime_type)},
                )

        if response.status_code != 200:
            raise ValueError(
                f"Parser returned HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()

        # Guard: parser returned success=False
        if not data.get("success", False):
            error_detail = data.get("error") or "Parser returned success=False"
            raise ValueError(error_detail)

        parsed_data = data.get("data") or {}
        raw_skills: list[str] = parsed_data.get("raw_skills") or []

        logger.info(
            f"[{job_id}] Parser success: {len(raw_skills)} raw skills extracted."
        )

        return {
            "parsed_resume": data,
            "raw_skills": raw_skills,
            "parse_error": None,
            "status": "normalizing",
        }

    except FileNotFoundError:
        error = f"Resume file not found at path: {file_path}"
        logger.error(f"[{job_id}] {error}")
        # File not found is unrecoverable — skip retries
        return {
            "parse_error": error,
            "parse_retries": MAX_RETRIES,
            "status": "failed",
        }

    except Exception as exc:
        retries = state["parse_retries"] + 1
        logger.error(f"[{job_id}] Parser attempt {retries} failed: {exc}")
        return {
            "parse_error": str(exc),
            "parse_retries": retries,
            "status": "parsing" if retries < MAX_RETRIES else "failed",
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE B: call_normalizer
# ─────────────────────────────────────────────────────────────────────────────

async def call_normalizer(state: ResumeProcessingState) -> dict:
    """
    Sends raw_skills list to the Normalization Service via JSON POST.

    Normalizer endpoint: POST {normalizer_url}/internal/normalize
    Body: { "raw_skills": [...], "candidate_id": "<job_id>" }
    Response: { success: bool, normalized_skills: [...], processing_time_ms: int }
    """
    settings = get_settings()
    job_id = state["job_id"]
    raw_skills = state.get("raw_skills") or []

    logger.info(
        f"[{job_id}] Calling Normalizer Service with {len(raw_skills)} skills "
        f"(attempt {state['normalize_retries'] + 1}) ..."
    )

    try:
        async with httpx.AsyncClient(timeout=settings.normalizer_timeout_seconds) as client:
            response = await client.post(
                f"{settings.normalizer_url}/internal/normalize",
                json={
                    "raw_skills": raw_skills,
                    "candidate_id": job_id,
                },
            )

        if response.status_code != 200:
            raise ValueError(
                f"Normalizer returned HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        normalized: list[dict] = data.get("normalized_skills") or []

        logger.info(
            f"[{job_id}] Normalizer success: {len(normalized)} skills normalized "
            f"in {data.get('processing_time_ms')}ms."
        )

        return {
            "normalized_skills": normalized,
            "normalization_error": None,
            "status": "storing",
        }

    except Exception as exc:
        retries = state["normalize_retries"] + 1
        logger.error(f"[{job_id}] Normalizer attempt {retries} failed: {exc}")
        return {
            "normalization_error": str(exc),
            "normalize_retries": retries,
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE C: store_in_db
# ─────────────────────────────────────────────────────────────────────────────

async def store_in_db(state: ResumeProcessingState) -> dict:
    """
    1. Extracts canonical skill names from normalized_skills.
    2. Builds an embedding text string and generates a 384-dim vector.
    3. Inserts the candidate record into Supabase (candidates table).
    4. Updates batch_jobs status to 'complete'.
    """
    settings = get_settings()
    job_id = state["job_id"]

    logger.info(f"[{job_id}] Storing candidate in database ...")

    try:
        # Extract canonical skill names
        normalized = state.get("normalized_skills") or []
        canonical_skills: list[str] = [
            s["canonical_name"]
            for s in normalized
            if s.get("canonical_name")
        ]

        # Fall back to raw skills if normalization failed or returned nothing
        embed_source = (
            " ".join(canonical_skills)
            if canonical_skills
            else " ".join(state.get("raw_skills") or [])
        )

        # Generate embedding vector
        embedding: list[float] = embed_text(embed_source) if embed_source.strip() else [0.0] * 384

        # Get the parsed candidate data sub-dict
        parsed_data: dict = (state.get("parsed_resume") or {}).get("data") or {}

        conn: asyncpg.Connection = await asyncpg.connect(settings.database_url)
        try:
            candidate_id = await insert_candidate(
                conn=conn,
                parsed_data=parsed_data,
                canonical_skills=canonical_skills,
                embedding=embedding,
                file_url=state["file_url"],
                file_type=state["file_type"],
            )
            await update_job_status(conn, job_id, "complete", candidate_id)
        finally:
            await conn.close()

        end_time = time.time()
        latency_ms = int((end_time - state["start_time"]) * 1000)

        logger.info(
            f"[{job_id}] Candidate {candidate_id} stored. "
            f"Total pipeline latency: {latency_ms}ms."
        )

        return {
            "candidate_id": candidate_id,
            "embedding_stored": True,
            "store_error": None,
            "status": "complete",
            "end_time": end_time,
            "latency_ms": latency_ms,
        }

    except Exception as exc:
        logger.error(f"[{job_id}] DB store failed: {exc}")
        return {
            "store_error": str(exc),
            "embedding_stored": False,
            "status": "failed",
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE D: handle_error
# ─────────────────────────────────────────────────────────────────────────────

async def handle_error(state: ResumeProcessingState) -> dict:
    """
    Called when the pipeline cannot recover (max retries exceeded on parse,
    or DB store failure). Updates batch_jobs to 'failed' status.
    """
    settings = get_settings()
    job_id = state["job_id"]

    error_msg = (
        state.get("parse_error")
        or state.get("normalization_error")
        or state.get("store_error")
        or "Unknown pipeline error"
    )

    logger.error(f"[{job_id}] Pipeline failed: {error_msg}")

    try:
        conn: asyncpg.Connection = await asyncpg.connect(settings.database_url)
        try:
            await update_job_status(conn, job_id, "failed", error_message=error_msg)
        finally:
            await conn.close()
    except Exception as db_exc:
        logger.error(f"[{job_id}] Could not mark job as failed in DB: {db_exc}")

    end_time = time.time()
    latency_ms = int((end_time - state["start_time"]) * 1000)

    return {
        "status": "failed",
        "end_time": end_time,
        "latency_ms": latency_ms,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EDGE ROUTERS (pure functions — no async, no side effects)
# ─────────────────────────────────────────────────────────────────────────────

def route_after_parse(state: ResumeProcessingState) -> str:
    """
    Decides which node to run after a parse attempt.

    ─ No error        → "normalize"
    ─ Error, retries remaining → "parse"  (retry loop)
    ─ Error, max retries hit   → "handle_error"
    """
    if not state.get("parse_error"):
        return "normalize"
    if state["parse_retries"] >= MAX_RETRIES:
        return "handle_error"
    return "parse"


def route_after_normalize(state: ResumeProcessingState) -> str:
    """
    Decides which node to run after a normalization attempt.

    ─ No error        → "store"
    ─ Error, retries remaining → "normalize"  (retry loop)
    ─ Error, max retries hit   → "store" (graceful degradation: store with raw skills)
      This prevents losing a successfully-parsed resume just because normalization failed.
    """
    if not state.get("normalization_error"):
        return "store"
    if state["normalize_retries"] >= MAX_RETRIES:
        # Graceful: store the candidate with raw (un-normalized) skills
        logger.warning(
            f"[{state['job_id']}] Normalizer max retries reached — "
            "storing with raw skills (graceful degradation)."
        )
        return "store"
    return "normalize"
