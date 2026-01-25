"""Authentication tests for Epic 1 stories 1.2, 1.3, 1.4."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User

# =============================================================================
# Story 1.2: Password Hashing Tests
# =============================================================================

class TestPasswordHashing:
    """Test password hashing and verification (Story 1.2)."""

    def test_hash_password_returns_string(self):
        """Test password hashing returns a string."""
        password = "testpass123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_produces_different_hash_each_time(self):
        """Test password hashing produces different hash each time (bcrypt salt)."""
        password = "testpass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2, "Each hash should be unique due to salt"

    def test_verify_password_works_correctly(self):
        """Test password verification works correctly."""
        password = "testpass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_fails_for_wrong_password(self):
        """Test password verification fails for wrong password."""
        password = "testpass123"
        wrong_password = "wrongpass123"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_plain_password_never_in_database(self):
        """Test plain password is never stored in database."""
        password = "testpass123"
        hashed = hash_password(password)
        assert password not in hashed, "Plain password should not be in hash"
        assert len(password) < len(hashed), "Hash should be longer than plain password"

    def test_hashed_password_format(self):
        """Test bcrypt hash format ($2b$...)."""
        password = "testpass123"
        hashed = hash_password(password)
        assert hashed.startswith("$2b$"), "Bcrypt hashes start with $2b$"

    @pytest.mark.asyncio
    async def test_user_creation_with_all_required_fields(self, db):
        """Test user creation with all required fields."""
        user = User(
            email="test@example.com",
            hashed_password=hash_password("testpass123"),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.hashed_password.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_constraint_violation(self, db):
        """Test duplicate email raises constraint violation."""
        # Create first user
        user1 = User(
            email="duplicate@example.com",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )
        db.add(user1)
        await db.commit()

        # Try to create second user with same email
        user2 = User(
            email="duplicate@example.com",
            hashed_password=hash_password("pass456"),
            is_active=True,
        )
        db.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            await db.commit()


# =============================================================================
# Story 1.3: JWT Login Tests
# =============================================================================

class TestJWTLogin:
    """Test JWT token creation and login endpoint (Story 1.3)."""

    def test_create_access_token_returns_string(self):
        """Test create_access_token returns a string."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_contains_correct_sub_claim(self):
        """Test JWT contains correct 'sub' claim."""
        subject = "user-123"
        data = {"sub": subject}
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == subject

    def test_jwt_contains_exp_claim(self):
        """Test JWT contains 'exp' claim."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in payload
        assert isinstance(payload["exp"], (int, float))

    def test_jwt_expiration_time_is_correct(self):
        """Test JWT expiration is set to ACCESS_TOKEN_EXPIRE_MINUTES."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Use timezone-aware datetime
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now

        # Should be approximately ACCESS_TOKEN_EXPIRE_MINUTES (allow 1 minute variance)
        expected_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        actual_minutes = time_diff.total_seconds() / 60
        assert expected_minutes - 1 <= actual_minutes <= expected_minutes + 1

    @pytest.mark.asyncio
    async def test_successful_login_returns_jwt_token(self, async_client: AsyncClient, db):
        """Test successful login returns JWT token."""
        # First, create a user
        user = User(
            email="login@example.com",
            hashed_password=hash_password("correctpass"),
            is_active=True,
        )
        db.add(user)
        await db.commit()

        # Now test login
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "login@example.com", "password": "correctpass"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_invalid_password_returns_401(self, async_client: AsyncClient, db):
        """Test invalid password returns 401."""
        # Create a user
        user = User(
            email="login2@example.com",
            hashed_password=hash_password("correctpass"),
            is_active=True,
        )
        db.add(user)
        await db.commit()

        # Test with wrong password
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "login2@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_non_existent_email_returns_401(self, async_client: AsyncClient):
        """Test non-existent email returns 401."""
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent@example.com", "password": "anypass"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_token_type_is_bearer(self, async_client: AsyncClient, db):
        """Test token_type is 'bearer'."""
        user = User(
            email="bearer@example.com",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )
        db.add(user)
        await db.commit()

        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "bearer@example.com", "password": "pass123"}
        )
        assert response.json()["token_type"] == "bearer"


# =============================================================================
# Story 1.4: Protected Endpoint Authorization Tests
# =============================================================================

class TestProtectedEndpointAuthorization:
    """Test protected endpoint authorization (Story 1.4)."""

    @pytest.mark.asyncio
    async def test_valid_token_grants_access_to_protected_endpoint(self, async_client: AsyncClient, db):
        """Test valid token grants access to protected endpoint."""
        # Create user
        user = User(
            email="protected@example.com",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )
        db.add(user)
        await db.commit()

        # Get token
        login_response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "protected@example.com", "password": "pass123"}
        )
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_missing_authorization_header_returns_401_not_authenticated(self, async_client: AsyncClient):
        """Test missing Authorization header returns 401 'Not authenticated'."""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_malformed_token_returns_401(self, async_client: AsyncClient):
        """Test malformed token returns 401 'Could not validate credentials'."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token-format"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_wrong_signature_token_returns_401(self, async_client: AsyncClient):
        """Test token with wrong signature returns 401."""
        # Create a token with wrong secret
        fake_payload = {"sub": "some-user-id", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
        fake_token = jwt.encode(fake_payload, "wrong-secret-key", algorithm="HS256")

        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, async_client: AsyncClient):
        """Test expired token returns 401."""
        # Create an expired token
        expired_payload = {
            "sub": "some-user-id",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired 1 minute ago
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"
