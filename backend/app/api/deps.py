"""Dependency injection for FastAPI endpoints."""

from typing import Annotated, AsyncGenerator, Optional, Tuple
from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db.session import async_session_maker
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.core.api_key import validate_api_key, has_access_level, get_access_level
from app.models.user import User
from app.models.api_key import APIKey, AccessLevel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user_jwt(
    db: AsyncSession,
    token: str
) -> Optional[User]:
    """Validate JWT token and return user.
    
    Args:
        db: Database session
        token: JWT access token
        
    Returns:
        User if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user_from_jwt(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Get current authenticated user from JWT token.
    
    This is the original JWT-only authentication method.
    Kept for backwards compatibility and specific JWT-only endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = await get_current_user_jwt(db, token)
    if user is None:
        raise credentials_exception
    return user


async def get_current_auth(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    api_key: Annotated[Optional[str], Security(api_key_header)] = None,
) -> Tuple[User, Optional[APIKey]]:
    """Get current authenticated user from JWT or API key.
    
    This unified authentication method accepts either:
    - JWT Bearer token (Authorization header)
    - API key (X-API-Key header)
    
    Returns:
        Tuple of (user, api_key)
        - api_key is None if JWT authentication was used
        - api_key is the APIKey object if API key authentication was used
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try API key first (if provided)
    if api_key:
        result = await validate_api_key(db, api_key)
        if result:
            user, api_key_obj = result
            return user, api_key_obj
        raise credentials_exception
    
    # Try JWT token
    if token:
        user = await get_current_user_jwt(db, token)
        if user:
            return user, None
        raise credentials_exception
    
    # No credentials provided
    raise credentials_exception


def require_access(level: AccessLevel):
    """Create a dependency that requires a specific access level.
    
    Usage:
        @router.get("/companies")
        async def list_companies(
            user: User = Depends(require_access(AccessLevel.READ))
        ):
            ...
    
    Args:
        level: Minimum required access level (read, write, admin)
        
    Returns:
        Dependency function that validates access and returns the user
    """
    async def check_access(
        auth: Annotated[Tuple[User, Optional[APIKey]], Depends(get_current_auth)]
    ) -> User:
        user, api_key = auth
        
        # JWT tokens are treated as ADMIN access (full access)
        # API keys are checked against their configured access level
        if api_key is None:
            # JWT authentication - full access
            return user
        
        # API key authentication - check access level
        api_level = get_access_level(api_key.access_level)
        if not has_access_level(api_level, level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient access level. Required: {level.value}"
            )
        
        return user
    
    return check_access


# Type aliases for cleaner endpoint signatures
DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user_from_jwt)]
CurrentAuth = Annotated[Tuple[User, Optional[APIKey]], Depends(get_current_auth)]

# Convenience dependencies for access levels
RequireRead = Annotated[User, Depends(require_access(AccessLevel.READ))]
RequireWrite = Annotated[User, Depends(require_access(AccessLevel.WRITE))]
RequireAdmin = Annotated[User, Depends(require_access(AccessLevel.ADMIN))]
