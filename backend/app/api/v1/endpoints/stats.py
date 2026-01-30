"""
Stats endpoint for dashboard metrics.
Provides aggregated counts and recent activity with in-memory caching.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter
from sqlalchemy import select, func

from app.api.deps import DB, RequireRead
from app.models.company import Company
from app.models.contact import Contact

router = APIRouter()

# Simple in-memory cache with TTL
_cache: dict = {"data": None, "expires_at": None}
CACHE_TTL_SECONDS = 60  # 1 minute cache


@router.get("")
async def get_stats(
    db: DB,
    current_user = RequireRead,
):
    """
    Get dashboard statistics including:
    - Total companies count
    - Total contacts count
    - Total unique lead sources
    - Recent activity (last 5 created records)
    """
    # Check cache
    if _cache["data"] and _cache["expires_at"] and _cache["expires_at"] > datetime.utcnow():
        return _cache["data"]
    
    # Query total companies
    total_companies = await db.scalar(
        select(func.count())
        .select_from(Company)
        .where(Company.deleted_at.is_(None))
    )
    
    # Query total contacts
    total_contacts = await db.scalar(
        select(func.count())
        .select_from(Contact)
        .where(Contact.deleted_at.is_(None))
    )
    
    # Count distinct lead sources from companies
    company_sources_result = await db.execute(
        select(func.count(func.distinct(Company.lead_source)))
        .where(Company.deleted_at.is_(None), Company.lead_source.isnot(None), Company.lead_source != '')
    )
    company_sources = company_sources_result.scalar() or 0
    
    # Count distinct lead sources from contacts
    contact_sources_result = await db.execute(
        select(func.count(func.distinct(Contact.lead_source)))
        .where(Contact.deleted_at.is_(None), Contact.lead_source.isnot(None), Contact.lead_source != '')
    )
    contact_sources = contact_sources_result.scalar() or 0
    
    # Get unique sources across both tables
    total_sources = company_sources + contact_sources
    
    # Recent activity - last 5 companies
    recent_companies_result = await db.execute(
        select(Company.id, Company.name, Company.created_at)
        .where(Company.deleted_at.is_(None))
        .order_by(Company.created_at.desc())
        .limit(5)
    )
    
    # Recent activity - last 5 contacts
    recent_contacts_result = await db.execute(
        select(Contact.id, Contact.first_name, Contact.last_name, Contact.created_at)
        .where(Contact.deleted_at.is_(None))
        .order_by(Contact.created_at.desc())
        .limit(5)
    )
    
    # Merge and sort recent activity
    activity = []
    for row in recent_companies_result.fetchall():
        activity.append({
            "type": "company",
            "id": str(row.id),
            "name": row.name,
            "created_at": row.created_at.isoformat() if row.created_at else None
        })
    
    for row in recent_contacts_result.fetchall():
        full_name = f"{row.first_name or ''} {row.last_name or ''}".strip()
        activity.append({
            "type": "contact",
            "id": str(row.id),
            "name": full_name or "Unknown",
            "created_at": row.created_at.isoformat() if row.created_at else None
        })
    
    # Sort by created_at descending and take top 5
    activity.sort(key=lambda x: x["created_at"] or "", reverse=True)
    activity = activity[:5]
    
    result = {
        "total_companies": total_companies or 0,
        "total_contacts": total_contacts or 0,
        "total_sources": total_sources,
        "recent_activity": activity,
    }
    
    # Update cache
    _cache["data"] = result
    _cache["expires_at"] = datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS)
    
    return result
