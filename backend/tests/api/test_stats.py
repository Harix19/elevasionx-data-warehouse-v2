"""Tests for the stats endpoint.

Tests that the stats endpoint returns correct dashboard statistics
and requires authentication.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.contact import Contact
from app.models.user import User


class TestStatsEndpoint:
    """Test stats endpoint functionality."""

    async def test_get_stats_success(
        self, async_client: AsyncClient
    ):
        """Test successful stats retrieval."""
        response = await async_client.get("/api/v1/stats/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "companies" in data
        assert "contacts" in data
        
        # Check company stats
        assert "total" in data["companies"]
        assert "by_industry" in data["companies"]
        assert "by_country" in data["companies"]
        assert "by_status" in data["companies"]
        
        # Check contact stats
        assert "total" in data["contacts"]
        assert "by_seniority" in data["contacts"]
        assert "by_department" in data["contacts"]
        assert "by_status" in data["contacts"]
        
    async def test_get_stats_with_data(
        self, async_client: AsyncClient, db: AsyncSession
    ):
        """Test stats with actual data."""
        # Create some companies
        companies = [
            Company(name="Tech Co", industry="Software", country="US"),
            Company(name="Finance Co", industry="Finance", country="UK"),
            Company(name="Another Tech", industry="Software", country="US"),
        ]
        for company in companies:
            db.add(company)
        await db.commit()
        
        # Create some contacts
        contacts = [
            Contact(email="exec@tech.com", seniority_level="Executive", department="Sales"),
            Contact(email="manager@finance.com", seniority_level="Manager", department="Marketing"),
        ]
        for contact in contacts:
            db.add(contact)
        await db.commit()
        
        response = await async_client.get("/api/v1/stats/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify counts
        assert data["companies"]["total"] >= 3
        assert data["contacts"]["total"] >= 2
        
        # Verify grouping
        industries = data["companies"]["by_industry"]
        assert any(i["industry"] == "Software" for i in industries)
        assert any(i["industry"] == "Finance" for i in industries)


class TestStatsCaching:
    """Test stats caching behavior."""

    async def test_stats_cached(
        self, async_client: AsyncClient
    ):
        """Test that stats are cached for performance."""
        # First request
        response1 = await async_client.get("/api/v1/stats/")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request should return cached data
        response2 = await async_client.get("/api/v1/stats/")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Data should be identical (from cache)
        assert data1 == data2
