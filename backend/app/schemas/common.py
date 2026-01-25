"""Common schemas for API responses."""

import base64
import json
from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorPaginationParams(BaseModel):
    """Cursor pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page (max 100)")
    cursor: str | None = Field(default=None, description="Encoded cursor for pagination")


def decode_cursor(cursor: str) -> tuple[datetime, str] | None:
    """Decode a cursor string into (created_at, id) tuple.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (created_at datetime, entity_id str) or None if invalid
    """
    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        data = json.loads(decoded)
        created_at = datetime.fromisoformat(data["created_at"])
        entity_id = data["id"]
        return created_at, entity_id
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def encode_cursor(created_at: datetime, entity_id: str) -> str:
    """Encode (created_at, id) into a cursor string.

    Args:
        created_at: Datetime of the entity
        entity_id: UUID string of the entity

    Returns:
        Base64-encoded cursor string
    """
    data = {
        "created_at": created_at.isoformat(),
        "id": entity_id,
    }
    json_str = json.dumps(data)
    return base64.b64encode(json_str.encode()).decode()


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper with cursor-based pagination."""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None
