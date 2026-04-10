from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    return {"message": "Parse endpoint working", "filename": file.filename}