"""Tests for tag-based filtering (Story 4-2)."""

import pytest
from httpx import AsyncClient


# =============================================================================
# Story 4-2: Tag-Based Filtering - Companies
# =============================================================================

@pytest.mark.anyio
async def test_filter_tags_or_logic_single(async_client: AsyncClient):
    """Test OR logic with single tag match."""
    # Create companies with different tags
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["enterprise", "saas"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company B",
            "domain": "b.com",
            "custom_tags_a": ["startup", "b2b"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company C",
            "domain": "c.com",
            "custom_tags_a": ["nonprofit"],
        },
    )

    # Filter by single tag - should match Company A
    response = await async_client.get("/api/v1/companies/?tags_a=enterprise")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company A"


@pytest.mark.anyio
async def test_filter_tags_or_logic_multiple(async_client: AsyncClient):
    """Test OR logic with multiple tags (any match)."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["enterprise", "saas"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company B",
            "domain": "b.com",
            "custom_tags_a": ["startup", "b2b"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company C",
            "domain": "c.com",
            "custom_tags_a": ["nonprofit"],
        },
    )

    # Filter by multiple tags - should match A and B
    response = await async_client.get("/api/v1/companies/?tags_a=enterprise,startup")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    names = {item["name"] for item in data["items"]}
    assert names == {"Company A", "Company B"}


@pytest.mark.anyio
async def test_filter_tags_and_logic(async_client: AsyncClient):
    """Test AND logic requiring all tags to exist."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["enterprise", "saas", "verified"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company B",
            "domain": "b.com",
            "custom_tags_a": ["enterprise", "saas"],  # Missing "verified"
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company C",
            "domain": "c.com",
            "custom_tags_a": ["verified"],
        },
    )

    # Filter requiring ALL tags - should only match Company A
    response = await async_client.get("/api/v1/companies/?tags_a_all=enterprise,saas,verified")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company A"


@pytest.mark.anyio
async def test_filter_tags_cross_category(async_client: AsyncClient):
    """Test filtering across different tag categories."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["enterprise"],
            "custom_tags_b": ["tech"],
            "custom_tags_c": ["west-coast"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company B",
            "domain": "b.com",
            "custom_tags_a": ["enterprise"],
            "custom_tags_b": ["finance"],
            "custom_tags_c": ["east-coast"],
        },
    )

    # Filter by tags_a AND tags_b - should only match Company A
    response = await async_client.get("/api/v1/companies/?tags_a=enterprise&tags_b=tech")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company A"


@pytest.mark.anyio
async def test_filter_tags_empty_ignored(async_client: AsyncClient):
    """Test that empty tag filters are ignored."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com"},
    )

    # Empty tags parameter should be ignored
    response = await async_client.get("/api/v1/companies/?tags_a=")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1

    # Whitespace-only should also be ignored
    response = await async_client.get("/api/v1/companies/?tags_a=   ")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.anyio
async def test_filter_tags_combined_with_pagination(async_client: AsyncClient):
    """Test tag filtering works with cursor pagination."""
    # Create 15 companies with tags
    for i in range(15):
        tags = ["enterprise"] if i % 2 == 0 else ["startup"]
        await async_client.post(
            "/api/v1/companies/",
            json={
                "name": f"Company {i:02d}",
                "domain": f"company{i:02d}.com",
                "custom_tags_a": tags,
            },
        )

    # Filter by enterprise and paginate
    response = await async_client.get("/api/v1/companies/?tags_a=enterprise&limit=5")
    assert response.status_code == 200
    data = response.json()

    # Should have 8 enterprise companies (0, 2, 4, 6, 8, 10, 12, 14)
    # First page should have 5
    assert len(data["items"]) == 5
    assert data["has_more"] is True
    assert all("enterprise" in item["custom_tags_a"] for item in data["items"])

    # Get next page
    cursor = data["next_cursor"]
    response = await async_client.get(f"/api/v1/companies/?tags_a=enterprise&limit=5&cursor={cursor}")
    assert response.status_code == 200
    second_page = response.json()
    assert len(second_page["items"]) == 3  # Remaining 3 enterprise companies


@pytest.mark.anyio
async def test_filter_tags_no_matches(async_client: AsyncClient):
    """Test filtering with tags that don't match any companies."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["enterprise"],
        },
    )

    # Filter by non-existent tag
    response = await async_client.get("/api/v1/companies/?tags_a=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["has_more"] is False


@pytest.mark.anyio
async def test_filter_tags_case_sensitive(async_client: AsyncClient):
    """Test that tag filtering is case-sensitive."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Company A",
            "domain": "a.com",
            "custom_tags_a": ["Enterprise"],
        },
    )

    # Filter with different case should not match
    response = await async_client.get("/api/v1/companies/?tags_a=enterprise")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0

    # Exact case should match
    response = await async_client.get("/api/v1/companies/?tags_a=Enterprise")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


# =============================================================================
# Story 4-2: Tag-Based Filtering - Contacts
# =============================================================================

@pytest.mark.anyio
async def test_filter_contacts_tags_or_logic(async_client: AsyncClient):
    """Test contact tag filtering with OR logic."""
    # Create a company
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create contacts with tags
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "company_id": company_id,
            "custom_tags_a": ["decision-maker", "technical"],
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@test.com",
            "company_id": company_id,
            "custom_tags_a": ["influencer"],
        },
    )

    # Filter by tag
    response = await async_client.get("/api/v1/contacts/?tags_a=decision-maker")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Alice"


@pytest.mark.anyio
async def test_filter_contacts_tags_and_logic(async_client: AsyncClient):
    """Test contact tag filtering with AND logic."""
    # Create a company
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "company_id": company_id,
            "custom_tags_a": ["decision-maker", "technical", "responsive"],
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@test.com",
            "company_id": company_id,
            "custom_tags_a": ["decision-maker", "technical"],  # Missing "responsive"
        },
    )

    # Filter requiring all tags
    response = await async_client.get("/api/v1/contacts/?tags_a_all=decision-maker,technical,responsive")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Alice"


@pytest.mark.anyio
async def test_filter_contacts_multiple_categories(async_client: AsyncClient):
    """Test filtering contacts across multiple tag categories."""
    # Create a company
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@test.com",
            "company_id": company_id,
            "custom_tags_a": ["vip"],
            "custom_tags_b": ["engineering"],
            "custom_tags_c": ["active"],
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@test.com",
            "company_id": company_id,
            "custom_tags_a": ["vip"],
            "custom_tags_b": ["sales"],
            "custom_tags_c": ["active"],
        },
    )

    # Filter by tags_a and tags_b
    response = await async_client.get("/api/v1/contacts/?tags_a=vip&tags_b=engineering")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Alice"
