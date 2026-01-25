"""Search schemas."""

from enum import Enum
from uuid import UUID
from typing import Any
from pydantic import BaseModel


class SearchType(str, Enum):
    """Types of entities to search."""

    COMPANIES = "companies"
    CONTACTS = "contacts"
    ALL = "all"


class SearchResultItem(BaseModel):
    """Single search result item."""

    entity_type: str  # "company" or "contact"
    entity_id: UUID
    relevance_score: float
    data: dict[str, Any]


class SearchResponse(BaseModel):
    """Search response wrapper."""

    results: list[SearchResultItem]
    total_count: int
