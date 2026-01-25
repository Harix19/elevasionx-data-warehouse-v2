"""Bulk import endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.bulk import (
    BulkImportResponse,
    BulkCompanyRequest,
    BulkContactRequest,
    BulkResult,
)
from app.services.csv_service import import_companies_csv, import_contacts_csv
from app.services.bulk_service import bulk_create_companies, bulk_create_contacts


router = APIRouter()


@router.post("/import", response_model=BulkImportResponse, status_code=202)
async def import_csv(
    file: UploadFile = File(...),
    type: str = Query(..., description="Import type: 'companies' or 'contacts'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkImportResponse:
    """
    Import companies or contacts from CSV file.

    **CSV Format for Companies:**
    - name (required)
    - domain, linkedin_url, location, employee_count, industry, keywords,
      technologies, description, country, twitter_url, facebook_url, revenue,
      funding_date, custom_tags_a, custom_tags_b, custom_tags_c, lead_source,
      lead_score, status

    **CSV Format for Contacts:**
    - first_name, last_name (required)
    - full_name, email, phone, location, linkedin_url, working_company_name,
      job_title, seniority_level, department, company_domain, company_linkedin_url,
      custom_tags_a, custom_tags_b, custom_tags_c, lead_source, lead_score, status

    **Array fields:** comma-separated (e.g., "tag1,tag2,tag3")

    **Upsert behavior:**
    - Companies: upsert by domain
    - Contacts: upsert by email (requires migration 002)

    Returns 202 Accepted with import summary.
    """
    # Validate type
    if type not in ['companies', 'contacts']:
        raise HTTPException(
            status_code=400,
            detail="Invalid type. Must be 'companies' or 'contacts'"
        )

    # Validate CSV content type
    if file.content_type not in ['text/csv', 'application/csv', 'text/plain']:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Must be CSV"
        )

    # Read file content
    try:
        content = await file.read()
        file_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV encoding. File must be UTF-8"
        )

    # Route to appropriate importer
    if type == 'companies':
        result = import_companies_csv(db, file_content)
    else:  # contacts
        result = import_contacts_csv(db, file_content)

    return result


@router.post("/companies", response_model=BulkResult)
def bulk_companies(
    request: BulkCompanyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkResult:
    """
    Bulk create or update companies via JSON.

    **Max records:** 10,000 per request

    **Upsert mode (default):**
    - Updates existing records by domain
    - Creates new records for unknown domains

    **Insert-only mode (upsert=false):**
    - Skips duplicate domains
    - Only creates new records
    """
    return bulk_create_companies(db, request.records, request.upsert)


@router.post("/contacts", response_model=BulkResult)
def bulk_contacts(
    request: BulkContactRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkResult:
    """
    Bulk create or update contacts via JSON.

    **Max records:** 10,000 per request

    **Company resolution:** Automatically resolves company_id from company_domain

    **Upsert mode (default):**
    - Updates existing records by email
    - Creates new records for unknown emails

    **Insert-only mode (upsert=false):**
    - Skips duplicate emails
    - Only creates new records
    """
    return bulk_create_contacts(db, request.records, request.upsert)
