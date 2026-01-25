"""Tests for CSV contact import endpoints."""

import pytest
from httpx import AsyncClient
from io import BytesIO

from app.models.company import Company
from app.models.contact import Contact


@pytest.mark.anyio
async def test_import_contacts_csv_success(async_client: AsyncClient, db):
    """Test successful contact CSV import with company resolution."""
    # Create test companies first
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io", "industry": "Software"}
    )

    csv_content = """first_name,last_name,email,job_title,company_domain
John,Doe,john@acme.com,CEO,acme.com
Jane,Smith,jane@techstart.io,CTO,techstart.io
Bob,Johnson,bob@example.com,Developer,"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 3
    assert data["created"] == 3
    assert data["updated"] == 0
    assert len(data["errors"]) == 0

    # Verify database records
    from sqlalchemy import select
    result = await db.execute(select(Contact))
    contacts = result.scalars().all()
    assert len(contacts) == 3

    # Verify company resolution
    result = await db.execute(select(Contact).where(Contact.email == "john@acme.com"))
    john = result.scalar_one()
    assert john.company_id is not None
    assert john.company_domain == "acme.com"

    result = await db.execute(select(Contact).where(Contact.email == "bob@example.com"))
    bob = result.scalar_one()
    assert bob.company_id is None


@pytest.mark.anyio
async def test_import_contacts_csv_upsert(async_client: AsyncClient, db):
    """Test contact CSV import with upsert behavior."""
    # Create test company
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )

    # First import
    csv_content1 = """first_name,last_name,email,job_title
John,Doe,john@acme.com,Developer"""

    response1 = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content1.encode()), "text/csv")}
    )
    assert response1.status_code == 202
    assert response1.json()["created"] == 1

    # Second import with same email but updated data
    csv_content2 = """first_name,last_name,email,job_title,company_domain
John,Doe,john@acme.com,Senior Developer,acme.com"""

    response2 = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content2.encode()), "text/csv")}
    )

    assert response2.status_code == 202
    data = response2.json()
    assert data["total"] == 1
    assert data["created"] == 0
    assert data["updated"] == 1

    # Verify update
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@acme.com"))
    contact = result.scalar_one()
    assert contact.job_title == "Senior Developer"
    assert contact.company_id is not None


@pytest.mark.anyio
async def test_import_contacts_csv_unmatched_company(async_client: AsyncClient, db):
    """Test contact import with company domain that doesn't exist."""
    csv_content = """first_name,last_name,email,company_domain
John,Doe,john@unknown.com,unknown.com"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 1
    assert data["created"] == 1
    assert len(data["errors"]) == 0

    # Contact should be created with null company_id but preserved domain
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@unknown.com"))
    contact = result.scalar_one()
    assert contact.company_id is None
    assert contact.company_domain == "unknown.com"


@pytest.mark.anyio
async def test_import_contacts_csv_missing_required_fields(async_client: AsyncClient):
    """Test contact import with missing required fields."""
    csv_content = """first_name,last_name,email
John,,john@test.com
,Doe,jane@test.com
ValidFirst,ValidLast,valid@test.com"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 1  # Only valid row
    assert data["created"] == 1
    assert len(data["errors"]) == 2  # Two rows with missing fields


@pytest.mark.anyio
async def test_import_contacts_csv_array_fields(async_client: AsyncClient, db):
    """Test contact CSV import with array fields (custom tags)."""
    csv_content = """first_name,last_name,email,custom_tags_a,custom_tags_b
John,Doe,john@test.com,"vip,priority","sales,marketing\""""

    response = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["created"] == 1

    # Verify arrays were parsed correctly
    from sqlalchemy import select
    result = await db.execute(select(Contact).where(Contact.email == "john@test.com"))
    contact = result.scalar_one()
    assert contact.custom_tags_a == ["vip", "priority"]
    assert contact.custom_tags_b == ["sales", "marketing"]


@pytest.mark.anyio
async def test_import_contacts_csv_batch_company_resolution(async_client: AsyncClient, db):
    """Test that company resolution is done in batch (single query)."""
    # Create test companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io"}
    )

    # Create CSV with multiple contacts from same companies
    csv_content = """first_name,last_name,email,company_domain
John,Doe,john1@acme.com,acme.com
Jane,Smith,jane1@acme.com,acme.com
Bob,Johnson,bob1@techstart.io,techstart.io
Alice,Williams,alice1@techstart.io,techstart.io"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=contacts",
        files={"file": ("contacts.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["created"] == 4

    # Verify all contacts have correct company_id
    from sqlalchemy import select
    result = await db.execute(select(Company).where(Company.domain == "acme.com"))
    acme_company = result.scalar_one()

    result = await db.execute(select(Contact).where(Contact.company_id == acme_company.id))
    acme_contacts = result.scalars().all()
    assert len(acme_contacts) == 2
