import time
import logging
import httpx
from fastapi import APIRouter, HTTPException
import groq

from app.schemas import ParseRequest, ParseResponse
from app.config import get_settings
from app.parsers.pdf_parser import parse_pdf
from app.parsers.docx_parser import parse_docx
from app.parsers.txt_parser import parse_txt
from app.extraction import extract_from_text

router = APIRouter(tags=["parsing"])
logger = logging.getLogger(__name__)
settings = get_settings()

@router.post("/parse", response_model=ParseResponse)
async def parse_resume(request: ParseRequest) -> ParseResponse:
    start_time = time.time()
    
    try:
        # Step A: Download the file
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(request.file_url, timeout=15.0)
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="File not found at URL")
                file_bytes = response.content
            except httpx.RequestError as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch file: {str(e)}")

        # Check file size
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_file_size_mb}MB limit")

        # Step B: Convert file to text
        try:
            match request.file_type:
                case "pdf":
                    raw_text = parse_pdf(file_bytes)
                case "docx":
                    raw_text = parse_docx(file_bytes)
                case "txt":
                    raw_text = parse_txt(file_bytes)
                case _:
                    raise HTTPException(status_code=422, detail="Unsupported file type")
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
            candidate_id=request.candidate_id,
            data=parsed,
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in parse_resume: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "service": settings.service_name, 
        "model": settings.groq_model
    }
