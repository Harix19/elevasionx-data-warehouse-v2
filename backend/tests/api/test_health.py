"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_endpoint(async_client: AsyncClient):
    """Test /health/live returns 200 with status ok."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_liveness_endpoint_returns_json(async_client: AsyncClient):
    """Test /health/live returns valid JSON."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_endpoint_structure(async_client: AsyncClient):
    """Test /health/ready returns expected structure."""
    response = await async_client.get("/health/ready")

    # Should return 200 regardless of DB connection
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
