"""
MediSync AI — FastAPI Application Entry Point
Configures middleware, registers routers, and handles lifespan events.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, admin, doctor, patient, queue
from app.core.config import settings
from app.core.database import engine
from app.core.redis_client import close_redis, get_redis
from app.models.models import Base


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan:
    - Startup: initialise database tables (dev mode), warm up Redis.
    - Shutdown: gracefully close Redis connection.
    """
    # Create all tables (useful for development; use Alembic in production)
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Warm up Redis
    await get_redis()

    yield

    # Teardown
    await close_redis()
    await engine.dispose()


# ── FastAPI application ────────────────────────────────────────────────────────

app = FastAPI(
    title="MediSync AI",
    description=(
        "Integrated Hospital Intelligence Platform — "
        "queue management, real-time monitoring, multi-modal AI, and EWS."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(doctor.router, prefix=API_PREFIX)
app.include_router(patient.router, prefix=API_PREFIX)
app.include_router(queue.router, prefix=API_PREFIX)


# ── Root & Health endpoints ───────────────────────────────────────────────────

@app.get("/", tags=["info"])
async def root() -> dict:
    """
    Root endpoint — returns API info and links to interactive docs.
    Visiting http://localhost:8000 in a browser will show this JSON.
    For the interactive Swagger UI go to http://localhost:8000/docs
    """
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": "/api",
    }


@app.get("/health", tags=["info"])
async def health_check() -> dict:
    """Simple liveness probe used by Docker and load balancers."""
    return {"status": "healthy", "app": settings.APP_NAME, "env": settings.APP_ENV}
