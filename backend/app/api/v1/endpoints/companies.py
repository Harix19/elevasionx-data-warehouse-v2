"""Company CRUD endpoints."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DB
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.schemas.contact import ContactListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(company_in: CompanyCreate, db: DB) -> Company:
    """Create a new company.

    Story 2.1: Create Company
    Story 2.2: Duplicate Detection (by domain)
    """
    # Check for duplicate domain if provided
    if company_in.domain:
        stmt = select(Company).where(
            Company.domain == company_in.domain,
            Company.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company with domain '{company_in.domain}' already exists",
            )

    # Create the company
    company_data = company_in.model_dump()
    # Handle None arrays - convert to empty lists for array columns
    for field in ["keywords", "technologies", "custom_tags_a", "custom_tags_b", "custom_tags_c"]:
        if company_data.get(field) is None:
            company_data[field] = []

    company = Company(**company_data)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
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
    industry: str | None = None,
    country: str | None = None,
    lead_status: str | None = None,
    # Range filters
    revenue_min: float | None = None,
    revenue_max: float | None = None,
    lead_score_min: int | None = None,
    lead_score_max: int | None = None,
    employee_count_min: int | None = None,
    employee_count_max: int | None = None,
) -> dict:
    """List companies with cursor-based pagination and filtering.

    Story 4.4: Cursor-Based Pagination
    Story 4.2: Tag-Based Filtering
    Story 4.3: Multi-Field and Range Filtering
    Uses composite key (created_at DESC, id ASC) for stable pagination.
    Excludes soft-deleted companies.

    Tag filters:
    - tags_a, tags_b, tags_c: Comma-separated tags for OR logic (any match)
    - tags_a_all, tags_b_all, tags_c_all: Comma-separated tags for AND logic (all must exist)

    String filters (case-insensitive):
    - industry, country, lead_status: Exact match filters

    Range filters:
    - revenue_min/max, lead_score_min/max, employee_count_min/max: Numeric range filters
    """
    from app.schemas.common import decode_cursor, encode_cursor
    from sqlalchemy import func, String, cast

    # Validate limit
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100",
        )

    # Validate range filters
    if revenue_min is not None and revenue_max is not None and revenue_min > revenue_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="revenue_min cannot be greater than revenue_max",
        )

    if lead_score_min is not None and lead_score_max is not None and lead_score_min > lead_score_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lead_score_min cannot be greater than lead_score_max",
        )

    if employee_count_min is not None and employee_count_max is not None and employee_count_min > employee_count_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="employee_count_min cannot be greater than employee_count_max",
        )

    # Build query with soft delete filter
    stmt = select(Company).where(Company.deleted_at.is_(None))

    # Apply string filters (case-insensitive)
    if industry:
        stmt = stmt.where(func.lower(Company.industry) == industry.lower())

    if country:
        stmt = stmt.where(func.lower(Company.country) == country.lower())

    if lead_status:
        # Cast ENUM to text before applying lower()
        stmt = stmt.where(func.lower(cast(Company.status, String)) == lead_status.lower())

    # Apply range filters
    if revenue_min is not None:
        stmt = stmt.where(Company.revenue >= revenue_min)

    if revenue_max is not None:
        stmt = stmt.where(Company.revenue <= revenue_max)

    if lead_score_min is not None:
        stmt = stmt.where(Company.lead_score >= lead_score_min)

    if lead_score_max is not None:
        stmt = stmt.where(Company.lead_score <= lead_score_max)

    if employee_count_min is not None:
        stmt = stmt.where(Company.employee_count >= employee_count_min)

    if employee_count_max is not None:
        stmt = stmt.where(Company.employee_count <= employee_count_max)

    # Apply tag filters - OR logic (overlap operator)
    if tags_a:
        tag_list = [tag.strip() for tag in tags_a.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_a.overlap(tag_list))

    if tags_b:
        tag_list = [tag.strip() for tag in tags_b.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_b.overlap(tag_list))

    if tags_c:
        tag_list = [tag.strip() for tag in tags_c.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_c.overlap(tag_list))

    # Apply tag filters - AND logic (contains operator)
    if tags_a_all:
        tag_list = [tag.strip() for tag in tags_a_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_a.contains(tag_list))

    if tags_b_all:
        tag_list = [tag.strip() for tag in tags_b_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_b.contains(tag_list))

    if tags_c_all:
        tag_list = [tag.strip() for tag in tags_c_all.split(",") if tag.strip()]
        if tag_list:
            stmt = stmt.where(Company.custom_tags_c.contains(tag_list))

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
        from sqlalchemy import or_, and_
        stmt = stmt.where(
            or_(
                Company.created_at < cursor_created_at,
                and_(
                    Company.created_at == cursor_created_at,
                    Company.id > cursor_id,
                ),
            )
        )

    # Order by composite key and fetch limit + 1 to check for more
    stmt = stmt.order_by(Company.created_at.desc(), Company.id.asc()).limit(limit + 1)

    result = await db.execute(stmt)
    companies = list(result.scalars().all())

    # Determine if there are more results
    has_more = len(companies) > limit
    if has_more:
        companies = companies[:limit]

    # Generate next cursor from last item if more results exist
    next_cursor = None
    if has_more and companies:
        last_company = companies[-1]
        next_cursor = encode_cursor(last_company.created_at, str(last_company.id))

    return {
        "items": companies,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": None,  # Expensive to compute; leave null
    }


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, db: DB) -> Company:
    """Get a single company by ID.

    Story 2.3: Read Company
    Returns 404 if company not found or soft-deleted.
    """
    stmt = select(Company).where(
        Company.id == company_id,
        Company.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_in: CompanyUpdate,
    db: DB,
) -> Company:
    """Update a company.

    Story 2.3: Update Company
    Story 2.5: Company Tagging (tags updated via this endpoint)
    """
    stmt = select(Company).where(
        Company.id == company_id,
        Company.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Check for duplicate domain if updating domain
    update_data = company_in.model_dump(exclude_unset=True)
    if "domain" in update_data and update_data["domain"]:
        stmt = select(Company).where(
            Company.domain == update_data["domain"],
            Company.id != company_id,
            Company.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company with domain '{update_data['domain']}' already exists",
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID, db: DB) -> None:
    """Soft delete a company.

    Story 2.4: Soft Delete
    Sets deleted_at timestamp instead of removing the record.
    """
    from datetime import datetime, timezone

    stmt = select(Company).where(
        Company.id == company_id,
        Company.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    company.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{company_id}/restore", response_model=CompanyResponse)
async def restore_company(company_id: UUID, db: DB) -> Company:
    """Restore a soft-deleted company.

    Story 2.4: Restore
    Clears the deleted_at timestamp.
    """
    # Note: We look for deleted companies here (deleted_at is NOT None)
    stmt = select(Company).where(
        Company.id == company_id,
        Company.deleted_at.is_not(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted company not found",
        )

    company.deleted_at = None
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/{company_id}/contacts", response_model=ContactListResponse)
async def list_company_contacts(
    company_id: UUID,
    db: DB,
    include_deleted: bool = False,
) -> dict:
    """List contacts for a company.

    Story 3.4: View Contacts for a Company
    Returns contacts linked to this company, ordered by created_at DESC.
    """
    # First validate company exists and is not deleted
    stmt = select(Company).where(
        Company.id == company_id,
        Company.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Query contacts for this company
    stmt = select(Contact).where(Contact.company_id == company_id)

    if not include_deleted:
        stmt = stmt.where(Contact.deleted_at.is_(None))

    stmt = stmt.order_by(Contact.created_at.desc())

    result = await db.execute(stmt)
    contacts = result.scalars().all()

    return {"items": contacts}
