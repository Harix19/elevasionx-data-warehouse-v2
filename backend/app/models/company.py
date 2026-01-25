"""Company model."""

from sqlalchemy import Column, String, Integer, Text, Boolean, Numeric, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.db.base import Base, TimestampMixin
from app.models.lead_status import LeadStatus, LeadStatusType


class Company(Base, TimestampMixin):
    """Company model for lead tracking."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    technologies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    funding_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    funding_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
    last_contacted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("idx_companies_domain", "domain"),
        Index("idx_companies_status", "status"),
        Index("idx_companies_industry", "industry"),
        Index("idx_companies_country", "country"),
        Index("idx_companies_lead_score", "lead_score"),
    )
