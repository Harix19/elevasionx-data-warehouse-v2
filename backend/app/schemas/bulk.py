"""Bulk operation schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Any
from datetime import datetime


class ImportError(BaseModel):
    """Error from a single row during import."""
    row: int
    error: str


class BulkImportResponse(BaseModel):
    """Response from CSV import operation."""
    total: int = Field(description="Total rows processed")
    created: int = Field(description="Number of new records created")
    updated: int = Field(description="Number of existing records updated")
    errors: list[ImportError] = Field(default_factory=list, description="List of errors encountered")


class RecordError(BaseModel):
    """Error from a single record during JSON bulk operation."""
    index: int
    record: dict[str, Any]
    error: str


class BulkCompanyRecord(BaseModel):
    """Single company record for bulk operations."""
    name: str
    domain: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    keywords: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    description: str | None = None
    country: str | None = None
    twitter_url: str | None = None
    facebook_url: str | None = None
    revenue: float | None = None
    funding_date: str | None = None
    custom_tags_a: list[str] = Field(default_factory=list)
    custom_tags_b: list[str] = Field(default_factory=list)
    custom_tags_c: list[str] = Field(default_factory=list)
    lead_source: str | None = None
    lead_score: int | None = None
    status: str | None = None


class BulkContactRecord(BaseModel):
    """Single contact record for bulk operations."""
    first_name: str
    last_name: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    working_company_name: str | None = None
    job_title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    company_domain: str | None = None
    company_linkedin_url: str | None = None
    custom_tags_a: list[str] = Field(default_factory=list)
    custom_tags_b: list[str] = Field(default_factory=list)
    custom_tags_c: list[str] = Field(default_factory=list)
    lead_source: str | None = None
    lead_score: int | None = None
    status: str | None = None


class BulkCompanyRequest(BaseModel):
    """Request for bulk company operations."""
    records: list[BulkCompanyRecord] = Field(
        ...,
        max_length=10000,
        description="List of company records (max 10,000)"
    )
    upsert: bool = Field(
        default=True,
        description="If true, update existing records; if false, skip duplicates"
    )

    @field_validator('records')
    @classmethod
    def validate_records_count(cls, v):
        if len(v) > 10000:
            raise ValueError("Maximum 10,000 records allowed per request")
        return v


class BulkContactRequest(BaseModel):
    """Request for bulk contact operations."""
    records: list[BulkContactRecord] = Field(
        ...,
        max_length=10000,
        description="List of contact records (max 10,000)"
    )
    upsert: bool = Field(
        default=True,
        description="If true, update existing records; if false, skip duplicates"
    )

    @field_validator('records')
    @classmethod
    def validate_records_count(cls, v):
        if len(v) > 10000:
            raise ValueError("Maximum 10,000 records allowed per request")
        return v


class BulkResult(BaseModel):
    """Result from bulk JSON operations."""
    total: int = Field(description="Total records processed")
    created: int = Field(description="Number of new records created")
    updated: int = Field(description="Number of existing records updated")
    skipped: int = Field(description="Number of records skipped (duplicates in insert-only mode)")
    errors: list[RecordError] = Field(default_factory=list, description="List of errors encountered")
