"""Tests for Company CRUD endpoints."""

import pytest
from httpx import AsyncClient


# =============================================================================
# Story 2.1: Create Company
# =============================================================================

@pytest.mark.anyio
async def test_create_company_success(async_client: AsyncClient):
    """Test creating a company successfully."""
    response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["domain"] == "acme.com"
    assert data["status"] == "new"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.anyio
async def test_create_company_missing_name(async_client: AsyncClient):
    """Test that name is required."""
    response = await async_client.post(
        "/api/v1/companies/",
        json={"domain": "acme.com"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_company_optional_fields(async_client: AsyncClient):
    """Test creating a company with only name (all other fields optional)."""
    response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Minimal Corp"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Corp"
    assert data["domain"] is None


# =============================================================================
# Story 2.2: Duplicate Detection
# =============================================================================

@pytest.mark.anyio
async def test_create_company_duplicate_domain(async_client: AsyncClient):
    """Test that duplicate domain returns 409 conflict."""
    # Create first company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com"},
    )
    # Try to create second with same domain
    response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Another Acme", "domain": "acme.com"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_domain_normalization_lowercase(async_client: AsyncClient):
    """Test that domains are normalized to lowercase."""
    response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "ACME.COM"},
    )
    assert response.status_code == 201
    assert response.json()["domain"] == "acme.com"


@pytest.mark.anyio
async def test_different_subdomains_allowed(async_client: AsyncClient):
    """Test that different subdomains are treated as different domains."""
    # Create first company
    response1 = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com"},
    )
    assert response1.status_code == 201

    # Create second with subdomain
    response2 = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Sub Acme", "domain": "sub.acme.com"},
    )
    assert response2.status_code == 201


# =============================================================================
# Story 2.3: Read & Update Company
# =============================================================================

@pytest.mark.anyio
async def test_get_company_success(async_client: AsyncClient):
    """Test getting a company by ID."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "Tech"},
    )
    company_id = create_response.json()["id"]

    # Get company
    response = await async_client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["domain"] == "acme.com"
    assert data["industry"] == "Tech"


@pytest.mark.anyio
async def test_get_company_not_found(async_client: AsyncClient):
    """Test getting a non-existent company returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/api/v1/companies/{fake_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_company_partial(async_client: AsyncClient):
    """Test partial update only changes specified fields."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "Tech"},
    )
    company_id = create_response.json()["id"]

    # Update only industry
    response = await async_client.patch(
        f"/api/v1/companies/{company_id}",
        json={"industry": "Finance"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corp"  # Unchanged
    assert data["domain"] == "acme.com"  # Unchanged
    assert data["industry"] == "Finance"  # Updated


@pytest.mark.anyio
async def test_update_company_not_found(async_client: AsyncClient):
    """Test updating a non-existent company returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.patch(
        f"/api/v1/companies/{fake_id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 404


# =============================================================================
# Story 2.4: Soft Delete & Restore
# =============================================================================

@pytest.mark.anyio
async def test_delete_company(async_client: AsyncClient):
    """Test soft deleting a company."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp"},
    )
    company_id = create_response.json()["id"]

    # Delete company
    response = await async_client.delete(f"/api/v1/companies/{company_id}")
    assert response.status_code == 204


@pytest.mark.anyio
async def test_deleted_company_not_in_list(async_client: AsyncClient):
    """Test that deleted companies are excluded from list."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp"},
    )
    company_id = create_response.json()["id"]

    # Delete company
    await async_client.delete(f"/api/v1/companies/{company_id}")

    # List companies
    response = await async_client.get("/api/v1/companies/")
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["id"] != company_id for item in items)


@pytest.mark.anyio
async def test_deleted_company_returns_404(async_client: AsyncClient):
    """Test that getting a deleted company returns 404."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp"},
    )
    company_id = create_response.json()["id"]

    # Delete company
    await async_client.delete(f"/api/v1/companies/{company_id}")

    # Try to get deleted company
    response = await async_client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_restore_company(async_client: AsyncClient):
    """Test restoring a soft-deleted company."""
    # Create company
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp"},
    )
    company_id = create_response.json()["id"]

    # Delete company
    await async_client.delete(f"/api/v1/companies/{company_id}")

    # Restore company
    response = await async_client.post(f"/api/v1/companies/{company_id}/restore")
    assert response.status_code == 200
    assert response.json()["deleted_at"] is None

    # Verify it's accessible again
    get_response = await async_client.get(f"/api/v1/companies/{company_id}")
    assert get_response.status_code == 200


# =============================================================================
# Story 2.5: Company Tagging
# =============================================================================

@pytest.mark.anyio
async def test_create_with_tags(async_client: AsyncClient):
    """Test creating a company with all three tag arrays."""
    response = await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Acme Corp",
            "custom_tags_a": ["tag1", "tag2"],
            "custom_tags_b": ["priority"],
            "custom_tags_c": ["vip", "enterprise"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["custom_tags_a"] == ["tag1", "tag2"]
    assert data["custom_tags_b"] == ["priority"]
    assert data["custom_tags_c"] == ["vip", "enterprise"]


@pytest.mark.anyio
async def test_update_single_tag_array(async_client: AsyncClient):
    """Test updating one tag array doesn't affect others."""
    # Create company with tags
    create_response = await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Acme Corp",
            "custom_tags_a": ["original"],
            "custom_tags_b": ["keep-this"],
        },
    )
    company_id = create_response.json()["id"]

    # Update only custom_tags_a
    response = await async_client.patch(
        f"/api/v1/companies/{company_id}",
        json={"custom_tags_a": ["updated"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["custom_tags_a"] == ["updated"]
    assert data["custom_tags_b"] == ["keep-this"]  # Unchanged


# =============================================================================
# Story 2.6: List Companies with Pagination
# =============================================================================

@pytest.mark.anyio
async def test_list_companies(async_client: AsyncClient):
    """Test listing companies returns items array."""
    # Create a company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp"},
    )

    response = await async_client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_list_empty(async_client: AsyncClient):
    """Test listing companies when none exist."""
    response = await async_client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


@pytest.mark.anyio
async def test_list_pagination(async_client: AsyncClient):
    """Test pagination limit works."""
    # Create 5 companies
    for i in range(5):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i}"},
        )

    # Request with limit=2
    response = await async_client.get("/api/v1/companies/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None
