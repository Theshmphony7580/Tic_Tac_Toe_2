import os
import httpx
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()

import os
# Get project root (backend folder)
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL")

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):

    try:
        # Save file locally
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        #  Send file path
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ORCHESTRATOR_URL,
                json={
                    "file_url": file_path,
                    "file_type": "pdf"
                }
            )

        return response.json()

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(e)}
        )