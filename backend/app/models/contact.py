"""Contact model."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.db.base import Base, TimestampMixin
from app.models.lead_status import LeadStatus, LeadStatusType


class Contact(Base, TimestampMixin):
    """Contact model for people at companies."""

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_domain: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_tags_a: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    custom_tags_b: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    custom_tags_c: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    lead_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        LeadStatusType,
        default=LeadStatus.NEW,
        nullable=False,
    )
    deleted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Indexes - email must be unique for ON CONFLICT to work
    __table_args__ = (
        Index("idx_contacts_email", "email", unique=True),
        Index("idx_contacts_company_id", "company_id"),
        Index("idx_contacts_seniority", "seniority_level"),
        Index("idx_contacts_department", "department"),
    )
