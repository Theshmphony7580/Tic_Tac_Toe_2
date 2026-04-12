"""
test_graph.py — Unit tests for the LangGraph orchestrator pipeline.

Tests use unittest.mock to stub out:
- HTTP calls to Parser and Normalizer (httpx.AsyncClient.post)
- asyncpg.connect (DB operations)
- embed_text (embedding generation)

No live services, Redis, or database are needed to run these tests.

Run with:
    cd f:\\Tic_Tac_Toe_2\\backend\\orchestrator-service
    pip install pytest pytest-asyncio
    pytest tests/test_graph.py -v
"""

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.graph import build_graph
from app.state import ResumeProcessingState

# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_JOB_ID = str(uuid.uuid4())
FAKE_FILE_URL = "f:/test_resumes/fake_resume.pdf"
FAKE_CANDIDATE_ID = str(uuid.uuid4())

PARSE_SUCCESS_RESPONSE = {
    "success": True,
    "data": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-0100",
        "location": "New York, NY",
        "linkedin_url": None,
        "portfolio_url": None,
        "summary": "Experienced software engineer",
        "total_experience_years": 5.0,
        "work_experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "raw_skills": ["Python", "Docker", "Kubernetes"],
        "languages": ["English"],
        "raw_text": "Jane Doe...",
        "confidence_score": 0.95,
        "warnings": [],
    },
    "processing_time_ms": 1200,
}

NORMALIZE_SUCCESS_RESPONSE = {
    "success": True,
    "normalized_skills": [
        {"raw_name": "Python", "canonical_name": "Python", "category": "Programming Languages", "confidence": 1.0, "matched_via": "fuzzy"},
        {"raw_name": "Docker", "canonical_name": "Docker", "category": "DevOps", "confidence": 0.98, "matched_via": "fuzzy"},
        {"raw_name": "Kubernetes", "canonical_name": "Kubernetes", "category": "DevOps", "confidence": 0.97, "matched_via": "fuzzy"},
    ],
    "processing_time_ms": 150,
}


def _make_initial_state() -> ResumeProcessingState:
    return {
        "job_id": FAKE_JOB_ID,
        "file_url": FAKE_FILE_URL,
        "file_type": "pdf",
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


def _make_http_response(status_code: int, json_data: dict) -> MagicMock:
    """Create a mock httpx response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    return mock_resp


# ── Test 1: Happy Path ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_happy_path():
    """
    All nodes succeed:
    - Parser returns a valid ParsedCandidate
    - Normalizer returns normalized skills
    - DB insert returns a candidate UUID
    Expected: status == "complete", candidate_id is set
    """
    graph = build_graph()

    # Mock file open (needed by call_parser)
    mock_file_content = b"%PDF fake resume content"

    # Mock httpx POST for Parser
    parser_mock_resp = _make_http_response(200, PARSE_SUCCESS_RESPONSE)
    norm_mock_resp = _make_http_response(200, NORMALIZE_SUCCESS_RESPONSE)

    # Mock asyncpg connection
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value={"id": FAKE_CANDIDATE_ID})

    call_count = {"n": 0}

    async def mock_post(url, **kwargs):
        call_count["n"] += 1
        if "parse" in url:
            return parser_mock_resp
        if "normalize" in url:
            return norm_mock_resp
        raise ValueError(f"Unexpected URL in mock: {url}")

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client.post = mock_post

    with (
        patch("builtins.open", MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_file_content))),
            __exit__=MagicMock(return_value=False),
        ))),
        patch("app.nodes.httpx.AsyncClient", return_value=mock_async_client),
        patch("app.nodes.asyncpg.connect", AsyncMock(return_value=mock_conn)),
        patch("app.nodes.insert_candidate", AsyncMock(return_value=FAKE_CANDIDATE_ID)),
        patch("app.nodes.update_job_status", AsyncMock()),
        patch("app.nodes.embed_text", return_value=[0.1] * 384),
    ):
        final_state = await graph.ainvoke(_make_initial_state())

    assert final_state["status"] == "complete", f"Expected 'complete', got '{final_state['status']}'"
    assert final_state["candidate_id"] == FAKE_CANDIDATE_ID
    assert final_state["embedding_stored"] is True
    assert final_state["parse_error"] is None
    assert final_state["normalization_error"] is None


# ── Test 2: Parser Fails (Max Retries) ────────────────────────────────────────

@pytest.mark.asyncio
async def test_parser_fails_max_retries():
    """
    Parser always throws a connection error.
    After MAX_RETRIES (3) attempts, the graph should route to handle_error.
    Expected: status == "failed", candidate_id is None
    """
    graph = build_graph()

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client.post = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused to parser")
    )

    with (
        patch("builtins.open", MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock()),
            __exit__=MagicMock(return_value=False),
        ))),
        patch("app.nodes.httpx.AsyncClient", return_value=mock_async_client),
        patch("app.nodes.asyncpg.connect", AsyncMock(return_value=AsyncMock(
            execute=AsyncMock(), close=AsyncMock(),
            __aenter__=AsyncMock(), __aexit__=AsyncMock(return_value=False),
        ))),
        patch("app.nodes.update_job_status", AsyncMock()),
    ):
        final_state = await graph.ainvoke(_make_initial_state())

    assert final_state["status"] == "failed"
    assert final_state["candidate_id"] is None
    assert final_state["parse_retries"] >= 3


# ── Test 3: Normalizer Fails — Graceful Degradation ──────────────────────────

@pytest.mark.asyncio
async def test_normalizer_fails_graceful_store():
    """
    Parser succeeds, but normalizer always fails.
    After MAX_RETRIES normalization attempts, route_after_normalize
    should trigger graceful degradation: store with raw skills.
    Expected: status == "complete", candidate_id is set (stored with raw skills)
    """
    import httpx as httpx_module

    graph = build_graph()

    parser_mock_resp = _make_http_response(200, PARSE_SUCCESS_RESPONSE)
    norm_error_resp = _make_http_response(500, {"detail": "Normalizer internal error"})

    call_count = {"n": 0}

    async def mock_post(url, **kwargs):
        if "parse" in url:
            return parser_mock_resp
        # Normalizer always fails with HTTP 500
        return norm_error_resp

    mock_async_client = AsyncMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client.post = mock_post

    with (
        patch("builtins.open", MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock()),
            __exit__=MagicMock(return_value=False),
        ))),
        patch("app.nodes.httpx.AsyncClient", return_value=mock_async_client),
        patch("app.nodes.asyncpg.connect", AsyncMock(return_value=AsyncMock(
            execute=AsyncMock(), close=AsyncMock(),
        ))),
        patch("app.nodes.insert_candidate", AsyncMock(return_value=FAKE_CANDIDATE_ID)),
        patch("app.nodes.update_job_status", AsyncMock()),
        patch("app.nodes.embed_text", return_value=[0.1] * 384),
    ):
        final_state = await graph.ainvoke(_make_initial_state())

    # Even though normalization failed, the candidate should still be stored
    assert final_state["status"] == "complete", (
        f"Expected 'complete' (graceful degradation), got '{final_state['status']}'"
    )
    assert final_state["candidate_id"] == FAKE_CANDIDATE_ID
    assert final_state["normalization_error"] is not None  # Error was recorded
