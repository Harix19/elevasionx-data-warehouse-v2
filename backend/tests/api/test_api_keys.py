"""Tests for API key management endpoints.

Tests CRUD operations for API keys including creation, listing,
retrieval, updating, deletion, and regeneration.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey, AccessLevel
from app.models.user import User
from app.core.api_key import generate_api_key


class TestAPICreate:
    """Test API key creation endpoint."""

    async def test_create_api_key_success(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test successful API key creation."""
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test Production Key",
                "access_level": "write",
                "rate_limit": 500
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Test Production Key"
        assert data["access_level"] == "write"
        assert data["rate_limit"] == 500
        assert data["is_active"] is True
        assert data["key_prefix"].startswith("ldwsk-")
        assert "key" in data  # Full key only returned on creation
        assert data["key"].startswith("ldwsk-")
        
    async def test_create_api_key_defaults(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test API key creation with default values."""
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={"name": "Default Key"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["access_level"] == "read"  # Default
        assert data["rate_limit"] == 1000  # Default
        
    async def test_create_api_key_invalid_rate_limit(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test API key creation with invalid rate limit."""
        response = await async_client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Invalid Key",
                "rate_limit": 50000  # Too high
            }
        )
        
        assert response.status_code == 422
        
    async def test_create_api_key_unauthorized(
        self, async_client: AsyncClient
    ):
        """Test API key creation without auth fails."""
        # Clear auth override temporarily
        from app.main import app
        from app.api.deps import get_current_user
        
        original_override = app.dependency_overrides.get(get_current_user)
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        try:
            response = await async_client.post(
                "/api/v1/api-keys/",
                json={"name": "Unauthorized Key"}
            )
            assert response.status_code == 401
        finally:
            # Restore override
            if original_override:
                app.dependency_overrides[get_current_user] = original_override


class TestAPIList:
    """Test API key listing endpoint."""

    async def test_list_api_keys(
        self, async_client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test listing API keys."""
        # Create a few API keys
        for i in range(3):
            full_key, prefix, hash_val = generate_api_key()
            api_key = APIKey(
                name=f"Key {i}",
                key_prefix=prefix,
                key_hash=hash_val,
                access_level=AccessLevel.READ,
                user_id=test_user.id,
                is_active=True,
            )
            db.add(api_key)
        await db.commit()
        
        response = await async_client.get("/api/v1/api-keys/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 3
        assert len(data["items"]) >= 3
        assert "key" not in data["items"][0]  # Keys are masked
        
    async def test_list_api_keys_pagination(
        self, async_client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test API key listing with pagination."""
        # Create multiple API keys
        for i in range(5):
            full_key, prefix, hash_val = generate_api_key()
            api_key = APIKey(
                name=f"Key {i}",
                key_prefix=prefix,
                key_hash=hash_val,
                access_level=AccessLevel.READ,
                user_id=test_user.id,
                is_active=True,
            )
            db.add(api_key)
        await db.commit()
        
        response = await async_client.get("/api/v1/api-keys/?limit=2&skip=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["total"] == 5
        
    async def test_list_api_keys_filter_active(
        self, async_client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test filtering API keys by active status."""
        # Create active and inactive keys
        for i, active in enumerate([True, True, False]):
            full_key, prefix, hash_val = generate_api_key()
            api_key = APIKey(
                name=f"Key {i}",
                key_prefix=prefix,
                key_hash=hash_val,
                access_level=AccessLevel.READ,
                user_id=test_user.id,
                is_active=active,
            )
            db.add(api_key)
        await db.commit()
        
        response = await async_client.get("/api/v1/api-keys/?is_active=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return active keys
        assert all(item["is_active"] for item in data["items"])


class TestAPIGet:
    """Test API key retrieval endpoint."""

    async def test_get_api_key(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test retrieving a specific API key."""
        response = await async_client.get(
            f"/api/v1/api-keys/{test_api_key_read.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_api_key_read.id)
        assert data["name"] == test_api_key_read.name
        assert "key" not in data  # Key is masked
        
    async def test_get_api_key_not_found(
        self, async_client: AsyncClient
    ):
        """Test retrieving non-existent API key."""
        from uuid import uuid4
        
        response = await async_client.get(
            f"/api/v1/api-keys/{uuid4()}"
        )
        
        assert response.status_code == 404


class TestAPIUpdate:
    """Test API key update endpoint."""

    async def test_update_api_key_name(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test updating API key name."""
        response = await async_client.patch(
            f"/api/v1/api-keys/{test_api_key_read.id}",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Name"
        
    async def test_update_api_key_access_level(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test updating API key access level."""
        response = await async_client.patch(
            f"/api/v1/api-keys/{test_api_key_read.id}",
            json={"access_level": "write"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_level"] == "write"
        
    async def test_update_api_key_deactivate(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test deactivating API key."""
        response = await async_client.patch(
            f"/api/v1/api-keys/{test_api_key_read.id}",
            json={"is_active": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is False


class TestAPIDelete:
    """Test API key deletion endpoint."""

    async def test_delete_api_key(
        self, async_client: AsyncClient, test_api_key_read: APIKey, db: AsyncSession
    ):
        """Test soft deleting API key."""
        response = await async_client.delete(
            f"/api/v1/api-keys/{test_api_key_read.id}"
        )
        
        assert response.status_code == 204
        
        # Verify key is marked inactive
        await db.refresh(test_api_key_read)
        assert test_api_key_read.is_active is False
        
    async def test_delete_api_key_not_found(
        self, async_client: AsyncClient
    ):
        """Test deleting non-existent API key."""
        from uuid import uuid4
        
        response = await async_client.delete(
            f"/api/v1/api-keys/{uuid4()}"
        )
        
        assert response.status_code == 404


class TestAPIRegenerate:
    """Test API key regeneration endpoint."""

    async def test_regenerate_api_key(
        self, async_client: AsyncClient, test_api_key_read: APIKey
    ):
        """Test regenerating API key."""
        old_prefix = test_api_key_read.key_prefix
        
        response = await async_client.post(
            f"/api/v1/api-keys/{test_api_key_read.id}/regenerate"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["key_prefix"] != old_prefix  # New prefix
        assert "key" in data  # New key returned
        assert data["is_active"] is True  # Reactivated
        
    async def test_regenerate_inactive_api_key(
        self, async_client: AsyncClient, test_api_key_read: APIKey, db: AsyncSession
    ):
        """Test regenerating inactive API key reactivates it."""
        # Deactivate first
        test_api_key_read.is_active = False
        await db.commit()
        
        response = await async_client.post(
            f"/api/v1/api-keys/{test_api_key_read.id}/regenerate"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is True
