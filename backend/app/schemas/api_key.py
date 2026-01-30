"""API key Pydantic schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.api_key import AccessLevel


class APIKeyBase(BaseModel):
    """Base API key schema with common fields."""
    
    name: str
    access_level: AccessLevel = AccessLevel.READ
    rate_limit: int = Field(default=1000, ge=1, le=10000)


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""
    
    @field_validator('rate_limit')
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Ensure rate limit is within acceptable range."""
        if v < 1:
            raise ValueError("Rate limit must be at least 1 request per minute")
        if v > 10000:
            raise ValueError("Rate limit cannot exceed 10000 requests per minute")
        return v


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    
    name: str | None = None
    access_level: AccessLevel | None = None
    rate_limit: int | None = Field(default=None, ge=1, le=10000)
    is_active: bool | None = None
    
    @field_validator('rate_limit')
    @classmethod
    def validate_rate_limit(cls, v: int | None) -> int | None:
        """Ensure rate limit is within acceptable range if provided."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("Rate limit must be at least 1 request per minute")
        if v > 10000:
            raise ValueError("Rate limit cannot exceed 10000 requests per minute")
        return v


class APIKeyResponse(BaseModel):
    """Schema for API key response (masked - never shows full key)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    key_prefix: str
    access_level: str
    rate_limit: int
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


class APIKeyCreated(APIKeyResponse):
    """Schema returned when creating an API key (includes full key once)."""
    
    key: str  # Full key - ONLY returned on creation


class APIKeyList(BaseModel):
    """Schema for paginated API key list response."""
    
    items: list[APIKeyResponse]
    total: int
    skip: int
    limit: int
