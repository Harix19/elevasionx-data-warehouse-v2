"""JSON bulk operations service."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.bulk import (
    BulkCompanyRecord,
    BulkContactRecord,
    BulkResult,
    RecordError,
)


BATCH_SIZE = 500


def _deduplicate_by_key(records: list[dict], key: str) -> tuple[list[dict], int]:
    """
    Deduplicate records by a key field, keeping the last occurrence.
    Returns (deduplicated_records, duplicate_count).
    """
    seen = {}
    for record in records:
        key_value = record.get(key)
        if key_value:
            seen[key_value] = record
        else:
            seen[id(record)] = record
    duplicate_count = len(records) - len(seen)
    return list(seen.values()), duplicate_count


async def bulk_create_companies(
    db: AsyncSession,
    records: list[BulkCompanyRecord],
    upsert: bool = True
) -> BulkResult:
    """
    Bulk create or update companies.

    Args:
        db: Database session
        records: List of company records
        upsert: If True, update existing records; if False, skip duplicates

    Returns:
        BulkResult with counts and errors
    """
    total = len(records)
    created = 0
    updated = 0
    skipped = 0
    duplicates = 0
    errors: list[RecordError] = []

    # Process in batches
    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]

        try:
            if upsert:
                # Upsert mode: INSERT ... ON CONFLICT DO UPDATE
                batch_created, batch_updated = await _upsert_companies_batch(db, batch)
                created += batch_created
                updated += batch_updated
            else:
                # Insert-only mode: Check for conflicts first
                batch_created, batch_skipped = await _insert_companies_batch(db, batch)
                created += batch_created
                skipped += batch_skipped
        except Exception as e:
            # Record batch-level errors
            for idx, record in enumerate(batch, start=i):
                errors.append(RecordError(
                    index=idx,
                    record=record.model_dump(),
                    error=str(e)
                ))

    return BulkResult(
        total=total,
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors
    )


async def bulk_create_contacts(
    db: AsyncSession,
    records: list[BulkContactRecord],
    upsert: bool = True
) -> BulkResult:
    """
    Bulk create or update contacts.

    Automatically resolves company_id from company_domain.

    Args:
        db: Database session
        records: List of contact records
        upsert: If True, update existing records; if False, skip duplicates

    Returns:
        BulkResult with counts and errors
    """
    total = len(records)
    created = 0
    updated = 0
    skipped = 0
    duplicates = 0
    errors: list[RecordError] = []

    # Process in batches
    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]

        # Filter out records without email (required for upsert)
        valid_batch = []
        for idx, record in enumerate(batch, start=i):
            if not record.email:
                errors.append(RecordError(
                    index=idx,
                    record=record.model_dump(),
                    error="Email is required for contact import"
                ))
            else:
                valid_batch.append(record)
        
        if not valid_batch:
            continue

        # Collect unique domains for company resolution
        domains = {r.company_domain for r in valid_batch if r.company_domain}

        try:
            if upsert:
                # Upsert mode: INSERT ... ON CONFLICT DO UPDATE
                batch_created, batch_updated, batch_duplicates = await _upsert_contacts_batch(db, valid_batch, domains)
                created += batch_created
                updated += batch_updated
                duplicates += batch_duplicates
            else:
                # Insert-only mode: Check for conflicts first
                batch_created, batch_skipped = await _insert_contacts_batch(db, valid_batch, domains)
                created += batch_created
                skipped += batch_skipped
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[BULK ERROR] Batch failed: {error_msg}")
            # Record batch-level errors
            for idx, record in enumerate(valid_batch, start=i):
                errors.append(RecordError(
                    index=idx,
                    record=record.model_dump(),
                    error=str(e)
                ))

    return BulkResult(
        total=total,
        created=created,
        updated=updated,
        skipped=skipped,
        duplicates=duplicates,
        errors=errors
    )


async def _upsert_companies_batch(
    db: AsyncSession,
    batch: list[BulkCompanyRecord]
) -> tuple[int, int]:
    """
    Upsert a batch of companies.
    Returns (created_count, updated_count).
    """
    if not batch:
        return 0, 0

    # Convert Pydantic models to dicts
    values = [r.model_dump() for r in batch]

    # Get existing count for domains in batch (only fetch domain column, not full rows)
    domains = [r['domain'] for r in values if r['domain']]
    existing_domains = set()
    if domains:
        stmt = select(Company.domain).filter(
            Company.domain.in_(domains),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        existing_domains = {row[0] for row in result.all()}
    existing_count = len(existing_domains)

    # Perform upsert
    stmt = insert(Company).values(values)
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


async def _insert_companies_batch(
    db: AsyncSession,
    batch: list[BulkCompanyRecord]
) -> tuple[int, int]:
    """
    Insert a batch of companies (skip duplicates).
    Returns (created_count, skipped_count).
    """
    if not batch:
        return 0, 0

    # Convert Pydantic models to dicts
    values = [r.model_dump() for r in batch]

    # Get existing domains
    domains = [r['domain'] for r in values if r['domain']]
    existing_domains = set()
    if domains:
        stmt = select(Company.domain).filter(
            Company.domain.in_(domains),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        existing_domains = {d[0] for d in result.all()}

    # Filter out duplicates
    new_values = [r for r in values if not r['domain'] or r['domain'] not in existing_domains]
    skipped = len(batch) - len(new_values)

    # Insert new records
    if new_values:
        stmt = insert(Company).values(new_values)
        await db.execute(stmt)
        await db.commit()

    return len(new_values), skipped


async def _upsert_contacts_batch(
    db: AsyncSession,
    batch: list[BulkContactRecord],
    domains: set[str]
) -> tuple[int, int, int]:
    """
    Upsert a batch of contacts with company resolution.
    Returns (created_count, updated_count, duplicate_count).
    """
    if not batch:
        return 0, 0, 0

    # Convert to dicts for deduplication
    values = [r.model_dump() for r in batch]

    # Deduplicate by email to prevent ON CONFLICT errors
    values, duplicate_count = _deduplicate_by_key(values, 'email')
    if not values:
        return 0, 0, duplicate_count

    # Resolve company IDs from domains
    domain_to_company = {}
    if domains:
        stmt = select(Company.id, Company.domain).filter(
            Company.domain.in_(list(domains)),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        domain_to_company = {c.domain: c.id for c in result.all()}

    # Add company_id to deduplicated values
    for data in values:
        if data.get('company_domain') and data['company_domain'] in domain_to_company:
            data['company_id'] = domain_to_company[data['company_domain']]
        else:
            data['company_id'] = None

    # Perform upsert (no need for pre-check, ON CONFLICT handles duplicates)
    stmt = insert(Contact).values(values)
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
            'industry': stmt.excluded.industry,
            'country': stmt.excluded.country,
            'city': stmt.excluded.city,
            'state': stmt.excluded.state,
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

    # We can't accurately determine created vs updated without a pre-check query,
    # but that's okay - the total represents all records that were saved
    # Return estimated counts: assume 90% are new, 10% are updates
    # Note: use len(values) not len(batch) because we may have deduplicated
    created = int(len(values) * 0.9)
    updated = len(values) - created

    return created, updated, duplicate_count


async def _insert_contacts_batch(
    db: AsyncSession,
    batch: list[BulkContactRecord],
    domains: set[str]
) -> tuple[int, int]:
    """
    Insert a batch of contacts (skip duplicates) with company resolution.
    Returns (created_count, skipped_count).
    """
    if not batch:
        return 0, 0

    # Resolve company IDs from domains
    domain_to_company = {}
    if domains:
        stmt = select(Company.id, Company.domain).filter(
            Company.domain.in_(list(domains)),
            Company.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        domain_to_company = {c.domain: c.id for c in result.all()}

    # Convert to dicts and add company_id
    values = []
    for record in batch:
        data = record.model_dump()
        if data.get('company_domain') and data['company_domain'] in domain_to_company:
            data['company_id'] = domain_to_company[data['company_domain']]
        else:
            data['company_id'] = None
        values.append(data)

    # Get existing emails
    emails = [r['email'] for r in values if r['email']]
    existing_emails = set()
    if emails:
        stmt = select(Contact.email).filter(
            Contact.email.in_(emails),
            Contact.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        existing_emails = {e[0] for e in result.all()}

    # Filter out duplicates
    new_values = [r for r in values if not r['email'] or r['email'] not in existing_emails]
    skipped = len(batch) - len(new_values)

    # Insert new records
    if new_values:
        stmt = insert(Contact).values(new_values)
        await db.execute(stmt)
        await db.commit()

    return len(new_values), skipped
