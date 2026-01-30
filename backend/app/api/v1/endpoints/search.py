"""Search endpoints."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, literal, union_all
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.api.deps import DB, RequireRead
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.search import SearchResponse, SearchType, SearchResultItem

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def search(
    db: DB,
    q: str = Query(..., min_length=1, description="Search query"),
    type: SearchType = Query(SearchType.ALL, description="Type of entities to search"),
    limit: int = Query(20, ge=1, le=50, description="Max results to return"),
    current_user = RequireRead,
) -> dict:
    """Full-text search across companies and contacts.

    Story 4.1: Full-Text Search
    Uses PostgreSQL GIN indexes and tsvector ranking.
    """
    if not q.strip():
        raise HTTPException(400, "Search query cannot be empty")

    search_query = func.plainto_tsquery('english', q)
    results = []

    # 1. Company Search Query
    if type in [SearchType.ALL, SearchType.COMPANIES]:
        # Create tsvector for ranking (must match index definition if possible,
        # but here we generate it on fly for flexibility if index isn't pre-computed column)
        # Using coalesce to handle nulls
        company_vector = func.to_tsvector(
            'english',
            func.coalesce(Company.name, '') + ' ' +
            func.coalesce(Company.description, '') + ' ' +
            func.coalesce(Company.domain, '')
        )

        company_rank = func.ts_rank(company_vector, search_query)

        company_stmt = select(
            literal("company").label("entity_type"),
            Company.id.label("entity_id"),
            company_rank.label("relevance_score"),
            func.json_build_object(
                "name", Company.name,
                "domain", Company.domain,
                "description", func.substring(Company.description, 1, 200),
                "industry", Company.industry,
                "location", Company.location
            ).label("data")
        ).where(
            company_vector.op('@@')(search_query),
            Company.deleted_at.is_(None)
        )
        results.append(company_stmt)

    # 2. Contact Search Query
    if type in [SearchType.ALL, SearchType.CONTACTS]:
        # Pre-process email to allow searching by parts (replace @ and . with space)
        # This ensures 'john.doe@example.com' becomes 'john doe example com' in vector
        email_clean = func.replace(func.replace(func.coalesce(Contact.email, ''), '@', ' '), '.', ' ')

        contact_vector = func.to_tsvector(
            'english',
            func.coalesce(Contact.first_name, '') + ' ' +
            func.coalesce(Contact.last_name, '') + ' ' +
            email_clean + ' ' +
            func.coalesce(Contact.job_title, '')
        )

        contact_rank = func.ts_rank(contact_vector, search_query)

        contact_stmt = select(
            literal("contact").label("entity_type"),
            Contact.id.label("entity_id"),
            contact_rank.label("relevance_score"),
            func.json_build_object(
                "full_name", Contact.full_name,
                "email", Contact.email,
                "job_title", Contact.job_title,
                "company_name", Contact.working_company_name
            ).label("data")
        ).where(
            contact_vector.op('@@')(search_query),
            Contact.deleted_at.is_(None)
        )
        results.append(contact_stmt)

    if not results:
        return {"results": [], "total_count": 0}

    # Combine queries, order by rank, and limit
    if len(results) == 1:
        final_stmt = results[0]
    else:
        final_stmt = union_all(*results)

    # Wrap in subquery to order and limit
    subquery = final_stmt.subquery()
    stmt = select(subquery).order_by(subquery.c.relevance_score.desc()).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    # Map to schema
    search_results = [
        SearchResultItem(
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            relevance_score=float(row.relevance_score),
            data=row.data
        )
        for row in rows
    ]

    return {
        "results": search_results,
        "total_count": len(search_results)  # Only counting fetched results for now
    }
