"""Streaming CSV export service."""

import csv
from io import StringIO
from typing import AsyncIterator
from datetime import datetime, date
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.contact import Contact


# Exportable company columns
COMPANY_EXPORT_COLUMNS = [
    'id', 'name', 'domain', 'linkedin_url', 'location', 'employee_count',
    'industry', 'keywords', 'technologies', 'description', 'country',
    'twitter_url', 'facebook_url', 'revenue', 'funding_date',
    'custom_tags_a', 'custom_tags_b', 'custom_tags_c', 'lead_source',
    'lead_score', 'status', 'created_at', 'updated_at'
]

# Exportable contact columns
CONTACT_EXPORT_COLUMNS = [
    'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
    'location', 'linkedin_url', 'working_company_name', 'job_title',
    'seniority_level', 'department', 'company_domain', 'company_linkedin_url',
    'custom_tags_a', 'custom_tags_b', 'custom_tags_c', 'lead_source',
    'lead_score', 'status', 'created_at', 'updated_at'
]


async def generate_companies_csv(
    db: Session,
    filters: dict,
    columns: list[str] | None = None
) -> AsyncIterator[str]:
    """
    Generate CSV export for companies with streaming.

    Args:
        db: Database session
        filters: Filter parameters (industry, country, status, etc.)
        columns: List of columns to export (defaults to all)

    Yields:
        CSV rows as strings
    """
    # Use provided columns or default to all
    export_columns = columns or COMPANY_EXPORT_COLUMNS

    # Build query with filters
    query = select(Company).where(Company.deleted_at.is_(None))
    query = _apply_company_filters(query, filters)

    # Yield CSV header
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=export_columns)
    writer.writeheader()
    yield output.getvalue()
    output.truncate(0)
    output.seek(0)

    # Stream results
    result = db.execute(query)
    for company in result.scalars():
        row_data = {}
        for col in export_columns:
            value = getattr(company, col, None)
            row_data[col] = _format_export_value(value)

        writer.writerow(row_data)
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)


async def generate_contacts_csv(
    db: Session,
    filters: dict,
    columns: list[str] | None = None
) -> AsyncIterator[str]:
    """
    Generate CSV export for contacts with streaming.

    Args:
        db: Database session
        filters: Filter parameters (seniority, department, status, etc.)
        columns: List of columns to export (defaults to all)

    Yields:
        CSV rows as strings
    """
    # Use provided columns or default to all
    export_columns = columns or CONTACT_EXPORT_COLUMNS

    # Build query with filters
    query = select(Contact).where(Contact.deleted_at.is_(None))
    query = _apply_contact_filters(query, filters)

    # Yield CSV header
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=export_columns)
    writer.writeheader()
    yield output.getvalue()
    output.truncate(0)
    output.seek(0)

    # Stream results
    result = db.execute(query)
    for contact in result.scalars():
        row_data = {}
        for col in export_columns:
            value = getattr(contact, col, None)
            row_data[col] = _format_export_value(value)

        writer.writerow(row_data)
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)


def _apply_company_filters(query, filters: dict):
    """Apply filters to company query."""
    if filters.get('industry'):
        query = query.where(Company.industry == filters['industry'])

    if filters.get('country'):
        query = query.where(Company.country == filters['country'])

    if filters.get('status'):
        query = query.where(Company.status == filters['status'])

    if filters.get('min_employee_count'):
        query = query.where(Company.employee_count >= filters['min_employee_count'])

    if filters.get('max_employee_count'):
        query = query.where(Company.employee_count <= filters['max_employee_count'])

    if filters.get('min_revenue'):
        query = query.where(Company.revenue >= filters['min_revenue'])

    if filters.get('max_revenue'):
        query = query.where(Company.revenue <= filters['max_revenue'])

    if filters.get('tags'):
        # Filter by any custom tags
        tags = filters['tags'].split(',')
        for tag in tags:
            query = query.where(
                Company.custom_tags_a.contains([tag]) |
                Company.custom_tags_b.contains([tag]) |
                Company.custom_tags_c.contains([tag])
            )

    return query


def _apply_contact_filters(query, filters: dict):
    """Apply filters to contact query."""
    if filters.get('seniority_level'):
        query = query.where(Contact.seniority_level == filters['seniority_level'])

    if filters.get('department'):
        query = query.where(Contact.department == filters['department'])

    if filters.get('status'):
        query = query.where(Contact.status == filters['status'])

    if filters.get('company_id'):
        query = query.where(Contact.company_id == filters['company_id'])

    if filters.get('tags'):
        # Filter by any custom tags
        tags = filters['tags'].split(',')
        for tag in tags:
            query = query.where(
                Contact.custom_tags_a.contains([tag]) |
                Contact.custom_tags_b.contains([tag]) |
                Contact.custom_tags_c.contains([tag])
            )

    return query


def _format_export_value(value) -> str:
    """Format a value for CSV export."""
    if value is None:
        return ''
    elif isinstance(value, list):
        # Join array values with commas
        return ','.join(str(v) for v in value)
    elif isinstance(value, (datetime, date)):
        # Format dates/timestamps as ISO strings
        return value.isoformat()
    elif isinstance(value, UUID):
        # Format UUIDs as strings
        return str(value)
    elif isinstance(value, bool):
        # Format booleans as strings
        return str(value).lower()
    else:
        return str(value)
