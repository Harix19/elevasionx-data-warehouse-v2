"""Tests for multi-field and range filtering (Story 4-3)."""

import pytest
from httpx import AsyncClient


# =============================================================================
# Story 4-3: Multi-Field and Range Filtering - Companies
# =============================================================================

@pytest.mark.anyio
async def test_filter_industry_case_insensitive(async_client: AsyncClient):
    """Test industry filter is case-insensitive."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com", "industry": "Technology"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company B", "domain": "b.com", "industry": "Finance"},
    )

    # Filter by industry with different case
    response = await async_client.get("/api/v1/companies/?industry=technology")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company A"

    # Upper case should also match
    response = await async_client.get("/api/v1/companies/?industry=TECHNOLOGY")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.anyio
async def test_filter_country(async_client: AsyncClient):
    """Test country filter."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com", "country": "USA"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company B", "domain": "b.com", "country": "Canada"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company C", "domain": "c.com", "country": "USA"},
    )

    # Filter by country
    response = await async_client.get("/api/v1/companies/?country=usa")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    names = {item["name"] for item in data["items"]}
    assert names == {"Company A", "Company C"}


@pytest.mark.anyio
async def test_filter_status(async_client: AsyncClient):
    """Test lead_status filter."""
    # Create companies with different statuses
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com", "status": "qualified"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company B", "domain": "b.com", "status": "new"},
    )

    # Filter by lead_status (case-insensitive)
    response = await async_client.get("/api/v1/companies/?lead_status=QUALIFIED")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company A"


@pytest.mark.anyio
async def test_filter_revenue_range(async_client: AsyncClient):
    """Test revenue range filter."""
    # Create companies with different revenues
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Small Co", "domain": "small.com", "revenue": 100000.50},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Medium Co", "domain": "medium.com", "revenue": 500000.75},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Large Co", "domain": "large.com", "revenue": 1000000.00},
    )

    # Filter by revenue range
    response = await async_client.get("/api/v1/companies/?revenue_min=200000&revenue_max=800000")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Medium Co"


@pytest.mark.anyio
async def test_filter_revenue_min_only(async_client: AsyncClient):
    """Test revenue filter with only minimum."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Small Co", "domain": "small.com", "revenue": 100000},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Large Co", "domain": "large.com", "revenue": 1000000},
    )

    # Filter by minimum revenue only
    response = await async_client.get("/api/v1/companies/?revenue_min=500000")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Large Co"


@pytest.mark.anyio
async def test_filter_revenue_max_only(async_client: AsyncClient):
    """Test revenue filter with only maximum."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Small Co", "domain": "small.com", "revenue": 100000},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Large Co", "domain": "large.com", "revenue": 1000000},
    )

    # Filter by maximum revenue only
    response = await async_client.get("/api/v1/companies/?revenue_max=500000")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Small Co"


@pytest.mark.anyio
async def test_filter_revenue_invalid_range_400(async_client: AsyncClient):
    """Test that min > max returns 400 error."""
    response = await async_client.get("/api/v1/companies/?revenue_min=1000000&revenue_max=500000")
    assert response.status_code == 400
    assert "revenue_min cannot be greater than revenue_max" in response.json()["detail"]


@pytest.mark.anyio
async def test_filter_lead_score_range(async_client: AsyncClient):
    """Test lead score range filter."""
    # Create companies with different lead scores
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com", "lead_score": 10},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company B", "domain": "b.com", "lead_score": 50},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company C", "domain": "c.com", "lead_score": 90},
    )

    # Filter by lead score range
    response = await async_client.get("/api/v1/companies/?lead_score_min=40&lead_score_max=80")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Company B"


@pytest.mark.anyio
async def test_filter_lead_score_invalid_range_400(async_client: AsyncClient):
    """Test lead score min > max returns 400."""
    response = await async_client.get("/api/v1/companies/?lead_score_min=90&lead_score_max=10")
    assert response.status_code == 400
    assert "lead_score_min cannot be greater than lead_score_max" in response.json()["detail"]


@pytest.mark.anyio
async def test_filter_employee_count_range(async_client: AsyncClient):
    """Test employee count range filter."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Startup", "domain": "startup.com", "employee_count": 5},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "SMB", "domain": "smb.com", "employee_count": 50},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Enterprise", "domain": "enterprise.com", "employee_count": 500},
    )

    # Filter by employee count range
    response = await async_client.get("/api/v1/companies/?employee_count_min=20&employee_count_max=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "SMB"


@pytest.mark.anyio
async def test_filter_employee_count_invalid_range_400(async_client: AsyncClient):
    """Test employee count min > max returns 400."""
    response = await async_client.get("/api/v1/companies/?employee_count_min=500&employee_count_max=100")
    assert response.status_code == 400
    assert "employee_count_min cannot be greater than employee_count_max" in response.json()["detail"]


@pytest.mark.anyio
async def test_filter_combined_all(async_client: AsyncClient):
    """Test combining string filters, range filters, and tag filters."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Perfect Match",
            "domain": "perfect.com",
            "industry": "Technology",
            "country": "USA",
            "revenue": 500000,
            "lead_score": 75,
            "employee_count": 50,
            "custom_tags_a": ["enterprise", "saas"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "Partial Match",
            "domain": "partial.com",
            "industry": "Technology",
            "country": "Canada",  # Different country
            "revenue": 500000,
            "lead_score": 75,
            "employee_count": 50,
            "custom_tags_a": ["enterprise", "saas"],
        },
    )
    await async_client.post(
        "/api/v1/companies/",
        json={
            "name": "No Match",
            "domain": "nomatch.com",
            "industry": "Finance",
            "country": "USA",
            "revenue": 100000,  # Too low
            "lead_score": 20,
            "employee_count": 5,
            "custom_tags_a": ["startup"],
        },
    )

    # Combine all filters
    response = await async_client.get(
        "/api/v1/companies/?"
        "industry=technology&"
        "country=usa&"
        "revenue_min=400000&revenue_max=600000&"
        "lead_score_min=70&lead_score_max=80&"
        "employee_count_min=40&employee_count_max=60&"
        "tags_a=enterprise"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Perfect Match"


@pytest.mark.anyio
async def test_filter_null_values_excluded(async_client: AsyncClient):
    """Test that companies with null values are excluded from range filters."""
    # Create companies with and without revenue
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Has Revenue", "domain": "hasrev.com", "revenue": 500000},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "No Revenue", "domain": "norev.com"},  # revenue is null
    )

    # Filter by revenue - should only return company with revenue
    response = await async_client.get("/api/v1/companies/?revenue_min=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Has Revenue"


# =============================================================================
# Story 4-3: Multi-Field and Range Filtering - Contacts
# =============================================================================

@pytest.mark.anyio
async def test_filter_contacts_seniority_level(async_client: AsyncClient):
    """Test seniority level filter for contacts."""
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
            "last_name": "Senior",
            "email": "alice@test.com",
            "company_id": company_id,
            "seniority_level": "Director",
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Junior",
            "email": "bob@test.com",
            "company_id": company_id,
            "seniority_level": "Associate",
        },
    )

    # Filter by seniority level (case-insensitive)
    response = await async_client.get("/api/v1/contacts/?seniority_level=director")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Alice"


@pytest.mark.anyio
async def test_filter_contacts_department(async_client: AsyncClient):
    """Test department filter for contacts."""
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
            "last_name": "Engineer",
            "email": "alice@test.com",
            "company_id": company_id,
            "department": "Engineering",
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Sales",
            "email": "bob@test.com",
            "company_id": company_id,
            "department": "Sales",
        },
    )

    # Filter by department
    response = await async_client.get("/api/v1/contacts/?department=ENGINEERING")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Alice"


@pytest.mark.anyio
async def test_filter_contacts_lead_score_range(async_client: AsyncClient):
    """Test lead score range filter for contacts."""
    # Create a company
    company_response = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "domain": "test.com"},
    )
    company_id = company_response.json()["id"]

    # Create contacts with different lead scores
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Low",
            "last_name": "Score",
            "email": "low@test.com",
            "company_id": company_id,
            "lead_score": 20,
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "High",
            "last_name": "Score",
            "email": "high@test.com",
            "company_id": company_id,
            "lead_score": 80,
        },
    )

    # Filter by lead score range
    response = await async_client.get("/api/v1/contacts/?lead_score_min=50&lead_score_max=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "High"


@pytest.mark.anyio
async def test_filter_contacts_lead_score_invalid_range_400(async_client: AsyncClient):
    """Test contacts lead score min > max returns 400."""
    response = await async_client.get("/api/v1/contacts/?lead_score_min=90&lead_score_max=10")
    assert response.status_code == 400
    assert "lead_score_min cannot be greater than lead_score_max" in response.json()["detail"]


@pytest.mark.anyio
async def test_filter_contacts_combined(async_client: AsyncClient):
    """Test combining all contact filters."""
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
            "first_name": "Perfect",
            "last_name": "Match",
            "email": "perfect@test.com",
            "company_id": company_id,
            "seniority_level": "Director",
            "department": "Engineering",
            "lead_score": 85,
            "custom_tags_a": ["decision-maker"],
        },
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Partial",
            "last_name": "Match",
            "email": "partial@test.com",
            "company_id": company_id,
            "seniority_level": "Director",
            "department": "Sales",  # Different department
            "lead_score": 85,
            "custom_tags_a": ["decision-maker"],
        },
    )

    # Combine all filters
    response = await async_client.get(
        "/api/v1/contacts/?"
        "seniority_level=director&"
        "department=engineering&"
        "lead_score_min=80&lead_score_max=90&"
        "tags_a=decision-maker"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Perfect"
