import httpx
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    
    # Step 1: Upload file to storage (Supabase)
    
    # Step 2: Call orchestrator
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://orchestrator:8004/process",
            json={
                "file_url": "backend\data\resumes\resume.pdf",
                "file_type": "pdf"
            }
        )

    return response.json()