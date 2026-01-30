"""Main FastAPI application."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limit import RateLimitMiddleware, SimpleRateLimitMiddleware
from app.core.config import settings

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title="Leads Data Warehouse API",
    description="API for managing companies and contacts",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests with method, path, and processing time."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {process_time:.4f}s"
    )
    return response


# Rate limiting middleware
# Use Redis-based middleware in production, simple in-memory for development
if settings.RATE_LIMIT_ENABLED:
    try:
        app.add_middleware(RateLimitMiddleware)
        logger.info("Rate limiting enabled with Redis backend")
    except Exception as e:
        logger.warning(
            f"Failed to initialize Redis rate limiter, using in-memory: {e}"
        )
        app.add_middleware(SimpleRateLimitMiddleware)
        logger.info("Rate limiting enabled with in-memory backend")


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health/live")
async def liveness():
    """Liveness health check endpoint."""
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness():
    """Readiness health check endpoint with database connection."""
    from app.db.session import async_session_maker
    from sqlalchemy import text

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return {"status": "error", "database": "disconnected"}
