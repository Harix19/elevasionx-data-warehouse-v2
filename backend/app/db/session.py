"""Database session and engine configuration."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Neon serverless REQUIRES NullPool - NO local pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # MANDATORY for Neon serverless
    echo=settings.DEBUG,
    # Disable statement caching to avoid InvalidCachedStatementError
    # when schema changes occur (e.g., during tests or migrations)
    connect_args={"statement_cache_size": 0},
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
