"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.logging import configure_logging, get_logger

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
