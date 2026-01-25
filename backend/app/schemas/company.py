"""Company Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.lead_status import LeadStatus


class CompanyBase(BaseModel):
    """Base company schema with common fields."""

    name: str
    domain: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    keywords: list[str] | None = None
    technologies: list[str] | None = None
    description: str | None = None
    country: str | None = None
    twitter_url: str | None = None
    facebook_url: str | None = None
    revenue: float | None = None
    funding_date: date | None = None
    funding_data: dict | None = None
    custom_tags_a: list[str] | None = None
    custom_tags_b: list[str] | None = None
    custom_tags_c: list[str] | None = None
    lead_source: str | None = None
    lead_score: int | None = None

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, v: str | None) -> str | None:
        """Normalize domain to lowercase and treat empty string as None."""
        if v is None or v == "":
            return None
        return v.lower().strip()


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""

    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company (all fields optional)."""

    name: str | None = None
    domain: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    keywords: list[str] | None = None
    technologies: list[str] | None = None
    description: str | None = None
    country: str | None = None
    twitter_url: str | None = None
    facebook_url: str | None = None
    revenue: float | None = None
    funding_date: date | None = None
    funding_data: dict | None = None
    custom_tags_a: list[str] | None = None
    custom_tags_b: list[str] | None = None
    custom_tags_c: list[str] | None = None
    lead_source: str | None = None
    lead_score: int | None = None
    status: LeadStatus | None = None

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, v: str | None) -> str | None:
        """Normalize domain to lowercase and treat empty string as None."""
        if v is None or v == "":
            return None
        return v.lower().strip()


class CompanyResponse(CompanyBase):
    """Schema for company response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    last_contacted_at: datetime | None = None
    deleted_at: datetime | None = None
