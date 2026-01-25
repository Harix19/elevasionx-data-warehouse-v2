"""Tests for streaming CSV export endpoints."""

import pytest
from httpx import AsyncClient
import csv
from io import StringIO

from app.models.company import Company
from app.models.contact import Contact


@pytest.mark.anyio
async def test_export_companies_all(async_client: AsyncClient, db):
    """Test exporting all companies as CSV."""
    # Create test companies
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io", "industry": "Software"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "DataCo", "domain": "dataco.com", "industry": "Analytics"}
    )

    response = await async_client.get("/api/v1/export/companies")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "companies-" in response.headers["content-disposition"]

    # Parse CSV
    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 3
    assert {row["name"] for row in rows} == {"Acme Corp", "TechStart", "DataCo"}


@pytest.mark.anyio
async def test_export_companies_filtered_by_industry(async_client: AsyncClient, db):
    """Test exporting companies filtered by industry."""
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io", "industry": "Software"}
    )

    response = await async_client.get("/api/v1/export/companies?industry=SaaS")

    assert response.status_code == 200

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 1
    assert rows[0]["name"] == "Acme Corp"
    assert rows[0]["industry"] == "SaaS"


@pytest.mark.anyio
async def test_export_companies_filtered_by_country(async_client: AsyncClient, db):
    """Test exporting companies filtered by country."""
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "country": "USA"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io", "country": "Canada"}
    )

    response = await async_client.get("/api/v1/export/companies?country=USA")

    assert response.status_code == 200

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 1
    assert rows[0]["name"] == "Acme Corp"


@pytest.mark.anyio
async def test_export_companies_column_selection(async_client: AsyncClient, db):
    """Test exporting companies with selected columns only."""
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "Acme Corp", "domain": "acme.com", "industry": "SaaS"}
    )
    await async_client.post(
        "/api/v1/companies/",
        json={"name": "TechStart", "domain": "techstart.io", "industry": "Software"}
    )

    response = await async_client.get("/api/v1/export/companies?columns=name,domain,industry")

    assert response.status_code == 200

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    # Verify only selected columns present
    assert set(rows[0].keys()) == {"name", "domain", "industry"}
    assert len(rows) == 2


@pytest.mark.anyio
async def test_export_companies_invalid_columns(async_client: AsyncClient):
    """Test export with invalid column names."""
    response = await async_client.get("/api/v1/export/companies?columns=name,invalid_column")

    assert response.status_code == 400
    assert "Invalid columns" in response.json()["detail"]


@pytest.mark.anyio
async def test_export_contacts_all(async_client: AsyncClient, db):
    """Test exporting all contacts as CSV."""
    # Create contacts
    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "John", "last_name": "Doe", "email": "john@acme.com"}
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={"first_name": "Jane", "last_name": "Smith", "email": "jane@test.com"}
    )

    response = await async_client.get("/api/v1/export/contacts")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "contacts-" in response.headers["content-disposition"]

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 2
    assert {row["email"] for row in rows} == {"john@acme.com", "jane@test.com"}


@pytest.mark.anyio
async def test_export_contacts_filtered_by_seniority(async_client: AsyncClient, db):
    """Test exporting contacts filtered by seniority level."""
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@acme.com",
            "seniority_level": "C-Level"
        }
    )
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
            "seniority_level": "Mid"
        }
    )

    response = await async_client.get("/api/v1/export/contacts?seniority_level=C-Level")

    assert response.status_code == 200

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 1
    assert rows[0]["email"] == "john@acme.com"


@pytest.mark.anyio
async def test_export_contacts_column_selection(async_client: AsyncClient, db):
    """Test exporting contacts with selected columns only."""
    await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "job_title": "CEO"
        }
    )

    response = await async_client.get(
        "/api/v1/export/contacts?columns=first_name,last_name,email,job_title"
    )

    assert response.status_code == 200

    csv_reader = csv.DictReader(StringIO(response.text))
    rows = list(csv_reader)

    assert set(rows[0].keys()) == {"first_name", "last_name", "email", "job_title"}
    assert len(rows) == 1
