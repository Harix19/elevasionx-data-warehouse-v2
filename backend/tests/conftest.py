
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
from app.models.api_key import APIKey, AccessLevel
from app.core.api_key import generate_api_key, verify_api_key

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


@pytest.fixture(scope="function")
async def test_api_key_read(db, test_user):
    """Create a read-only API key for testing."""
    full_key, key_prefix, key_hash = generate_api_key()
    
    api_key = APIKey(
        name="Test Read Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        access_level=AccessLevel.READ,
        rate_limit=1000,
        user_id=test_user.id,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # Return both the API key object and the full key (for auth headers)
    api_key.full_key = full_key
    return api_key


@pytest.fixture(scope="function")
async def test_api_key_write(db, test_user):
    """Create a write API key for testing."""
    full_key, key_prefix, key_hash = generate_api_key()
    
    api_key = APIKey(
        name="Test Write Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        access_level=AccessLevel.WRITE,
        rate_limit=1000,
        user_id=test_user.id,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    api_key.full_key = full_key
    return api_key


@pytest.fixture(scope="function")
async def test_api_key_admin(db, test_user):
    """Create an admin API key for testing."""
    full_key, key_prefix, key_hash = generate_api_key()
    
    api_key = APIKey(
        name="Test Admin Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        access_level=AccessLevel.ADMIN,
        rate_limit=1000,
        user_id=test_user.id,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    api_key.full_key = full_key
    return api_key


@pytest.fixture(scope="function")
async def client_with_api_key(db, test_user, test_api_key_admin):
    """Create a client that uses API key authentication."""
    from app.api.deps import get_db

    # Create an async generator that yields our test session
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # Don't override get_current_user - let it use real API key auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        # Store API key for tests to use
        client.api_key = test_api_key_admin.full_key
        yield client

    app.dependency_overrides.clear()
