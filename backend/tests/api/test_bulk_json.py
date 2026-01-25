"""Tests for JSON bulk operations endpoints."""

import pytest
from httpx import AsyncClient

from app.models.company import Company
from app.models.contact import Contact


@pytest.mark.anyio
async def test_bulk_companies_upsert_mode(async_client: AsyncClient, db):
    """Test bulk company creation in upsert mode."""
    payload = {
        "records": [
            {"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"},
            {"name": "TechStart", "domain": "techstart.io", "industry": "Software"},
            {"name": "DataCo", "domain": "dataco.com", "industry": "Analytics"},
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/companies", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["created"] == 3
    assert data["updated"] == 0
    assert data["skipped"] == 0
    assert len(data["errors"]) == 0

    # Verify database
    from sqlalchemy import select
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    assert len(companies) == 3


@pytest.mark.anyio
async def test_bulk_companies_upsert_updates_existing(async_client: AsyncClient, db):
    """Test bulk company upsert updates existing records."""
    # Create initial company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )

    # Upsert with updated data
    payload = {
        "records": [
            {
                "name": "Acme Corporation",
                "domain": "acme.com",
                "industry": "Technology",
                "country": "USA"
            }
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/companies", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert data["updated"] == 1

    # Verify update
    from sqlalchemy import select
    result = await db.execute(select(Company).where(Company.domain == "acme.com"))
    updated = result.scalar_one()
    assert updated.name == "Acme Corporation"
    assert updated.industry == "Technology"
    assert updated.country == "USA"


@pytest.mark.anyio
async def test_bulk_companies_insert_only_mode(async_client: AsyncClient, db):
    """Test bulk company creation in insert-only mode (skip duplicates)."""
    # Create existing company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )

    # Try to insert with same domain
    payload = {
        "records": [
            {"name": "Acme Corp Updated", "domain": "acme.com", "industry": "Tech"},
            {"name": "NewCo", "domain": "newco.com", "industry": "Software"},
        ],
        "upsert": False
    }

    response = await async_client.post("/api/v1/bulk/companies", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1  # Only NewCo
    assert data["updated"] == 0
    assert data["skipped"] == 1  # Acme duplicate skipped

    # Verify original not updated
    from sqlalchemy import select
    result = await db.execute(select(Company).where(Company.domain == "acme.com"))
    original = result.scalar_one()
    assert original.name == "Acme Corp"  # Not updated


@pytest.mark.anyio
async def test_bulk_companies_max_records_validation(async_client: AsyncClient):
    """Test bulk companies enforces 10,000 record limit."""
    payload = {
        "records": [
            {"name": f"Company {i}", "domain": f"company{i}.com"}
            for i in range(10001)  # Exceeds limit
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/companies", json=payload)

    assert response.status_code == 422  # Validation error
    assert "10,000" in str(response.json())


@pytest.mark.anyio
async def test_bulk_contacts_upsert_mode(async_client: AsyncClient, db):
    """Test bulk contact creation in upsert mode with company resolution."""
    # Create test companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io"}
    )

    payload = {
        "records": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@acme.com",
                "job_title": "CEO",
                "company_domain": "acme.com"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@techstart.io",
                "job_title": "CTO",
                "company_domain": "techstart.io"
            },
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/contacts", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["created"] == 2
    assert data["updated"] == 0

    # Verify company resolution
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@acme.com"))
    john = result.scalar_one()
    assert john.company_id is not None


@pytest.mark.anyio
async def test_bulk_contacts_upsert_updates_existing(async_client: AsyncClient, db):
    """Test bulk contact upsert updates existing records."""
    # Create initial contact
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "job_title": "Developer"
        }
    )

    # Upsert with updated data
    payload = {
        "records": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "job_title": "Senior Developer",
                "seniority_level": "Senior"
            }
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/contacts", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert data["updated"] == 1

    # Verify update
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@test.com"))
    updated = result.scalar_one()
    assert updated.job_title == "Senior Developer"
    assert updated.seniority_level == "Senior"


@pytest.mark.anyio
async def test_bulk_contacts_insert_only_mode(async_client: AsyncClient, db):
    """Test bulk contact creation in insert-only mode (skip duplicates)."""
    # Create existing contact
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "job_title": "Developer"
        }
    )

    # Try to insert with same email
    payload = {
        "records": [
            {
                "first_name": "John",
                "last_name": "Updated",
                "email": "john@test.com",
                "job_title": "Senior"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@test.com",
                "job_title": "Manager"
            },
        ],
        "upsert": False
    }

    response = await async_client.post("/api/v1/bulk/contacts", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1  # Only Jane
    assert data["updated"] == 0
    assert data["skipped"] == 1  # John duplicate skipped

    # Verify original not updated
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@test.com"))
    original = result.scalar_one()
    assert original.last_name == "Doe"  # Not updated


@pytest.mark.anyio
async def test_bulk_contacts_unmatched_company_domain(async_client: AsyncClient, db):
    """Test bulk contacts with company domain that doesn't exist."""
    payload = {
        "records": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@unknown.com",
                "company_domain": "unknown.com"
            }
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/contacts", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1

    # Contact should have null company_id but preserved domain
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@unknown.com"))
    contact = result.scalar_one()
    assert contact.company_id is None
    assert contact.company_domain == "unknown.com"


@pytest.mark.anyio
async def test_bulk_contacts_max_records_validation(async_client: AsyncClient):
    """Test bulk contacts enforces 10,000 record limit."""
    payload = {
        "records": [
            {
                "first_name": f"Person{i}",
                "last_name": "Test",
                "email": f"person{i}@test.com"
            }
            for i in range(10001)
        ],
        "upsert": True
    }

    response = await async_client.post("/api/v1/bulk/contacts", json=payload)

    assert response.status_code == 422
    assert "10,000" in str(response.json())
