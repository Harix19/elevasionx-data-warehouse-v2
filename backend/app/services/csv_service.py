"""CSV import service."""

import csv
from io import StringIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.bulk import BulkImportResponse, ImportError
from app.core.config import settings


def _parse_array(value: str) -> list[str]:
    """Parse comma-separated string into list."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


async def _upsert_companies_batch(db: AsyncSession, batch: list[dict]) -> tuple[int, int]:
    """
    Upsert a batch of companies using PostgreSQL INSERT ... ON CONFLICT.
    Returns (created_count, updated_count).
    """
    if not batch:
        return 0, 0

    # Get current count of records with domains in this batch
    domains = [r['domain'] for r in batch if r['domain']]
    existing_count = 0
    if domains:
        stmt = select(Company).filter(
            Company.domain.in_(domains),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        existing_count = len(result.scalars().all())

    # Perform upsert
    stmt = insert(Company).values(batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=['domain'],
        set_={
            'name': stmt.excluded.name,
            'linkedin_url': stmt.excluded.linkedin_url,
            'location': stmt.excluded.location,
            'employee_count': stmt.excluded.employee_count,
            'industry': stmt.excluded.industry,
            'keywords': stmt.excluded.keywords,
            'technologies': stmt.excluded.technologies,
            'description': stmt.excluded.description,
            'country': stmt.excluded.country,
            'twitter_url': stmt.excluded.twitter_url,
            'facebook_url': stmt.excluded.facebook_url,
            'revenue': stmt.excluded.revenue,
            'funding_date': stmt.excluded.funding_date,
            'custom_tags_a': stmt.excluded.custom_tags_a,
            'custom_tags_b': stmt.excluded.custom_tags_b,
            'custom_tags_c': stmt.excluded.custom_tags_c,
            'lead_source': stmt.excluded.lead_source,
            'lead_score': stmt.excluded.lead_score,
            'status': stmt.excluded.status,
        }
    )

    await db.execute(stmt)
    await db.commit()

    created = len(batch) - existing_count
    updated = existing_count

    return created, updated


async def _upsert_contacts_batch(db: AsyncSession, batch: list[dict], domains: set[str]) -> tuple[int, int]:
    """
    Upsert a batch of contacts using PostgreSQL INSERT ... ON CONFLICT.
    Resolves company_id from company_domain.
    Returns (created_count, updated_count).
    """
    if not batch:
        return 0, 0

    # Resolve company IDs from domains (single query)
    domain_to_company = {}
    if domains:
        stmt = select(Company.id, Company.domain).filter(
            Company.domain.in_(list(domains)),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        companies = result.all()
        domain_to_company = {c.domain: c.id for c in companies}

    # Add company_id to each record
    for record in batch:
        if record.get('company_domain') and record['company_domain'] in domain_to_company:
            record['company_id'] = domain_to_company[record['company_domain']]
        else:
            record['company_id'] = None

    # Get current count of records with emails in this batch
    emails = [r['email'] for r in batch if r['email']]
    existing_count = 0
    if emails:
        stmt = select(Contact).filter(
            Contact.email.in_(emails),
            Contact.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        existing_count = len(result.scalars().all())

    # Perform upsert
    stmt = insert(Contact).values(batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=['email'],
        set_={
            'first_name': stmt.excluded.first_name,
            'last_name': stmt.excluded.last_name,
            'full_name': stmt.excluded.full_name,
            'phone': stmt.excluded.phone,
            'location': stmt.excluded.location,
            'linkedin_url': stmt.excluded.linkedin_url,
            'working_company_name': stmt.excluded.working_company_name,
            'job_title': stmt.excluded.job_title,
            'seniority_level': stmt.excluded.seniority_level,
            'department': stmt.excluded.department,
            'company_id': stmt.excluded.company_id,
            'company_domain': stmt.excluded.company_domain,
            'company_linkedin_url': stmt.excluded.company_linkedin_url,
            'custom_tags_a': stmt.excluded.custom_tags_a,
            'custom_tags_b': stmt.excluded.custom_tags_b,
            'custom_tags_c': stmt.excluded.custom_tags_c,
            'lead_source': stmt.excluded.lead_source,
            'lead_score': stmt.excluded.lead_score,
            'status': stmt.excluded.status,
        }
    )

    await db.execute(stmt)
    await db.commit()

    created = len(batch) - existing_count
    updated = existing_count

    return created, updated


async def import_companies_csv(db: AsyncSession, file_content: str) -> BulkImportResponse:
    """
    Import companies from CSV content.

    CSV columns: name, domain, linkedin_url, location, employee_count, industry,
                 keywords, technologies, description, country, twitter_url,
                 facebook_url, revenue, funding_date, custom_tags_a, custom_tags_b,
                 custom_tags_c, lead_source, lead_score, status

    Upserts by domain (unique key).
    """
    reader = csv.DictReader(StringIO(file_content))

    total = 0
    created = 0
    updated = 0
    errors: list[ImportError] = []

    batch = []

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
        try:
            # Parse row data
            record = {
                'name': row.get('name', '').strip(),
                'domain': row.get('domain', '').strip() or None,
                'linkedin_url': row.get('linkedin_url', '').strip() or None,
                'location': row.get('location', '').strip() or None,
                'employee_count': int(row.get('employee_count', 0)) if row.get('employee_count', '').strip() else None,
                'industry': row.get('industry', '').strip() or None,
                'keywords': _parse_array(row.get('keywords', '')),
                'technologies': _parse_array(row.get('technologies', '')),
                'description': row.get('description', '').strip() or None,
                'country': row.get('country', '').strip() or None,
                'twitter_url': row.get('twitter_url', '').strip() or None,
                'facebook_url': row.get('facebook_url', '').strip() or None,
                'revenue': float(row.get('revenue', 0)) if row.get('revenue', '').strip() else None,
                'funding_date': row.get('funding_date', '').strip() or None,
                'custom_tags_a': _parse_array(row.get('custom_tags_a', '')),
                'custom_tags_b': _parse_array(row.get('custom_tags_b', '')),
                'custom_tags_c': _parse_array(row.get('custom_tags_c', '')),
                'lead_source': row.get('lead_source', '').strip() or None,
                'lead_score': int(row.get('lead_score', 0)) if row.get('lead_score', '').strip() else None,
                'status': row.get('status', '').strip() or 'new',
            }

            # Validate required fields
            if not record['name']:
                errors.append(ImportError(row=row_num, error="Missing required field: name"))
                continue

            batch.append(record)
            total += 1

            # Process batch when full
            if len(batch) >= settings.CSV_IMPORT_BATCH_SIZE:
                batch_created, batch_updated = await _upsert_companies_batch(db, batch)
                created += batch_created
                updated += batch_updated
                batch = []

        except Exception as e:
            errors.append(ImportError(row=row_num, error=str(e)))

    # Process remaining batch
    if batch:
        batch_created, batch_updated = await _upsert_companies_batch(db, batch)
        created += batch_created
        updated += batch_updated

    return BulkImportResponse(
        total=total,
        created=created,
        updated=updated,
        errors=errors
    )


async def import_contacts_csv(db: AsyncSession, file_content: str) -> BulkImportResponse:
    """
    Import contacts from CSV content.

    CSV columns: first_name, last_name, full_name, email, phone, location,
                 linkedin_url, working_company_name, job_title, seniority_level,
                 department, company_domain, company_linkedin_url, custom_tags_a,
                 custom_tags_b, custom_tags_c, lead_source, lead_score, status

    Upserts by email (unique key).
    Resolves company_id from company_domain.
    """
    reader = csv.DictReader(StringIO(file_content))

    total = 0
    created = 0
    updated = 0
    errors: list[ImportError] = []

    batch = []
    domains_in_batch = set()

    for row_num, row in enumerate(reader, start=2):
        try:
            company_domain = row.get('company_domain', '').strip() or None
            if company_domain:
                domains_in_batch.add(company_domain)

            record = {
                'first_name': row.get('first_name', '').strip(),
                'last_name': row.get('last_name', '').strip(),
                'full_name': row.get('full_name', '').strip() or None,
                'email': row.get('email', '').strip() or None,
                'phone': row.get('phone', '').strip() or None,
                'location': row.get('location', '').strip() or None,
                'linkedin_url': row.get('linkedin_url', '').strip() or None,
                'working_company_name': row.get('working_company_name', '').strip() or None,
                'job_title': row.get('job_title', '').strip() or None,
                'seniority_level': row.get('seniority_level', '').strip() or None,
                'department': row.get('department', '').strip() or None,
                'company_domain': company_domain,
                'company_linkedin_url': row.get('company_linkedin_url', '').strip() or None,
                'custom_tags_a': _parse_array(row.get('custom_tags_a', '')),
                'custom_tags_b': _parse_array(row.get('custom_tags_b', '')),
                'custom_tags_c': _parse_array(row.get('custom_tags_c', '')),
                'lead_source': row.get('lead_source', '').strip() or None,
                'lead_score': int(row.get('lead_score', 0)) if row.get('lead_score', '').strip() else None,
                'status': row.get('status', '').strip() or 'new',
            }

            # Validate required fields
            if not record['first_name'] or not record['last_name']:
                errors.append(ImportError(row=row_num, error="Missing required fields: first_name, last_name"))
                continue

            batch.append(record)
            total += 1

            # Process batch when full
            if len(batch) >= settings.CSV_IMPORT_BATCH_SIZE:
                batch_created, batch_updated = await _upsert_contacts_batch(db, batch, domains_in_batch)
                created += batch_created
                updated += batch_updated
                batch = []
                domains_in_batch = set()

        except Exception as e:
            errors.append(ImportError(row=row_num, error=str(e)))

    # Process remaining batch
    if batch:
        batch_created, batch_updated = await _upsert_contacts_batch(db, batch, domains_in_batch)
        created += batch_created
        updated += batch_updated

    return BulkImportResponse(
        total=total,
        created=created,
        updated=updated,
        errors=errors
    )
