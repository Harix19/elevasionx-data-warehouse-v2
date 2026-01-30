"""Tests for API key authentication.

Tests that API keys work correctly for authentication and
that different access levels are enforced properly.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey, AccessLevel
from app.models.user import User
from app.core.api_key import generate_api_key, verify_api_key


class TestAPIKeyValidation:
    """Test API key validation logic."""

    async def test_generate_api_key_format(self):
        """Test that generated API keys have correct format."""
        full_key, prefix, key_hash = generate_api_key()
        
        assert full_key.startswith("ldwsk-")
        assert prefix.startswith("ldwsk-")
        assert len(prefix) == 12
        assert len(full_key) > 12
        assert key_hash.startswith("$2")  # bcrypt hash
        
    async def test_verify_api_key_success(self):
        """Test that valid API keys are verified correctly."""
        full_key, prefix, key_hash = generate_api_key()
        
        assert verify_api_key(full_key, key_hash) is True
        
    async def test_verify_api_key_failure(self):
        """Test that invalid API keys are rejected."""
        full_key, prefix, key_hash = generate_api_key()
        
        assert verify_api_key("invalid-key", key_hash) is False
        assert verify_api_key(full_key, "$2b$04$invalidhash") is False


class TestAPIKeyAuthentication:
    """Test API key authentication via API endpoints."""

    async def test_auth_with_valid_api_key(
        self, db: AsyncSession, test_user: User
    ):
        """Test that valid API key allows access."""
        # Create API key with write access
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Test Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.WRITE,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        
        # Make request with API key
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            
        assert response.status_code == 200
        
    async def test_auth_with_invalid_api_key(self):
        """Test that invalid API key is rejected."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": "ldwsk-invalidkey123"}
            )
            
        assert response.status_code == 401
        
    async def test_auth_with_deactivated_api_key(
        self, db: AsyncSession, test_user: User
    ):
        """Test that deactivated API key is rejected."""
        # Create deactivated API key
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Inactive Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=False,  # Deactivated
        )
        db.add(api_key)
        await db.commit()
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            
        assert response.status_code == 401


class TestAPIKeyAccessLevels:
    """Test that different access levels are enforced."""

    async def test_read_key_can_read(
        self, db: AsyncSession, test_user: User
    ):
        """Test that read key can access GET endpoints."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Read Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            
        assert response.status_code == 200
        
    async def test_read_key_cannot_write(
        self, db: AsyncSession, test_user: User
    ):
        """Test that read key cannot access write endpoints."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Read Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key},
                json={
                    "name": "Test Company",
                    "website": "https://example.com"
                }
            )
            
        assert response.status_code == 403
        
    async def test_write_key_can_read_and_write(
        self, db: AsyncSession, test_user: User
    ):
        """Test that write key can access both read and write endpoints."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Write Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.WRITE,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Test read
            response = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200
            
            # Test write
            response = await client.post(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key},
                json={
                    "name": "Test Company",
                    "website": "https://example.com"
                }
            )
            assert response.status_code == 201


class TestAPIKeyTracking:
    """Test API key usage tracking."""

    async def test_last_used_updated(
        self, db: AsyncSession, test_user: User
    ):
        """Test that last_used_at is updated on API key use."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Track Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=1000,
            user_id=test_user.id,
            is_active=True,
            last_used_at=None,
        )
        db.add(api_key)
        await db.commit()
        
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
        
        # Refresh and check
        await db.refresh(api_key)
        assert api_key.last_used_at is not None
