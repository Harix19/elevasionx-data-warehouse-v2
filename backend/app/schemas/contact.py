"""Contact Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.lead_status import LeadStatus


class ContactBase(BaseModel):
    """Base contact schema with common fields."""

    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    job_title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    custom_tags_a: list[str] | None = None
    custom_tags_b: list[str] | None = None
    custom_tags_c: list[str] | None = None
    lead_source: str | None = None
    lead_score: int | None = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""

    company_id: UUID | None = None


class ContactUpdate(BaseModel):
    """Schema for updating a contact (all fields optional)."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    job_title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    custom_tags_a: list[str] | None = None
    custom_tags_b: list[str] | None = None
    custom_tags_c: list[str] | None = None
    lead_source: str | None = None
    lead_score: int | None = None
    status: LeadStatus | None = None
    company_id: UUID | None = None


class ContactResponse(ContactBase):
    """Schema for contact response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None = None
    full_name: str | None = None
    working_company_name: str | None = None
    company_domain: str | None = None
    company_linkedin_url: str | None = None
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ContactListResponse(BaseModel):
    """Schema for list of contacts response."""

    items: list[ContactResponse]
