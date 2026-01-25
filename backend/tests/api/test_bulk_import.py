"""Tests for CSV bulk import endpoints."""

import pytest
from httpx import AsyncClient
from io import BytesIO

from app.models.company import Company


@pytest.mark.anyio
async def test_import_companies_csv_success(async_client: AsyncClient, db):
    """Test successful company CSV import."""
    csv_content = """name,domain,industry,country,employee_count
Acme Corp,acme.com,SaaS,USA,50
TechStart,techstart.io,Software,Canada,25
DataCo,dataco.com,Analytics,UK,100"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=companies",
        files={"file": ("companies.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 3
    assert data["created"] == 3
    assert data["updated"] == 0
    assert len(data["errors"]) == 0

    # Verify database records
    from sqlalchemy import select
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    assert len(companies) == 3
    assert {c.name for c in companies} == {"Acme Corp", "TechStart", "DataCo"}


@pytest.mark.anyio
async def test_import_companies_csv_upsert(async_client: AsyncClient, db):
    """Test company CSV import with upsert behavior."""
    # First import
    csv_content1 = """name,domain,industry
Acme Corp,acme.com,SaaS"""

    response1 = await async_client.post(
        "/api/v1/bulk/import?type=companies",
        files={"file": ("companies.csv", BytesIO(csv_content1.encode()), "text/csv")}
    )
    assert response1.status_code == 202
    assert response1.json()["created"] == 1

    # Second import with same domain but updated data
    csv_content2 = """name,domain,industry,country
Acme Corporation,acme.com,Technology,USA"""

    response2 = await async_client.post(
        "/api/v1/bulk/import?type=companies",
        files={"file": ("companies.csv", BytesIO(csv_content2.encode()), "text/csv")}
    )

    assert response2.status_code == 202
    data = response2.json()
    assert data["total"] == 1
    assert data["created"] == 0
    assert data["updated"] == 1

    # Verify update
    from sqlalchemy import select
    result = await db.execute(select(Company).where(Company.domain == "acme.com"))
    company = result.scalar_one()
    assert company.name == "Acme Corporation"
    assert company.industry == "Technology"
    assert company.country == "USA"


@pytest.mark.anyio
async def test_import_companies_csv_partial_errors(async_client: AsyncClient, db):
    """Test CSV import with some invalid rows."""
    csv_content = """name,domain,industry
Acme Corp,acme.com,SaaS
,invalid.com,Tech
ValidCo,valid.com,Software"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=companies",
        files={"file": ("companies.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["total"] == 2  # Only valid rows counted
    assert data["created"] == 2
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 3  # Row with missing name
    assert "name" in data["errors"][0]["error"].lower()


@pytest.mark.anyio
async def test_import_companies_csv_invalid_type(async_client: AsyncClient):
    """Test CSV import with invalid type parameter."""
    csv_content = """name,domain
Test,test.com"""

    response = await async_client.post(
        "/api/v1/bulk/import?type=invalid",
        files={"file": ("companies.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 400
    assert "Invalid type" in response.json()["detail"]


@pytest.mark.anyio
async def test_import_companies_csv_array_fields(async_client: AsyncClient, db):
    """Test CSV import with array fields (keywords, technologies, tags)."""
    csv_content = """name,domain,keywords,technologies,custom_tags_a
Acme,acme.com,"ai,ml,data","python,aws,docker","tag1,tag2,tag3\""""

    response = await async_client.post(
        "/api/v1/bulk/import?type=companies",
        files={"file": ("companies.csv", BytesIO(csv_content.encode()), "text/csv")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["created"] == 1

    # Verify arrays were parsed correctly
    from sqlalchemy import select
    result = await db.execute(select(Company).where(Company.domain == "acme.com"))
    company = result.scalar_one()
    assert company.keywords == ["ai", "ml", "data"]
    assert company.technologies == ["python", "aws", "docker"]
    assert company.custom_tags_a == ["tag1", "tag2", "tag3"]
