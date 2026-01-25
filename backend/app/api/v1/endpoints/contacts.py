"""Contact CRUD endpoints."""

from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, or_, and_

from app.api.deps import DB
from app.models.contact import Contact
from app.models.company import Company
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.schemas.common import PaginatedResponse, decode_cursor, encode_cursor

router = APIRouter()


async def _populate_company_snapshots(contact: Contact, company: Company) -> None:
    """Populate contact's company snapshot fields from the linked company."""
    contact.working_company_name = company.name
    contact.company_domain = company.domain
    contact.company_linkedin_url = company.linkedin_url


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact_in: ContactCreate, db: DB) -> Contact:
    """Create a new contact.

    Story 3.1: Create Contact with Company Link
    - Auto-generates full_name from first_name + last_name
    - If company_id provided, validates company exists and populates snapshots
    """
    # Validate company exists if company_id provided
    company = None
    if contact_in.company_id:
        stmt = select(Company).where(
            Company.id == contact_in.company_id,
            Company.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

    # Create the contact
    contact_data = contact_in.model_dump()

    # Auto-generate full_name
    contact_data["full_name"] = f"{contact_data['first_name']} {contact_data['last_name']}"

    # Handle None arrays - convert to empty lists for array columns
    for field in ["custom_tags_a", "custom_tags_b", "custom_tags_c"]:
        if contact_data.get(field) is None:
            contact_data[field] = []

    contact = Contact(**contact_data)

    # Populate company snapshots if company exists
    if company:
        await _populate_company_snapshots(contact, company)

    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    db: DB,
    limit: int = 20,
    cursor: str | None = None,
    # Tag filters - OR logic (any tag matches)
    tags_a: str | None = None,
    tags_b: str | None = None,
    tags_c: str | None = None,
    # Tag filters - AND logic (all tags must exist)
    tags_a_all: str | None = None,
    tags_b_all: str | None = None,
    tags_c_all: str | None = None,
    # String filters (case-insensitive)
    seniority_level: str | None = None,
    department: str | None = None,
    lead_status: str | None = None,
    # Range filters
    lead_score_min: int | None = None,
    lead_score_max: int | None = None,
) -> dict:
    """List contacts with cursor-based pagination and filtering.

    Story 4.4: Cursor-Based Pagination
    Story 4.2: Tag-Based Filtering
    Story 4.3: Multi-Field and Range Filtering
    Uses composite key (created_at DESC, id ASC) for stable pagination.
    Excludes soft-deleted contacts.

    Tag filters:
    - tags_a, tags_b, tags_c: Comma-separated tags for OR logic (any match)
    - tags_a_all, tags_b_all, tags_c_all: Comma-separated tags for AND logic (all must exist)

    String filters (case-insensitive):
    - seniority_level, department, lead_status: Exact match filters

    Range filters:
    - lead_score_min/max: Numeric range filters
    """
    from sqlalchemy import func, String, cast

    # Validate limit
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100",
        )

    # Validate range filters
    if lead_score_min is not None and lead_score_max is not None and lead_score_min > lead_score_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_score_min cannot be greater than lead_score_max",
        )

    # Build query with soft delete filter
    stmt = select(Contact).where(Contact.deleted_at.is_(None))

    # Apply string filters (case-insensitive)
    if seniority_level:
        stmt = stmt.where(func.lower(Contact.seniority_level) == seniority_level.lower())

    if department:
        stmt = stmt.where(func.lower(Contact.department) == department.lower())

    if lead_status:
        # Cast ENUM to text before applying lower()
        stmt = stmt.where(func.lower(cast(Contact.status, String)) == lead_status.lower())

    # Apply range filters
    if lead_score_min is not None:
        stmt = stmt.where(Contact.lead_score >= lead_score_min)

    if lead_score_max is not None:
        stmt = stmt.where(Contact.lead_score <= lead_score_max)

    # Apply tag filters - OR logic (overlap operator)
    if tags_a:
        tag_list = [tag.strip() for tag in tags_a.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_a.overlap(tag_list))

    if tags_b:
        tag_list = [tag.strip() for tag in tags_b.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_b.overlap(tag_list))

    if tags_c:
        tag_list = [tag.strip() for tag in tags_c.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_c.overlap(tag_list))

    # Apply tag filters - AND logic (contains operator)
    if tags_a_all:
        tag_list = [tag.strip() for tag in tags_a_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_a.contains(tag_list))

    if tags_b_all:
        tag_list = [tag.strip() for tag in tags_b_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_b.contains(tag_list))

    if tags_c_all:
        tag_list = [tag.strip() for tag in tags_c_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Contact.custom_tags_c.contains(tag_list))

    # Apply cursor filtering if provided
    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format",
            )
        cursor_created_at, cursor_id = cursor_data

        # Continue from cursor using composite key
        # For DESC created_at, we want created_at < cursor OR (created_at = cursor AND id > cursor_id)
        stmt = stmt.where(
            or_(
                Contact.created_at < cursor_created_at,
                and_(
                    Contact.created_at == cursor_created_at,
                    Contact.id > cursor_id,
                ),
            )
        )

    # Order by composite key and fetch limit + 1 to check for more
    stmt = stmt.order_by(Contact.created_at.desc(), Contact.id.asc()).limit(limit + 1)

    result = await db.execute(stmt)
    contacts = list(result.scalars().all())

    # Determine if there are more results
    has_more = len(contacts) > limit
    if has_more:
        contacts = contacts[:limit]

    # Generate next cursor from last item if more results exist
    next_cursor = None
    if has_more and contacts:
        last_contact = contacts[-1]
        next_cursor = encode_cursor(last_contact.created_at, str(last_contact.id))

    return {
        "items": contacts,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": None,  # Expensive to compute; leave null
    }


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: UUID, db: DB) -> Contact:
    """Get a single contact by ID.

    Story 3.2: Read Contact
    Returns 404 if contact not found or soft-deleted.
    """
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    contact_in: ContactUpdate,
    db: DB,
) -> Contact:
    """Update a contact.

    Story 3.2: Update Contact
    Story 3.5: Contact Tagging (tags updated via this endpoint)
    - Regenerates full_name if first_name or last_name changed
    - Updates company snapshots if company_id changed
    """
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    update_data = contact_in.model_dump(exclude_unset=True)

    # Check if company_id is being updated
    if "company_id" in update_data:
        new_company_id = update_data["company_id"]
        if new_company_id is not None:
            stmt = select(Company).where(
                Company.id == new_company_id,
                Company.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            company = result.scalar_one_or_none()
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found",
                )
            # Update company snapshots
            await _populate_company_snapshots(contact, company)
        else:
            # Clear company snapshots if company_id set to None
            contact.working_company_name = None
            contact.company_domain = None
            contact.company_linkedin_url = None

    # Apply updates
    for field, value in update_data.items():
        setattr(contact, field, value)

    # Regenerate full_name if first_name or last_name changed
    if "first_name" in update_data or "last_name" in update_data:
        contact.full_name = f"{contact.first_name} {contact.last_name}"

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: UUID, db: DB) -> None:
    """Soft delete a contact.

    Story 3.3: Soft Delete
    Sets deleted_at timestamp instead of removing the record.
    """
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    contact.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{contact_id}/restore", response_model=ContactResponse)
async def restore_contact(contact_id: UUID, db: DB) -> Contact:
    """Restore a soft-deleted contact.

    Story 3.3: Restore
    Clears the deleted_at timestamp.
    Returns 400 if contact is not deleted.
    """
    # First check if contact exists at all
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if contact.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact is not deleted",
        )

    contact.deleted_at = None
    await db.commit()
    await db.refresh(contact)
    return contact
