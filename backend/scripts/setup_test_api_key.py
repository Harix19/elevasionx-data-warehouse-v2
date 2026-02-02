"""Setup script for creating test user and API key.

Run this script to create a test user with a WRITE-level API key for testing.

Usage:
    cd backend && python3 -m scripts.setup_test_api_key

This creates:
    - A test user (test@example.com)
    - A WRITE-level API key for that user
    - Saves the API key to .env.test for testing
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import hash_password
from app.core.api_key import generate_api_key


# Test user configuration
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"
TEST_USER_NAME = "Test User"
API_KEY_NAME = "Test API Key for Integration Tests"


async def setup_test_environment():
    """Create test user and API key."""
    async with async_session_maker() as session:
        # Check if test user exists
        stmt = select(User).where(User.email == TEST_EMAIL)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✓ Test user already exists: {user.email} (ID: {user.id})")
        else:
            # Create test user
            print(f"Creating test user: {TEST_EMAIL}")
            user = User(
                id=uuid.uuid4(),
                email=TEST_EMAIL,
                hashed_password=hash_password(TEST_PASSWORD),
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✓ Created test user (ID: {user.id})")
        
        # Generate new API key
        print(f"\nCreating new WRITE-level API key...")
        full_key, prefix, key_hash = generate_api_key()
        
        # Use raw SQL with proper enum casting
        sql = text("""
            INSERT INTO api_keys (id, name, key_prefix, key_hash, access_level, rate_limit, user_id, is_active, last_used_at, created_at, updated_at)
            VALUES (:id, :name, :prefix, :hash, 'write'::access_level, :rate_limit, :user_id, :is_active, :last_used, :created, :updated)
        """)
        
        now = datetime.now(timezone.utc)
        params = {
            "id": str(uuid.uuid4()),
            "name": API_KEY_NAME,
            "prefix": prefix,
            "hash": key_hash,
            "rate_limit": 1000,
            "user_id": str(user.id),
            "is_active": True,
            "last_used": None,
            "created": now,
            "updated": now,
        }
        
        await session.execute(sql, params)
        await session.commit()
        
        print(f"✓ Created API key: {prefix}... (Level: WRITE)")
        print(f"\n{'='*60}")
        print(f"API KEY (SAVE THIS - shown only once):")
        print(f"{full_key}")
        print(f"{'='*60}\n")
        
        # Save to .env.test file
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.test")
        env_content = f"""# Test environment configuration
# Generated on {datetime.now(timezone.utc).isoformat()}

# Test User
TEST_USER_EMAIL={TEST_EMAIL}
TEST_USER_PASSWORD={TEST_PASSWORD}

# Test API Key (WRITE level)
TEST_API_KEY={full_key}
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print(f"✓ Saved configuration to {env_file}")
        
        return full_key


if __name__ == "__main__":
    try:
        api_key = asyncio.run(setup_test_environment())
        print("\n✓ Setup complete!")
        print(f"\nTo run live API tests with authentication:")
        print(f"  export API_TEST_KEY={api_key}")
        print(f"  pytest tests/api/test_live_api.py -v")
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
