import logging
from fastapi import APIRouter, HTTPException
from app.schemas import MatchRequest, MatchResult
from app.matcher import run_match

logger = logging.getLogger(__name__)
router = APIRouter(tags=["matching"])

@router.post("/match", response_model=MatchResult, summary="Match candidates to a Job Description")
async def match_candidates(request: MatchRequest) -> MatchResult:
    """
    Embeds the job description, queries pgvector for top-K candidates,
    computes composite scores, and returns gap analysis.
    """
    try:
        result = await run_match(request)
        logger.info(
            f"Match completed: {len(result.results)} candidates returned "
            f"out of {result.total_candidates_scanned} scanned "
            f"in {result.processing_time_ms}ms"
        )
        return result
    except RuntimeError as e:
        logger.error(f"Service not ready: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during matching: {e}")
        raise HTTPException(status_code=500, detail="Internal matching error")
