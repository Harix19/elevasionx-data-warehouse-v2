"""User endpoints for protected resources."""

from fastapi import APIRouter

from app.api.deps import CurrentUser

router = APIRouter()


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_active": current_user.is_active,
    }
