"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, companies, contacts, search, bulk, export, stats, api_keys

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(bulk.router, prefix="/bulk", tags=["bulk"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
