"""
CRISPR-Sim Backend
==================
FastAPI application entry point.

Run locally with Docker:
    docker compose up --build

Run without Docker:
    cd crispr_sim/backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sequence import router as sequence_router
from api.crispr import router as crispr_router
from api.analysis import router as analysis_router
from api.chat import router as chat_router
from api.advanced import router as advanced_router
from api.auth import router as auth_router
from api.history import router as history_router
from api.settings import router as settings_router
from core.config import get_settings
from utils.database import database_status, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise PostgreSQL schema and seed data on startup."""
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    lifespan=lifespan,
    title="CRISPR-Sim API",
    description=(
        "Interactive CRISPR-Cas9 gene-editing simulator with JWT auth and PostgreSQL persistence. "
        "Provides endpoints for sequence input, PAM scanning, "
        "Cas9 cut simulation, NHEJ/HDR repair, translation, and mutation analysis."
    ),
    version="2.0.0",
    contact={"name": "CRISPR-Sim", "url": "https://github.com/vskanna0510/crispr-sim-backend"},
    license_info={"name": "MIT"},
)

origins = settings.cors_origins if settings.cors_origins != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(history_router)
app.include_router(settings_router)
app.include_router(sequence_router)
app.include_router(crispr_router)
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(advanced_router)


@app.get("/", tags=["Health"], summary="API health check")
async def root():
    return {
        "status": "ok",
        "app": "CRISPR-Sim API",
        "version": "2.0.0",
        "docs": "/docs",
        "auth": "JWT Bearer — POST /auth/register, /auth/login",
    }


@app.get("/health", tags=["Health"], summary="Detailed health probe")
async def health():
    return {
        "status": "healthy",
        "database": database_status(),
        "auth_required": settings.require_auth,
    }
