"""
workers.py — Celery application and task definitions.

Celery workers are synchronous OS processes.
LangGraph's .ainvoke() is a coroutine.
We bridge them using asyncio.run() which creates a fresh event loop
per task invocation — the standard pattern for async-in-sync contexts.

To start the worker locally:
    celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
"""

import asyncio
import logging
import time

from celery import Celery

from app.config import get_settings
from app.graph import resume_graph
from app.state import ResumeProcessingState

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Celery application ────────────────────────────────────────────────────────
celery_app = Celery(
    "orchestrator",
    broker=settings.redis_url,
    backend=settings.redis_url,  # Store task results in Redis for polling
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Reliability
    task_track_started=True,        # Expose "STARTED" state in result backend
    task_acks_late=True,            # Only ACK after task completes (no lost jobs on crash)
    worker_prefetch_multiplier=1,   # Fetch one task at a time (pipeline is CPU-intensive)

    # TTL
    result_expires=3600,            # Results kept in Redis for 1 hour
)

# Apply Eager Mode for Redis-free local testing
if settings.celery_task_always_eager:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


# ── Main task ─────────────────────────────────────────────────────────────────
@celery_app.task(
    bind=True,
    name="orchestrator.process_resume",
    max_retries=0,  # LangGraph handles retries internally via edge routers
)
def process_resume_task(self, job_id: str, file_url: str, file_type: str) -> dict:
    """
    Main Celery pipeline task.

    Called via: process_resume_task.delay(job_id, file_url, file_type)

    Builds the initial LangGraph state and runs the compiled resume_graph
    using asyncio.run() to bridge synchronous Celery into async LangGraph.

    Returns a summary dict that gets stored in Redis by Celery.
    """
    logger.info(f"[{job_id}] Celery task received — launching LangGraph pipeline ...")

    initial_state: ResumeProcessingState = {
        "job_id": job_id,
        "file_url": file_url,
        "file_type": file_type,
        "parsed_resume": None,
        "raw_skills": None,
        "parse_error": None,
        "parse_retries": 0,
        "normalized_skills": None,
        "normalization_error": None,
        "normalize_retries": 0,
        "candidate_id": None,
        "embedding_stored": False,
        "store_error": None,
        "status": "parsing",
        "start_time": time.time(),
        "end_time": None,
        "latency_ms": None,
    }

    try:
        # asyncio.run() creates a brand-new event loop for this sync context
        final_state: ResumeProcessingState = asyncio.run(
            resume_graph.ainvoke(initial_state)
        )
    except Exception as exc:
        logger.exception(f"[{job_id}] Unhandled exception in LangGraph pipeline: {exc}")
        return {
            "job_id": job_id,
            "status": "failed",
            "candidate_id": None,
            "error": str(exc),
            "latency_ms": None,
        }

    logger.info(
        f"[{job_id}] Pipeline finished — "
        f"status={final_state.get('status')} | "
        f"candidate_id={final_state.get('candidate_id')} | "
        f"latency={final_state.get('latency_ms')}ms"
    )

    return {
        "job_id": job_id,
        "status": final_state.get("status"),
        "candidate_id": final_state.get("candidate_id"),
        "latency_ms": final_state.get("latency_ms"),
    }
