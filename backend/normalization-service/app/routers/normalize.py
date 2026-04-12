import time
import logging
import traceback
from fastapi import APIRouter, HTTPException
from app.schemas import NormalizeRequest, NormalizeResponse
from app.database import get_taxonomy
from app.fuzzy_matcher import normalize_skills_via_fuzzy
from app.llm_fallback import resolve_unknown_skills_via_llm

router = APIRouter(tags=["normalization"])
logger = logging.getLogger(__name__)

# @router.post("/normalize", response_model=NormalizeResponse)
# # async def normalize_skills(request: NormalizeRequest) -> NormalizeResponse:
# #     start_time = time.time()
    
#     if not request.raw_skills:
#         return NormalizeResponse(
#             success=True,
#             candidate_id=request.candidate_id,
#             normalized_skills=[],
#             processing_time_ms=0
#         )

#     try:
#         # 1. Fetch Taxonomy (from Redis cache or Postgres)
#         taxonomy = await get_taxonomy()

#         # 2. Fastest Pass: RapidFuzz Matching
#         resolved, unresolved = normalize_skills_via_fuzzy(request.raw_skills, taxonomy)
        
#         # 3. Fallback Pass: Groq LLM
#         if unresolved:
#             logger.info(f"Fuzzy Matcher missed {len(unresolved)} skills. Sending to LLM fallback.")
#             llm_resolved = resolve_unknown_skills_via_llm(unresolved, taxonomy)
#             resolved.extend(llm_resolved)

#         processing_time_ms = int((time.time() - start_time) * 1000)
        
#         return NormalizeResponse(
#             success=True,
#             candidate_id=request.candidate_id,
#             normalized_skills=resolved,
#             processing_time_ms=processing_time_ms
#         )

#     except Exception as e:
#         logger.error(f"Unhandled error in normalize_skills: {e}")
#         tb = traceback.format_exc()
#         print("NORMALIZER ERROR:\n", tb)

#         return {
#             "error": str(e),
#             "trace": tb
#         }

from fastapi import APIRouter

router = APIRouter()

@router.post("/normalize")
async def normalize_skills(data: dict):

    start = time.time()

    raw_skills = data.get("raw_skills", [])

    if not raw_skills:
        return {
            "success": False,
            "normalized_skills": [],
            "processing_time_ms": 0
        }

    # TEMP: simple normalization (basic cleanup)
    normalized = [skill.strip().title() for skill in raw_skills]

    return {
        "success": True,
        "raw_skills" : raw_skills,
        "normalized_skills": normalized,
        "processing_time_ms": int((time.time() - start) * 1000)
    }

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "talentintel-normalizer"}
