import time
import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import groq

from app.schemas import ParseResponse
from app.config import get_settings
from app.parsers.pdf_parser import parse_pdf
from app.parsers.docx_parser import parse_docx
from app.parsers.txt_parser import parse_txt
from app.extraction import extract_from_text

router = APIRouter(tags=["parsing"])
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/parse", response_model=ParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    candidate_id: UUID | None = Form(None)
) -> ParseResponse:
    start_time = time.time()
    
    try:
        # Step A: Read the file instantly from the multipart payload
        file_bytes = await file.read()

        # Check file size
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_file_size_mb}MB limit")

        # Step B: Convert file to text based on filename extension
        filename = file.filename.lower() if file.filename else ""
        try:
            if filename.endswith(".pdf"):
                raw_text = parse_pdf(file_bytes)
            elif filename.endswith(".docx"):
                raw_text = parse_docx(file_bytes)
            elif filename.endswith(".txt"):
                raw_text = parse_txt(file_bytes)
            else:
                raise HTTPException(status_code=422, detail="Unsupported file extension. Use .pdf, .docx, or .txt")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Check if empty document
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Document appears to be empty after extraction")

        # Step C: Extract structured data via Groq
        try:
            parsed = extract_from_text(raw_text)
        except groq.RateLimitError:
            raise HTTPException(status_code=429, detail="LLM rate limit reached")
            
        # Step D & E: Return response
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ParseResponse(
            success=True,
            candidate_id=candidate_id,
            data=parsed,
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Unhandled error in parse_resume:\n{tb}")
        raise HTTPException(status_code=500, detail=f"Error: {type(e).__name__}: {str(e)}")

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "service": settings.service_name, 
        "model": settings.groq_model
    }
