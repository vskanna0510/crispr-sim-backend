"""
CRISPR-Sim Backend
==================
FastAPI application entry point.

Run:
    cd crispr_sim/backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Interactive docs:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sequence import router as sequence_router
from api.crispr    import router as crispr_router
from api.analysis  import router as analysis_router
from api.chat      import router as chat_router
from api.advanced  import router as advanced_router
from utils.database import init_db

# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the SQLite database on startup."""
    init_db()
    yield


# ─── App factory ─────────────────────────────────────────────────────────────

app = FastAPI(
    lifespan=lifespan,
    title="CRISPR-Sim API",
    description=(
        "Interactive CRISPR-Cas9 gene-editing simulator. "
        "Provides endpoints for sequence input, PAM scanning, "
        "Cas9 cut simulation, NHEJ/HDR repair, translation, and mutation analysis."
    ),
    version="1.0.0",
    contact={"name": "CRISPR-Sim", "url": "https://github.com/crispr-sim"},
    license_info={"name": "MIT"},
)


# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Flutter app (and any local dev server) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(sequence_router)
app.include_router(crispr_router)
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(advanced_router)


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="API health check")
async def root():
    return {
        "status":  "ok",
        "app":     "CRISPR-Sim API",
        "version": "1.0.0",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health probe")
async def health():
    return {"status": "healthy", "database": "sqlite"}
