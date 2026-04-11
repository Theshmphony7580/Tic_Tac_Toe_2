from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_pool, close_pool
from app.routers import signup, signin, session, verification, google


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[auth-service] Starting...")
    await init_pool()
    yield
    await close_pool()
    print("[auth-service] Shut down.")


app = FastAPI(
    title="Auth Service",
    description="Authentication & session management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Auth Service is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Mount routers — all routes prefixed with /auth
app.include_router(signup.router, prefix="/auth", tags=["Signup"])
app.include_router(signin.router, prefix="/auth", tags=["Signin"])
app.include_router(session.router, prefix="/auth", tags=["Session"])
app.include_router(verification.router, prefix="/auth", tags=["Verification"])
app.include_router(google.router, prefix="/auth", tags=["Google OAuth"])
