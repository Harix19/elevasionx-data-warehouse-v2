"""Lead status ENUM type."""

from sqlalchemy import String, Enum as SQLEnum
import enum


class LeadStatus(str, enum.Enum):
    """Lead status values."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    CHURNED = "churned"


# For use in SQLAlchemy models
LeadStatusType = SQLEnum(
    LeadStatus,
    name="lead_status",
    values_callable=lambda obj: [e.value for e in obj],
)
