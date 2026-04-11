import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.match import router as match_router
from app.database import create_pool, close_pool
from app.embedder import load_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Matching Service starting up...")
    # 1. Load embedding model into memory (blocks until done, ~2-5s)
    load_model()
    # 2. Open DB connection pool
    await create_pool()
    logger.info("Matching Service ready.")
    yield
    # Shutdown
    logger.info("Matching Service shutting down...")
    await close_pool()

app = FastAPI(
    title="TalentIntel Matching Service",
    description="Semantic candidate matching using pgvector + sentence-transformers.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(match_router, prefix="/internal")
