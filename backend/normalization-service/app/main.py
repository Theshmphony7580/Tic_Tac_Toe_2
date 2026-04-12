import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.normalize import router as normalize_router
from app.database import init_redis, close_redis, get_taxonomy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Normalization Service starting up...")
    
    # Pre-warm Redis and Cache taxonomy
    # await init_redis()
    # try:
    #     await get_taxonomy()
    #     logger.info("Successfully primed the Redis taxonomy cache.")
    # except Exception as e:
    #     logger.error(f"Failed to pre-warm taxonomy cache: {e}")
        
    yield
    
    # Shutdown
    logger.info("Normalization Service shutting down...")
    # await close_redis()

app = FastAPI(
    title="TalentIntel Normalization Service",
    description="Maps raw extracted skills to official taxonomic categories utilizing RapidFuzz and LLM inference.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(normalize_router, prefix="/internal")
