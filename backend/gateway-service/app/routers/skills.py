from fastapi import APIRouter

router = APIRouter()

@router.get("/skills/taxonomy")
async def get_skills():
    return {"skills": []}