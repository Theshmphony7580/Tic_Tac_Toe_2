from fastapi import APIRouter

router = APIRouter()

@router.get("/candidates/{candidate_id}/skills")
async def get_candidate_skills(candidate_id: str):
    return {"candidate_id": candidate_id, "skills": []}