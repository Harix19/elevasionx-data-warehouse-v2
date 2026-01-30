"""Tests for rate limiting middleware.

Tests that rate limiting is enforced correctly for both
JWT and API key authentication.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey, AccessLevel
from app.models.user import User
from app.core.api_key import generate_api_key


class TestRateLimiting:
    """Test rate limiting enforcement."""

    @pytest.mark.skip(reason="Redis not available in test environment")
    async def test_rate_limit_headers_present(
        self, async_client: AsyncClient
    ):
        """Test that rate limit headers are present in responses."""
        response = await async_client.get("/api/v1/companies/")
        
        assert response.status_code == 200
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify values are reasonable
        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        
    @pytest.mark.skip(reason="Redis not available in test environment")
    async def test_rate_limit_exceeded(
        self, db: AsyncSession, test_user: User
    ):
        """Test that rate limit is enforced."""
        # Create API key with very low rate limit
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Low Limit Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=2,  # Very low limit for testing
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
            # First two requests should succeed
            response1 = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            assert response1.status_code == 200
            
            response2 = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            assert response2.status_code == 200
            
            # Third request should be rate limited
            response3 = await client.get(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key}
            )
            assert response3.status_code == 429
            
            # Should have Retry-After header
            assert "Retry-After" in response3.headers


class TestRateLimitConfiguration:
    """Test rate limit configuration per API key."""

    async def test_default_rate_limit(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test that default rate limit is applied."""
        # API key should have default rate limit (1000)
        assert test_api_key_read.rate_limit == 1000
        
    async def test_custom_rate_limit(
        self, db: AsyncSession, test_user: User
    ):
        """Test that custom rate limit is stored correctly."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Custom Limit Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.READ,
            rate_limit=500,  # Custom limit
            user_id=test_user.id,
            is_active=True,
        )
        db.add(api_key)
        await db.commit()
        
        assert api_key.rate_limit == 500
