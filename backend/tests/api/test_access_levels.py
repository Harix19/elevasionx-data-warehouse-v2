"""Tests for access level enforcement.

Tests that access levels (read/write/admin) are properly enforced
across all endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey, AccessLevel
from app.models.user import User
from app.models.company import Company
from app.models.contact import Contact
from app.core.api_key import generate_api_key


class TestReadAccess:
    """Test READ access level permissions."""

    async def test_read_can_access_companies_get(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key can GET companies."""
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
            
    async def test_read_can_access_contacts_get(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key can GET contacts."""
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
                "/api/v1/contacts/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200
            
    async def test_read_can_access_search(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key can use search."""
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
                "/api/v1/search?q=test",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200
            
    async def test_read_can_access_export(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key can export data."""
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
                "/api/v1/export/companies",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200
            
    async def test_read_can_access_stats(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key can view stats."""
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
                "/api/v1/stats/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200


class TestWriteAccess:
    """Test WRITE access level permissions."""

    async def test_write_can_create_company(
        self, db: AsyncSession, test_user: User
    ):
        """Test write key can create companies."""
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
            response = await client.post(
                "/api/v1/companies/",
                headers={"X-API-Key": full_key},
                json={
                    "name": "New Company",
                    "website": "https://example.com"
                }
            )
            assert response.status_code == 201
            
    async def test_write_can_update_company(
        self, db: AsyncSession, test_user: User
    ):
        """Test write key can update companies."""
        # Create a company first
        company = Company(name="Test Company", website="https://test.com")
        db.add(company)
        await db.commit()
        
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
            response = await client.patch(
                f"/api/v1/companies/{company.id}",
                headers={"X-API-Key": full_key},
                json={"name": "Updated Name"}
            )
            assert response.status_code == 200
            
    async def test_write_can_delete_company(
        self, db: AsyncSession, test_user: User
    ):
        """Test write key can delete companies."""
        # Create a company first
        company = Company(name="Test Company", website="https://test.com")
        db.add(company)
        await db.commit()
        
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
            response = await client.delete(
                f"/api/v1/companies/{company.id}",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 204
            
    async def test_write_can_bulk_import(
        self, db: AsyncSession, test_user: User
    ):
        """Test write key can use bulk import."""
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
            response = await client.post(
                "/api/v1/bulk/companies",
                headers={"X-API-Key": full_key},
                json={"companies": [{"name": "Bulk Co"}]}
            )
            assert response.status_code in [200, 202]


class TestAdminAccess:
    """Test ADMIN access level permissions."""

    async def test_admin_can_manage_api_keys(
        self, db: AsyncSession, test_user: User
    ):
        """Test admin key can manage API keys."""
        full_key, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            name="Admin Key",
            key_prefix=prefix,
            key_hash=key_hash,
            access_level=AccessLevel.ADMIN,
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
            # List API keys
            response = await client.get(
                "/api/v1/api-keys/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 200
            
            # Create API key
            response = await client.post(
                "/api/v1/api-keys/",
                headers={"X-API-Key": full_key},
                json={"name": "New Key"}
            )
            assert response.status_code == 201
            
    async def test_write_cannot_manage_api_keys(
        self, db: AsyncSession, test_user: User
    ):
        """Test write key cannot manage API keys."""
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
            # Try to access API keys endpoint
            response = await client.get(
                "/api/v1/api-keys/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 403
            
    async def test_read_cannot_manage_api_keys(
        self, db: AsyncSession, test_user: User
    ):
        """Test read key cannot manage API keys."""
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
            # Try to access API keys endpoint
            response = await client.get(
                "/api/v1/api-keys/",
                headers={"X-API-Key": full_key}
            )
            assert response.status_code == 403
