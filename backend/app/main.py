"""Main FastAPI application."""

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

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

# IMPORTANT: CORS must be the LAST middleware added to run first
# This ensures CORS headers are added to all responses including errors

# GZip compression for responses > 1KB (add first - runs last)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting middleware (add second)
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

# Request logging middleware (add third)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests with structured timing and trace information."""
    start_time = time.time()

    # Generate or extract trace ID
    trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    response = await call_next(request)
    process_time = time.time() - start_time
    duration_ms = process_time * 1000

    # Structured logging
    logger.info(
        "Request completed",
        extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )

    # Add response headers for timing and tracing
    response.headers["X-Request-ID"] = trace_id
    response.headers["X-Response-Time"] = f"{duration_ms:.3f}"

    return response

# CORS configuration (add LAST so it runs FIRST on requests)
# This ensures preflight OPTIONS requests are handled before other middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Leads Data Warehouse API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health/ready",
        "api": "/api/v1"
    }


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
