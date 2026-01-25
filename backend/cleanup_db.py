"""Cleanup script to drop existing lead_status ENUM type from failed migration.

WARNING: This script is for DEVELOPMENT/TESTING environments only.
It will DROP ALL TABLES in the database.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine


async def cleanup() -> None:
    """Drop the lead_status ENUM type that already exists."""
    # Safety check: Only run in development
    env = os.getenv("ENV", "").lower()
    if env not in ("dev", "development", "test"):
        print(f"ERROR: Cleanup script can only run in development environment. Current ENV={env}")
        sys.exit(1)

    print("=" * 60)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 60)
    print("This will DROP ALL TABLES in the database.")
    print("Database: neondb (Neon PostgreSQL)")
    print()

    # Require confirmation
    response = input("Type 'yes' to continue: ")
    if response.lower() != "yes":
        print("Cleanup cancelled.")
        sys.exit(0)

    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            # Drop tables and ENUM
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS contacts CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS companies CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS lead_status CASCADE"))

        print("✅ Cleanup complete: All tables and types dropped")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(cleanup())
