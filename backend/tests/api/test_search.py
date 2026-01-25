"""Tests for full-text search (Story 4-1)."""

import pytest
from httpx import AsyncClient


# =============================================================================
# Story 4-1: Full-Text Search
# =============================================================================

@pytest.mark.anyio
async def test_search_companies_by_name(async_client: AsyncClient):
    """Test searching companies by name."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Industries", "domain": "acme.com", "description": "General manufacturing"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Globex Corp", "domain": "globex.com", "description": "Global exports"},
    )

    # Search for "Acme"
    response = await async_client.get("/api/v1/search/?q=Acme")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["entity_type"] == "company"
    assert data["results"][0]["data"]["name"] == "Acme Industries"


@pytest.mark.anyio
async def test_search_companies_by_description(async_client: AsyncClient):
    """Test searching companies by description."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company A", "domain": "a.com", "description": "Specializes in artificial intelligence"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Company B", "domain": "b.com", "description": "Traditional manufacturing"},
    )

    # Search for "intelligence"
    response = await async_client.get("/api/v1/search/?q=intelligence")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["name"] == "Company A"


@pytest.mark.anyio
async def test_search_companies_by_domain(async_client: AsyncClient):
    """Test searching companies by domain."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Google Inc", "domain": "google.com"},
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Amazon Inc", "domain": "amazon.com"},
    )

    # Search for "google.com"
    response = await async_client.get("/api/v1/search/?q=google.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["name"] == "Google Inc"


@pytest.mark.anyio
async def test_search_contacts_by_name(async_client: AsyncClient):
    """Test searching contacts by name."""
    # Create companies first
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Tech Corp", "domain": "tech.com"},
    )
    company_id = company.json()["id"]

    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "John", "last_name": "Doe", "company_id": company_id},
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "Jane", "last_name": "Smith", "company_id": company_id},
    )

    # Search for "John"
    response = await async_client.get("/api/v1/search/?q=John")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["entity_type"] == "contact"
    assert "John Doe" in data["results"][0]["data"]["full_name"]


@pytest.mark.anyio
async def test_search_contacts_by_email(async_client: AsyncClient):
    """Test searching contacts by email."""
    # Create companies first
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Tech Corp", "domain": "tech.com"},
    )
    company_id = company.json()["id"]

    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "company_id": company_id},
    )

    # Search for "john.doe"
    response = await async_client.get("/api/v1/search/?q=john.doe")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["email"] == "john.doe@example.com"


@pytest.mark.anyio
async def test_search_contacts_by_job_title(async_client: AsyncClient):
    """Test searching contacts by job title."""
    # Create companies first
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Tech Corp", "domain": "tech.com"},
    )
    company_id = company.json()["id"]

    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "CTO",
            "last_name": "Person",
            "job_title": "Chief Technology Officer",
            "company_id": company_id
        },
    )

    # Search for "Technology"
    response = await async_client.get("/api/v1/search/?q=Technology")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["job_title"] == "Chief Technology Officer"


@pytest.mark.anyio
async def test_search_multi_term_ranked(async_client: AsyncClient):
    """Test multi-term search and relevance ranking."""
    # Create companies
    # First company has "Data" and "Analytics" in name (higher weight)
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Data Analytics Corp", "domain": "data.com", "description": "Solutions"},
    )
    # Second company has terms in description (lower weight usually) or just one term repeated
    # Note: plainto_tsquery uses AND logic, so both must have "Data" and "Analytics"
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Other Corp", "domain": "analytics.com", "description": "Data and Analytics solutions"},
    )

    # Search for "Data Analytics"
    response = await async_client.get("/api/v1/search/?q=Data Analytics")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 2

    # First result should be the one with terms in name (higher relevance)
    assert data["results"][0]["data"]["name"] == "Data Analytics Corp"
    assert data["results"][0]["relevance_score"] > data["results"][1]["relevance_score"]


@pytest.mark.anyio
async def test_search_case_insensitive(async_client: AsyncClient):
    """Test that search is case-insensitive."""
    # Create companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "UPPERCASE NAME", "domain": "upper.com"},
    )

    # Search with lowercase
    response = await async_client.get("/api/v1/search/?q=uppercase")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["name"] == "UPPERCASE NAME"


@pytest.mark.anyio
async def test_search_empty_query_400(async_client: AsyncClient):
    """Test empty search query returns 400."""
    response = await async_client.get("/api/v1/search/?q=  ")
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


@pytest.mark.anyio
async def test_search_type_companies_only(async_client: AsyncClient):
    """Test searching only companies."""
    # Create company and contact with same name term
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Omega Corp", "domain": "omega.com"},
    )
    company_id = company.json()["id"]

    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "Omega", "last_name": "Person", "company_id": company_id},
    )

    # Search for "Omega" but restrict to companies
    response = await async_client.get("/api/v1/search/?q=Omega&type=companies")
    assert response.status_code == 200
    data = response.json()

    # Should only get 1 result (the company)
    assert len(data["results"]) == 1
    assert data["results"][0]["entity_type"] == "company"


@pytest.mark.anyio
async def test_search_type_contacts_only(async_client: AsyncClient):
    """Test searching only contacts."""
    # Create company and contact with same name term
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Gamma Corp", "domain": "gamma.com"},
    )
    company_id = company.json()["id"]

    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "Gamma", "last_name": "Person", "company_id": company_id},
    )

    # Search for "Gamma" but restrict to contacts
    response = await async_client.get("/api/v1/search/?q=Gamma&type=contacts")
    assert response.status_code == 200
    data = response.json()

    # Should only get 1 result (the contact)
    assert len(data["results"]) == 1
    assert data["results"][0]["entity_type"] == "contact"


@pytest.mark.anyio
async def test_search_excludes_deleted(async_client: AsyncClient):
    """Test search excludes soft-deleted entities."""
    # Create company
    company = await async_client.post(
        "/api/v1/companies/",
        json={"name": "Deleted Corp", "domain": "deleted.com"},
    )
    company_id = company.json()["id"]

    # Verify it's searchable
    response = await async_client.get("/api/v1/search/?q=Deleted")
    assert len(response.json()["results"]) == 1

    # Delete it
    await async_client.delete(f"/api/v1/companies/{company_id}")

    # Verify it's no longer searchable
    response = await async_client.get("/api/v1/search/?q=Deleted")
    data = response.json()
    assert len(data["results"]) == 0
