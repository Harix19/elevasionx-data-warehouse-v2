"""API key model for authentication and access control."""

from datetime import datetime, timezone
import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AccessLevel(str, enum.Enum):
    """Access levels for API keys.
    
    - read: GET endpoints only
    - write: GET, POST, PATCH, DELETE (full CRUD)
    - admin: Full access + API key management
    """
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class APIKey(Base):
    """API key for programmatic access.
    
    API keys provide an alternative to JWT authentication for
    programmatic access to the API. Each key is associated with
    a user and has configurable access levels and rate limits.
    """
    
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Descriptive name for the key
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # First 12 chars for identification (e.g., "ldwsk-a1b2c3d4")
    # Not the actual key, just a prefix for display
    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    # bcrypt hash of the full API key
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Access level (read/write/admin)
    access_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AccessLevel.READ.value,
    )
    
    # Requests per minute limit
    rate_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
    )
    
    # Owner of the key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Soft delete / deactivation
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Tracking
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationship
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix={self.key_prefix}, level={self.access_level})>"
