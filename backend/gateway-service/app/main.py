from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Routers (we'll create these next)
from routers import parse, match, candidates, skills

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API Gateway starting...")
    # TODO: Initialize DB
    yield
    print("API Gateway shutting down...")

app = FastAPI(
    title="TalentIntel API Gateway",
    description="API Gateway for Resume Parsing, Skill Matching & Talent Intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "TalentIntel API Gateway is running",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(parse.router, prefix="/api/v1", tags=["Parse"])
app.include_router(match.router, prefix="/api/v1", tags=["Match"])
app.include_router(candidates.router, prefix="/api/v1", tags=["Candidates"])
app.include_router(skills.router, prefix="/api/v1", tags=["Skills"])