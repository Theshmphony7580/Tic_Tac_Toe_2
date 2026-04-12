"""run_orchestrator_pipeline.py — End-to-end orchestrator pipeline runner.

This script invokes the orchestrator LangGraph pipeline directly.
It exercises Parser and Normalizer through the orchestrator nodes, then stores
results in the database by calling the same pipeline used by Celery workers.

Usage:
    cd backend/orchestrator-service
    python run_orchestrator_pipeline.py --file-url path/to/resume.pdf --file-type pdf
"""

import argparse
import asyncio
import json
import time
import uuid
from pathlib import Path

from app.graph import resume_graph
from app.state import ResumeProcessingState


def build_initial_state(job_id: str, file_url: str, file_type: str) -> ResumeProcessingState:
    return {
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


async def run_pipeline(initial_state: ResumeProcessingState) -> ResumeProcessingState:
    return await resume_graph.ainvoke(initial_state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the orchestrator pipeline end to end through Parser and Normalizer."
    )
    parser.add_argument(
        "--file-url",
        required=True,
        nargs="+",
        help="Local resume file path. Multiple tokens are joined with spaces, so quoting is optional.",
    )
    parser.add_argument(
        "--file-type",
        choices=["pdf", "docx", "txt"],
        default="pdf",
        help="Resume file type",
    )
    parser.add_argument(
        "--job-id",
        help="Optional job UUID. If omitted, a random UUID is generated.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the final pipeline state as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    file_path = Path(" ".join(args.file_url))

    if not file_path.exists():
        print(f"ERROR: resume file not found: {file_path}")
        return 2

    job_id = args.job_id or str(uuid.uuid4())
    initial_state = build_initial_state(job_id, str(file_path.resolve()), args.file_type)

    print(f"Starting orchestrator pipeline for job_id={job_id}")
    print(f"  file_url={initial_state['file_url']}")
    print(f"  file_type={initial_state['file_type']}")

    final_state = asyncio.run(run_pipeline(initial_state))

    print("\nPipeline finished")
    print(f"  status: {final_state.get('status')}")
    print(f"  candidate_id: {final_state.get('candidate_id')}")
    print(f"  latency_ms: {final_state.get('latency_ms')}")
    if final_state.get("parse_error"):
        print(f"  parse_error: {final_state.get('parse_error')}")
    if final_state.get("normalization_error"):
        print(f"  normalization_error: {final_state.get('normalization_error')}")
    if final_state.get("store_error"):
        print(f"  store_error: {final_state.get('store_error')}")

    if args.print_json:
        print("\nFinal state JSON:")
        print(json.dumps(final_state, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
