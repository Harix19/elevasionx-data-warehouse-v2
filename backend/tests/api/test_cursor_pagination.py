"""Tests for cursor-based pagination (Story 4-4)."""

import pytest
from httpx import AsyncClient


# =============================================================================
# Story 4-4: Cursor-Based Pagination - Companies
# =============================================================================

@pytest.mark.anyio
async def test_cursor_pagination_first_page(async_client: AsyncClient):
    """Test first page of cursor pagination returns items and cursor."""
    # Create 25 companies
    for i in range(25):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i:02d}", "domain": f"company{i:02d}.com"},
        )

    # Fetch first page with limit 10
    response = await async_client.get("/api/v1/companies/?limit=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 10
    assert data["has_more"] is True
    assert data["next_cursor"] is not None

    # Items should be ordered by created_at DESC
    # Most recent (Company 24) should be first
    assert "Company 24" in data["items"][0]["name"]


@pytest.mark.anyio
async def test_cursor_pagination_next_page(async_client: AsyncClient):
    """Test using cursor to fetch next page."""
    # Create 25 companies
    for i in range(25):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i:02d}", "domain": f"company{i:02d}.com"},
        )

    # Fetch first page
    response = await async_client.get("/api/v1/companies/?limit=10")
    assert response.status_code == 200
    first_page = response.json()
    assert first_page["has_more"] is True
    cursor = first_page["next_cursor"]

    # Fetch second page using cursor
    response = await async_client.get(f"/api/v1/companies/?limit=10&cursor={cursor}")
    assert response.status_code == 200
    second_page = response.json()

    assert len(second_page["items"]) == 10
    assert second_page["has_more"] is True
    assert second_page["next_cursor"] is not None
    assert second_page["next_cursor"] != cursor  # Different cursor

    # No overlap between pages
    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert len(first_ids & second_ids) == 0


@pytest.mark.anyio
async def test_cursor_pagination_last_page_no_more(async_client: AsyncClient):
    """Test last page has has_more=False and no next_cursor."""
    # Create exactly 15 companies
    for i in range(15):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i:02d}", "domain": f"company{i:02d}.com"},
        )

    # Fetch first page with limit 10
    response = await async_client.get("/api/v1/companies/?limit=10")
    assert response.status_code == 200
    first_page = response.json()
    assert first_page["has_more"] is True
    cursor = first_page["next_cursor"]

    # Fetch second (last) page
    response = await async_client.get(f"/api/v1/companies/?limit=10&cursor={cursor}")
    assert response.status_code == 200
    last_page = response.json()

    assert len(last_page["items"]) == 5  # Only 5 remaining
    assert last_page["has_more"] is False
    assert last_page["next_cursor"] is None


@pytest.mark.anyio
async def test_cursor_pagination_invalid_cursor_400(async_client: AsyncClient):
    """Test invalid cursor returns 400."""
    # Create a company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )

    # Use invalid cursor
    response = await async_client.get("/api/v1/companies/?cursor=invalid_cursor_format")
    assert response.status_code == 400
    assert "Invalid cursor format" in response.json()["detail"]


@pytest.mark.anyio
async def test_cursor_pagination_limit_max_100(async_client: AsyncClient):
    """Test limit cannot exceed 100."""
    # Create a company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )

    # Request with limit > 100
    response = await async_client.get("/api/v1/companies/?limit=101")
    assert response.status_code == 400
    assert "cannot exceed 100" in response.json()["detail"]


@pytest.mark.anyio
async def test_cursor_pagination_empty_results(async_client: AsyncClient):
    """Test pagination with no results."""
    response = await async_client.get("/api/v1/companies/?limit=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 0
    assert data["has_more"] is False
    assert data["next_cursor"] is None


@pytest.mark.anyio
async def test_cursor_pagination_excludes_deleted(async_client: AsyncClient):
    """Test cursor pagination excludes soft-deleted companies."""
    # Create 5 companies
    company_ids = []
    for i in range(5):
        response = await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i}", "domain": f"company{i}.com"},
        )
        company_ids.append(response.json()["id"])

    # Delete the middle company
    await async_client.delete(f"/api/v1/companies/{company_ids[2]}")

    # Fetch all companies
    response = await async_client.get("/api/v1/companies/?limit=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 4  # Only 4 non-deleted

    returned_ids = {item["id"] for item in data["items"]}
    assert company_ids[2] not in returned_ids  # Deleted company not in results


# =============================================================================
# Story 4-4: Cursor-Based Pagination - Contacts
# =============================================================================

@pytest.mark.anyio
async def test_cursor_pagination_contacts_first_page(async_client: AsyncClient):
    """Test cursor pagination for contacts."""
    # Create a company first
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create 25 contacts
    for i in range(25):
        await async_client.post(
            "/api/v1/contacts/",
            json={
                "first_name": f"First{i:02d}",
                "last_name": f"Last{i:02d}",
                "email": f"contact{i:02d}@test.com",
                "company_id": company_id,
            },
        )

    # Fetch first page with limit 10
    response = await async_client.get("/api/v1/contacts/?limit=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 10
    assert data["has_more"] is True
    assert data["next_cursor"] is not None


@pytest.mark.anyio
async def test_cursor_pagination_contacts_next_page(async_client: AsyncClient):
    """Test contacts cursor pagination across pages."""
    # Create a company
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create 25 contacts
    for i in range(25):
        await async_client.post(
            "/api/v1/contacts/",
            json={
                "first_name": f"First{i:02d}",
                "last_name": f"Last{i:02d}",
                "email": f"contact{i:02d}@test.com",
                "company_id": company_id,
            },
        )

    # Fetch first page
    response = await async_client.get("/api/v1/contacts/?limit=10")
    first_page = response.json()
    cursor = first_page["next_cursor"]

    # Fetch second page
    response = await async_client.get(f"/api/v1/contacts/?limit=10&cursor={cursor}")
    assert response.status_code == 200
    second_page = response.json()

    assert len(second_page["items"]) == 10
    assert second_page["has_more"] is True

    # No overlap
    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert len(first_ids & second_ids) == 0


@pytest.mark.anyio
async def test_cursor_pagination_contacts_invalid_cursor(async_client: AsyncClient):
    """Test contacts endpoint rejects invalid cursor."""
    response = await async_client.get("/api/v1/contacts/?cursor=bad_cursor")
    assert response.status_code == 400
    assert "Invalid cursor format" in response.json()["detail"]


@pytest.mark.anyio
async def test_cursor_pagination_contacts_limit_validation(async_client: AsyncClient):
    """Test contacts endpoint enforces limit <= 100."""
    response = await async_client.get("/api/v1/contacts/?limit=150")
    assert response.status_code == 400
    assert "cannot exceed 100" in response.json()["detail"]


@pytest.mark.anyio
async def test_cursor_pagination_stable_across_inserts(async_client: AsyncClient):
    """Test cursor pagination remains stable when new items are inserted."""
    # Create 20 companies
    for i in range(20):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i:02d}", "domain": f"company{i:02d}.com"},
        )

    # Fetch first page
    response = await async_client.get("/api/v1/companies/?limit=10")
    first_page = response.json()
    cursor = first_page["next_cursor"]
    first_page_ids = {item["id"] for item in first_page["items"]}

    # Insert new companies (these should appear on first page if we refetch)
    for i in range(100, 105):
        await async_client.post(
            "/api/v1/companies/",
            json={"name": f"Company {i}", "domain": f"company{i}.com"},
        )

    # Fetch second page using original cursor
    # Should still get the same items that were after the cursor
    response = await async_client.get(f"/api/v1/companies/?limit=10&cursor={cursor}")
    second_page = response.json()

    # The second page should not include any IDs from first page
    second_page_ids = {item["id"] for item in second_page["items"]}
    assert len(first_page_ids & second_page_ids) == 0
