"""Test database migrations."""

import pytest
from sqlalchemy import text
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_migration_creates_enum_type():
    """Test that lead_status ENUM type is created."""
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_type WHERE typname = 'lead_status'")
            )
            assert result.fetchone() is not None, "lead_status ENUM type should exist"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_creates_all_tables():
    """Test that all required tables are created."""
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('companies', 'contacts', 'users', 'alembic_version')
            """))
            tables = {row[0] for row in result.fetchall()}
            assert tables == {'companies', 'contacts', 'users', 'alembic_version'}
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_migration_creates_indexes():
    """Test that indexes are created."""
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT count(*)
                FROM pg_indexes
                WHERE schemaname = 'public'
            """))
            count = result.fetchone()[0]
            assert count >= 20, f"Expected at least 20 indexes, got {count}"
    finally:
        await engine.dispose()
