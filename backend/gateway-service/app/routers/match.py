from fastapi import APIRouter

router = APIRouter()

@router.post("/match")
async def match_candidates():
    return {"message": "Match endpoint working"}