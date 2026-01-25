"""Seed user accounts for team authentication."""

import asyncio
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import hash_password

SEED_USERS = [
    {"email": "admin@example.com", "password": "adminpass123"},
    {"email": "sales@example.com", "password": "salespass123"},
    {"email": "ops@example.com", "password": "opspass123"},
]


async def seed_users():
    """Create user accounts with hashed passwords."""
    async with async_session_maker() as session:
        for user_data in SEED_USERS:
            user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                is_active=True,
            )
            session.add(user)
        await session.commit()
        print(f"Created {len(SEED_USERS)} users")


if __name__ == "__main__":
    asyncio.run(seed_users())
