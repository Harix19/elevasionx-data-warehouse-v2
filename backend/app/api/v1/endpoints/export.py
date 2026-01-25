"""CSV export endpoints."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.export_service import (
    generate_companies_csv,
    generate_contacts_csv,
    COMPANY_EXPORT_COLUMNS,
    CONTACT_EXPORT_COLUMNS,
)


router = APIRouter()


@router.get("/companies")
async def export_companies(
    industry: str | None = None,
    country: str | None = None,
    status: str | None = None,
    min_employee_count: int | None = None,
    max_employee_count: int | None = None,
    min_revenue: float | None = None,
    max_revenue: float | None = None,
    tags: str | None = Query(None, description="Comma-separated tags"),
    columns: str | None = Query(None, description="Comma-separated column names"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export companies as streaming CSV.

    **Filters:**
    - industry: Filter by industry
    - country: Filter by country
    - status: Filter by lead status
    - min_employee_count, max_employee_count: Employee count range
    - min_revenue, max_revenue: Revenue range
    - tags: Comma-separated custom tags (matches any tag field)

    **Column Selection:**
    - columns: Comma-separated column names (defaults to all)
    - Available columns: id, name, domain, linkedin_url, location, employee_count,
      industry, keywords, technologies, description, country, twitter_url,
      facebook_url, revenue, funding_date, custom_tags_a, custom_tags_b,
      custom_tags_c, lead_source, lead_score, status, created_at, updated_at

    Returns streaming CSV file.
    """
    # Parse filters
    filters = {
        'industry': industry,
        'country': country,
        'status': status,
        'min_employee_count': min_employee_count,
        'max_employee_count': max_employee_count,
        'min_revenue': min_revenue,
        'max_revenue': max_revenue,
        'tags': tags,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    # Parse column selection
    column_list = None
    if columns:
        column_list = [col.strip() for col in columns.split(',')]
        # Validate columns
        invalid_cols = set(column_list) - set(COMPANY_EXPORT_COLUMNS)
        if invalid_cols:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Invalid columns: {', '.join(invalid_cols)}"
            )

    # Generate streaming response
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"companies-{timestamp}.csv"

    return StreamingResponse(
        generate_companies_csv(db, filters, column_list),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/contacts")
async def export_contacts(
    seniority_level: str | None = None,
    department: str | None = None,
    status: str | None = None,
    company_id: str | None = None,
    tags: str | None = Query(None, description="Comma-separated tags"),
    columns: str | None = Query(None, description="Comma-separated column names"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export contacts as streaming CSV.

    **Filters:**
    - seniority_level: Filter by seniority level
    - department: Filter by department
    - status: Filter by lead status
    - company_id: Filter by company UUID
    - tags: Comma-separated custom tags (matches any tag field)

    **Column Selection:**
    - columns: Comma-separated column names (defaults to all)
    - Available columns: id, first_name, last_name, full_name, email, phone,
      location, linkedin_url, working_company_name, job_title, seniority_level,
      department, company_domain, company_linkedin_url, custom_tags_a,
      custom_tags_b, custom_tags_c, lead_source, lead_score, status,
      created_at, updated_at

    Returns streaming CSV file.
    """
    # Parse filters
    filters = {
        'seniority_level': seniority_level,
        'department': department,
        'status': status,
        'company_id': company_id,
        'tags': tags,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    # Parse column selection
    column_list = None
    if columns:
        column_list = [col.strip() for col in columns.split(',')]
        # Validate columns
        invalid_cols = set(column_list) - set(CONTACT_EXPORT_COLUMNS)
        if invalid_cols:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Invalid columns: {', '.join(invalid_cols)}"
            )

    # Generate streaming response
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"contacts-{timestamp}.csv"

    return StreamingResponse(
        generate_contacts_csv(db, filters, column_list),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
