
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.core.config import settings
# Import models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.company import Company
from app.models.contact import Contact

# Use a test database URL
TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio for anyio tests."""
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={"statement_cache_size": 0},
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_user(db):
    """Create a test user for authenticated requests."""
    from app.core.security import hash_password
    from uuid import uuid4

    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def db(engine):
    """Create a database session with transaction rollback for test isolation.

    Uses SAVEPOINT pattern - no schema changes, just rollback after each test.
    Tables must already exist in the database (via alembic migrations).
    """
    async with engine.connect() as conn:
        # Start outer transaction
        trans = await conn.begin()
        # Create nested savepoint for rollback
        await conn.begin_nested()

        # Create session bound to this connection
        session = AsyncSession(bind=conn, expire_on_commit=False)

        yield session

        # Rollback everything - no schema changes needed
        await session.close()
        await trans.rollback()


@pytest.fixture(scope="function")
async def async_client(db, test_user):
    """Create an async test client for the FastAPI app with auth bypass."""
    from app.api.deps import get_db, get_current_user

    # Create an async generator that yields our test session
    async def override_get_db():
        yield db

    # Bypass authentication with mock user
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
