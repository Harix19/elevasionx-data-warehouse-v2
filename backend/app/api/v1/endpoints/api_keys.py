"""API key management endpoints.

STORY-010: Internal team needs a way to generate and manage API keys
for programmatic access without JWT tokens.

Provides CRUD operations for API keys with proper access control:
- read: GET endpoints only
- write: Full CRUD operations
- admin: Full access including API key management
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, RequireAdmin
from app.models.api_key import APIKey, AccessLevel
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreated,
    APIKeyList
)
from app.core.api_key import generate_api_key, verify_api_key

router = APIRouter()


@router.post(
    "/",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="""
    Generate a new API key for programmatic access.
    
    The API key is returned ONLY ONCE during creation.
    Make sure to copy it immediately as it cannot be retrieved later.
    
    Access level determines permissions:
    - read: GET endpoints only (companies, contacts, search, export)
    - write: Full CRUD operations including bulk import
    - admin: Full access including API key management
    
    Rate limit can be set between 1-10000 requests per minute.
    Default is 1000 requests per minute.
    
    Requires: admin access
    """,
)
async def create_api_key(
    data: APIKeyCreate,
    current_user: RequireAdmin,
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreated:
    """Create a new API key."""
    # Generate the key
    full_key, key_prefix, key_hash = generate_api_key()
    
    # Create the database record
    api_key = APIKey(
        name=data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        access_level=data.access_level.value,
        rate_limit=data.rate_limit,
        user_id=current_user.id,
        is_active=True,
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # Return response with full key (only shown once!)
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        access_level=api_key.access_level,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
        key=full_key,  # Only returned once!
    )


@router.get(
    "/",
    response_model=APIKeyList,
    summary="List API keys",
    description="""
    List all API keys for the current user.
    
    Returns masked API keys (only showing the prefix for identification).
    The full key is never returned after initial creation.
    
    Supports pagination with skip and limit parameters.
    
    Requires: admin access
    """,
)
async def list_api_keys(
    current_user: RequireAdmin,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> APIKeyList:
    """List API keys for the current user."""
    # Build query
    query = select(APIKey).where(APIKey.user_id == current_user.id)
    
    if is_active is not None:
        query = query.where(APIKey.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(APIKey.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    return APIKeyList(
        items=[APIKeyResponse.model_validate(k) for k in api_keys],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{api_key_id}",
    response_model=APIKeyResponse,
    summary="Get API key details",
    description="""
    Get detailed information about a specific API key.
    
    Returns masked key information (prefix only, not the full key).
    
    Requires: admin access
    """,
)
async def get_api_key(
    api_key_id: uuid.UUID,
    current_user: RequireAdmin,
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Get a specific API key by ID."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyResponse.model_validate(api_key)


@router.patch(
    "/{api_key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="""
    Update an existing API key's properties.
    
    Can update:
    - name: Descriptive name
    - access_level: read/write/admin
    - rate_limit: Requests per minute (1-10000)
    - is_active: Enable/disable the key
    
    Note: Cannot change the key itself. Use regenerate endpoint for that.
    
    Requires: admin access
    """,
)
async def update_api_key(
    api_key_id: uuid.UUID,
    data: APIKeyUpdate,
    current_user: RequireAdmin,
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Update an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields if provided
    if data.name is not None:
        api_key.name = data.name
    if data.access_level is not None:
        api_key.access_level = data.access_level.value
    if data.rate_limit is not None:
        api_key.rate_limit = data.rate_limit
    if data.is_active is not None:
        api_key.is_active = data.is_active
    
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyResponse.model_validate(api_key)


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (revoke) API key",
    description="""
    Soft delete (revoke) an API key.
    
    The key is marked as inactive and can no longer be used for authentication.
    The key record is kept for audit purposes.
    
    Requires: admin access
    """,
)
async def delete_api_key(
    api_key_id: uuid.UUID,
    current_user: RequireAdmin,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete (revoke) an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Soft delete by marking inactive
    api_key.is_active = False
    await db.commit()


@router.post(
    "/{api_key_id}/regenerate",
    response_model=APIKeyCreated,
    summary="Regenerate API key",
    description="""
    Generate a new API key, invalidating the old one.
    
    This creates a new key with the same name and permissions,
    but with a new key value. The old key is immediately invalidated.
    
    Returns the new API key (shown only once - save it immediately).
    
    Requires: admin access
    """,
)
async def regenerate_api_key(
    api_key_id: uuid.UUID,
    current_user: RequireAdmin,
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreated:
    """Regenerate an API key with a new value."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Generate new key
    full_key, key_prefix, key_hash = generate_api_key()
    
    # Update the record with new values
    api_key.key_prefix = key_prefix
    api_key.key_hash = key_hash
    api_key.is_active = True  # Reactivate if it was deactivated
    
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        access_level=api_key.access_level,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
        key=full_key,  # Only returned once!
    )
