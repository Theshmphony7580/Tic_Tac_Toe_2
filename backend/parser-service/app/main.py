import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.parse import router as parse_router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info("Parser Service starting up...")
    
    if not settings.groq_api_key or "your_" in settings.groq_api_key:
        logger.error("GROQ_API_KEY is not properly configured!")
        
    logger.info(f"Using Groq model: {settings.groq_model}")
    logger.info(f"Max file size: {settings.max_file_size_mb}MB")
    
    yield
    
    # Shutdown
    logger.info("Parser Service shutting down...")

app = FastAPI(
    title="TalentIntel Parser Service",
    description="Resume parsing agent — converts PDF/DOCX/TXT to structured JSON using Groq LLM",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(parse_router, prefix="/internal")
