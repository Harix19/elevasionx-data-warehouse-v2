"""API key generation and validation utilities."""

import secrets
import bcrypt
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey, AccessLevel
from app.models.user import User


API_KEY_PREFIX = "ldwsk-"
API_KEY_PREFIX_LENGTH = 12  # Length of "ldwsk-" + 6 chars for identifier


def generate_api_key() -> Tuple[str, str, str]:
    """Generate a new API key.
    
    Returns:
        Tuple of (full_key, prefix, hash)
        - full_key: The complete API key (only shown once on creation)
        - prefix: First 12 chars for identification (e.g., "ldwsk-a1b2c3d4")
        - hash: bcrypt hash of the full key for storage
    """
    # Generate 32 random characters (base64url encoded)
    random_part = secrets.token_urlsafe(24)
    full_key = f"{API_KEY_PREFIX}{random_part}"
    
    # Extract first 12 characters for the prefix
    prefix = full_key[:12]
    
    # Hash with bcrypt
    key_bytes = full_key.encode("utf-8")
    key_hash = bcrypt.hashpw(key_bytes, bcrypt.gensalt()).decode("utf-8")
    
    return full_key, prefix, key_hash


def verify_api_key(plain_key: str, key_hash: str) -> bool:
    """Verify an API key against its hash.
    
    Args:
        plain_key: The raw API key provided by the user
        key_hash: The stored bcrypt hash
        
    Returns:
        True if the key matches the hash, False otherwise
    """
    return bcrypt.checkpw(plain_key.encode("utf-8"), key_hash.encode("utf-8"))


def has_access_level(key_level: AccessLevel, required_level: AccessLevel) -> bool:
    """Check if an API key's access level meets the required level.
    
    Hierarchy: read < write < admin
    
    Args:
        key_level: The API key's access level
        required_level: The minimum required access level
        
    Returns:
        True if the key has sufficient access
    """
    level_hierarchy = {
        AccessLevel.READ: 1,
        AccessLevel.WRITE: 2,
        AccessLevel.ADMIN: 3,
    }
    return level_hierarchy[key_level] >= level_hierarchy[required_level]


async def validate_api_key(
    db: AsyncSession,
    api_key: str
) -> Optional[Tuple[User, APIKey]]:
    """Validate an API key and return the associated user.
    
    Args:
        db: Database session
        api_key: The API key to validate (including "ldwsk-" prefix)
        
    Returns:
        Tuple of (user, api_key_obj) if valid, None otherwise
    """
    # Extract the prefix for database lookup
    prefix = api_key[:12] if len(api_key) >= 12 else ""
    
    # Find the API key by prefix (we need to check against hash)
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_prefix == prefix,
            APIKey.is_active == True
        )
    )
    api_key_obj: Optional[APIKey] = result.scalar_one_or_none()
    
    if not api_key_obj:
        return None
    
    # Verify the full key against the stored hash
    if not verify_api_key(api_key, api_key_obj.key_hash):
        return None
    
    # Get the associated user
    result = await db.execute(
        select(User).where(
            User.id == api_key_obj.user_id,
            User.is_active == True
        )
    )
    user: Optional[User] = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # Update last_used_at
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    
    return user, api_key_obj


def get_access_level(level_str: str) -> AccessLevel:
    """Convert string to AccessLevel enum.
    
    Args:
        level_str: One of 'read', 'write', 'admin'
        
    Returns:
        Corresponding AccessLevel enum value
    """
    try:
        return AccessLevel(level_str.lower())
    except ValueError:
        return AccessLevel.READ
