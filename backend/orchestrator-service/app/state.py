from typing import TypedDict, Optional


class ResumeProcessingState(TypedDict):
    """
    The shared state dictionary that passes through every LangGraph node.
    Each node reads its required inputs and writes its outputs back into this dict.
    LangGraph merges the partial dict returned by each node into the running state.
    """

    # ── INPUT (populated at graph entry point) ─────────────────────────────
    job_id: str         # UUID string matching the batch_jobs table row
    file_url: str       # Absolute local path to the uploaded resume file
    file_type: str      # "pdf" | "docx" | "txt"

    # ── AFTER PARSE NODE ───────────────────────────────────────────────────
    parsed_resume: Optional[dict]   # Full ParseResponse JSON { success, data: ParsedCandidate }
    raw_skills: Optional[list]      # Shortcut: parsed_resume["data"]["raw_skills"]
    parse_error: Optional[str]      # Error message if parsing failed; None on success
    parse_retries: int              # How many parse attempts have been made

    # ── AFTER NORMALIZE NODE ───────────────────────────────────────────────
    normalized_skills: Optional[list]   # List of NormalizedSkill dicts from Normalizer
    normalization_error: Optional[str]  # Error message if normalization failed; None on success
    normalize_retries: int              # How many normalization attempts have been made

    # ── AFTER STORE NODE ───────────────────────────────────────────────────
    candidate_id: Optional[str]   # UUID of the inserted candidates table row
    embedding_stored: bool         # True if embedding vector was saved successfully
    store_error: Optional[str]     # Error message if DB store failed; None on success

    # ── PIPELINE METADATA ──────────────────────────────────────────────────
    status: str             # queued | parsing | normalizing | storing | complete | failed
    start_time: float       # Unix timestamp when the task began
    end_time: Optional[float]
    latency_ms: Optional[int]
