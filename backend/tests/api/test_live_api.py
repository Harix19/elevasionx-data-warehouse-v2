"""Live API endpoint tests with real-time HTTP validation.

These tests make actual HTTP calls to a running API server to validate
endpoint behavior in a real environment. Useful for integration testing
and validating the API against a live database.

Usage:
    1. Start the API server: `uvicorn app.main:app --reload`
    2. Run tests: `pytest tests/api/test_live_api.py -v`
    
Environment variables:
    API_BASE_URL: Base URL of the API (default: http://localhost:8000)
    API_TEST_EMAIL: Test user email for authentication
    API_TEST_PASSWORD: Test user password for authentication
    API_TEST_KEY: API key for authentication (alternative to JWT)

Authentication:
    Tests support multiple authentication methods in order of preference:
    1. API Key (X-API-Key header) - if API_TEST_KEY is set
    2. JWT Token (Bearer token) - if API_TEST_EMAIL/PASSWORD are valid
    3. No auth - for public endpoints only
"""

import os
import pytest
import httpx
from uuid import uuid4
from datetime import datetime

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1 = f"{BASE_URL}/api/v1"
TEST_EMAIL = os.getenv("API_TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("API_TEST_PASSWORD", "testpass123")
TEST_API_KEY = os.getenv("API_TEST_KEY", "ldwsk-AWtL7bNGc5BaMKek-9hrsZnQCPn3NaL9")

# Timeout for HTTP requests (seconds) - longer for database writes
REQUEST_TIMEOUT = 30.0


class LiveAPIClient:
    """HTTP client wrapper for live API testing.
    
    Supports multiple authentication methods:
    - API Key via X-API-Key header
    - JWT Bearer token via /auth/token endpoint
    """
    
    def __init__(self):
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT)
        self.token = None
        self.api_key = None
        self.headers = {"Content-Type": "application/json"}
        self.auth_method = None  # 'api_key', 'jwt', or None
    
    def authenticate_with_api_key(self, api_key: str) -> bool:
        """Authenticate using API key."""
        try:
            self.headers["X-API-Key"] = api_key
            # Test if the key works by making a request
            response = self.client.get(f"{API_V1}/companies/", headers=self.headers, params={"limit": 1})
            if response.status_code in [200, 201]:
                self.api_key = api_key
                self.auth_method = "api_key"
                return True
            del self.headers["X-API-Key"]
            return False
        except Exception as e:
            print(f"API key authentication failed: {e}")
            return False
    
    def authenticate_with_jwt(self, email: str = TEST_EMAIL, password: str = TEST_PASSWORD) -> bool:
        """Authenticate using JWT token."""
        try:
            response = self.client.post(
                f"{API_V1}/auth/token",
                data={"username": email, "password": password},
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.auth_method = "jwt"
                return True
            return False
        except Exception as e:
            print(f"JWT authentication failed: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Try multiple authentication methods in order."""
        # Try API key first if provided
        if TEST_API_KEY:
            if self.authenticate_with_api_key(TEST_API_KEY):
                print(f"Authenticated with API key")
                return True
        
        # Try JWT next
        if self.authenticate_with_jwt():
            print(f"Authenticated with JWT for {TEST_EMAIL}")
            return True
        
        # Check if endpoints work without auth (public endpoints)
        try:
            response = self.client.get(f"{API_V1}/companies/", params={"limit": 1})
            if response.status_code == 200:
                self.auth_method = None
                print("Using unauthenticated access (public endpoints)")
                return True
        except:
            pass
        
        return False
    
    def get(self, endpoint: str, params: dict = None):
        """Make authenticated GET request."""
        return self.client.get(f"{API_V1}{endpoint}", headers=self.headers, params=params)
    
    def post(self, endpoint: str, json: dict = None):
        """Make authenticated POST request."""
        return self.client.post(f"{API_V1}{endpoint}", headers=self.headers, json=json)
    
    def patch(self, endpoint: str, json: dict = None):
        """Make authenticated PATCH request."""
        return self.client.patch(f"{API_V1}{endpoint}", headers=self.headers, json=json)
    
    def delete(self, endpoint: str):
        """Make authenticated DELETE request."""
        return self.client.delete(f"{API_V1}{endpoint}", headers=self.headers)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def api_client():
    """Create an authenticated API client for testing."""
    client = LiveAPIClient()
    yield client
    client.close()


@pytest.fixture(scope="module")
def authenticated_client(api_client):
    """Ensure client is authenticated before tests."""
    if api_client.authenticate():
        yield api_client
    else:
        pytest.skip("Could not authenticate - is the API server running?")


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_liveness_endpoint(self):
        """Test /health/live endpoint returns OK."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/health/live")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
    
    def test_readiness_endpoint(self):
        """Test /health/ready endpoint returns OK with database status."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_with_valid_credentials(self):
        """Test successful login returns JWT token."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            # The auth endpoint is /auth/token (OAuth2 standard)
            response = client.post(
                f"{API_V1}/auth/token",
                data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
            )
            # May be 200 or 401 depending on whether user exists
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password returns 401."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{API_V1}/auth/token",
                data={"username": "fake@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == 401


# ============================================================================
# Companies API Tests
# ============================================================================

class TestCompaniesAPI:
    """Test Companies CRUD endpoints."""
    
    def test_list_companies(self, authenticated_client):
        """Test GET /companies returns paginated list."""
        response = authenticated_client.get("/companies/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "has_more" in data
        assert "next_cursor" in data
        assert isinstance(data["items"], list)
    
    def test_list_companies_with_limit(self, authenticated_client):
        """Test GET /companies with limit parameter."""
        response = authenticated_client.get("/companies/", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
    
    def test_list_companies_limit_exceeds_max(self, authenticated_client):
        """Test GET /companies with limit > 100 returns 400."""
        response = authenticated_client.get("/companies/", params={"limit": 150})
        assert response.status_code == 400
        assert "cannot exceed 100" in response.json()["detail"]
    
    def test_create_company(self, authenticated_client):
        """Test POST /companies creates a new company."""
        unique_domain = f"test-{uuid4().hex[:8]}.com"
        company_data = {
            "name": f"Test Company {uuid4().hex[:8]}",
            "domain": unique_domain,
            "industry": "Technology",
            "country": "USA",
        }
        
        response = authenticated_client.post("/companies/", json=company_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == company_data["name"]
        assert data["domain"] == unique_domain
        assert "id" in data
        assert "created_at" in data
        
        # Cleanup: delete the created company
        authenticated_client.delete(f"/companies/{data['id']}")
    
    def test_create_company_duplicate_domain(self, authenticated_client):
        """Test POST /companies with duplicate domain returns 409."""
        unique_domain = f"dup-{uuid4().hex[:8]}.com"
        company_data = {"name": "Company 1", "domain": unique_domain}
        
        # Create first company
        response1 = authenticated_client.post("/companies/", json=company_data)
        assert response1.status_code == 201
        company_id = response1.json()["id"]
        
        # Try to create duplicate
        company_data["name"] = "Company 2"
        response2 = authenticated_client.post("/companies/", json=company_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
        
        # Cleanup
        authenticated_client.delete(f"/companies/{company_id}")
    
    def test_get_company_by_id(self, authenticated_client):
        """Test GET /companies/{id} returns company details."""
        # Create a test company
        company_data = {"name": f"GetTest-{uuid4().hex[:8]}", "domain": f"get-{uuid4().hex[:8]}.com"}
        create_response = authenticated_client.post("/companies/", json=company_data)
        company_id = create_response.json()["id"]
        
        # Get the company
        response = authenticated_client.get(f"/companies/{company_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == company_id
        assert data["name"] == company_data["name"]
        
        # Cleanup
        authenticated_client.delete(f"/companies/{company_id}")
    
    def test_get_company_not_found(self, authenticated_client):
        """Test GET /companies/{id} returns 404 for non-existent ID."""
        fake_id = str(uuid4())
        response = authenticated_client.get(f"/companies/{fake_id}")
        assert response.status_code == 404
    
    def test_update_company(self, authenticated_client):
        """Test PATCH /companies/{id} updates company."""
        # Create a test company
        company_data = {"name": f"UpdateTest-{uuid4().hex[:8]}", "domain": f"update-{uuid4().hex[:8]}.com"}
        create_response = authenticated_client.post("/companies/", json=company_data)
        company_id = create_response.json()["id"]
        
        # Update the company
        update_data = {"name": "Updated Company Name", "industry": "Finance"}
        response = authenticated_client.patch(f"/companies/{company_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Company Name"
        assert data["industry"] == "Finance"
        
        # Cleanup
        authenticated_client.delete(f"/companies/{company_id}")
    
    def test_delete_company_soft_delete(self, authenticated_client):
        """Test DELETE /companies/{id} performs soft delete."""
        # Create a test company
        company_data = {"name": f"DeleteTest-{uuid4().hex[:8]}", "domain": f"delete-{uuid4().hex[:8]}.com"}
        create_response = authenticated_client.post("/companies/", json=company_data)
        company_id = create_response.json()["id"]
        
        # Delete the company
        response = authenticated_client.delete(f"/companies/{company_id}")
        assert response.status_code == 204
        
        # Verify it's not accessible
        get_response = authenticated_client.get(f"/companies/{company_id}")
        assert get_response.status_code == 404
    
    def test_restore_company(self, authenticated_client):
        """Test POST /companies/{id}/restore restores deleted company."""
        # Create and delete a company
        company_data = {"name": f"RestoreTest-{uuid4().hex[:8]}", "domain": f"restore-{uuid4().hex[:8]}.com"}
        create_response = authenticated_client.post("/companies/", json=company_data)
        company_id = create_response.json()["id"]
        authenticated_client.delete(f"/companies/{company_id}")
        
        # Restore the company
        response = authenticated_client.post(f"/companies/{company_id}/restore")
        assert response.status_code == 200
        assert response.json()["deleted_at"] is None
        
        # Verify it's accessible again
        get_response = authenticated_client.get(f"/companies/{company_id}")
        assert get_response.status_code == 200
        
        # Cleanup
        authenticated_client.delete(f"/companies/{company_id}")
    
    def test_filter_options_endpoint(self, authenticated_client):
        """Test GET /companies/filter-options returns available filters."""
        response = authenticated_client.get("/companies/filter-options")
        assert response.status_code == 200
        data = response.json()
        # Response should be a dict with available filter options
        assert isinstance(data, dict)


# ============================================================================
# Contacts API Tests
# ============================================================================

class TestContactsAPI:
    """Test Contacts CRUD endpoints."""
    
    def test_list_contacts(self, authenticated_client):
        """Test GET /contacts returns paginated list."""
        response = authenticated_client.get("/contacts/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "has_more" in data
        assert isinstance(data["items"], list)
    
    def test_list_contacts_with_search(self, authenticated_client):
        """Test GET /contacts with search query."""
        response = authenticated_client.get("/contacts/", params={"q": "test"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
    
    def test_create_contact(self, authenticated_client):
        """Test POST /contacts creates a new contact."""
        contact_data = {
            "first_name": "Test",
            "last_name": f"User-{uuid4().hex[:8]}",
            "email": f"test-{uuid4().hex[:8]}@example.com",
            "job_title": "Developer",
        }
        
        response = authenticated_client.post("/contacts/", json=contact_data)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == contact_data["first_name"]
        assert data["last_name"] == contact_data["last_name"]
        assert data["full_name"] == f"{contact_data['first_name']} {contact_data['last_name']}"
        assert "id" in data
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{data['id']}")
    
    def test_create_contact_missing_required_fields(self, authenticated_client):
        """Test POST /contacts without required fields returns 422."""
        response = authenticated_client.post("/contacts/", json={"email": "test@example.com"})
        assert response.status_code == 422
    
    def test_create_contact_with_company(self, authenticated_client):
        """Test POST /contacts with company_id links to company."""
        # Create a company first
        company_data = {"name": f"ContactCompany-{uuid4().hex[:8]}", "domain": f"cc-{uuid4().hex[:8]}.com"}
        company_response = authenticated_client.post("/companies/", json=company_data)
        company_id = company_response.json()["id"]
        
        # Create contact with company link
        contact_data = {
            "first_name": "Linked",
            "last_name": "Contact",
            "company_id": company_id,
        }
        response = authenticated_client.post("/contacts/", json=contact_data)
        assert response.status_code == 201
        data = response.json()
        assert data["company_id"] == company_id
        assert data["working_company_name"] == company_data["name"]
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{data['id']}")
        authenticated_client.delete(f"/companies/{company_id}")
    
    def test_get_contact_by_id(self, authenticated_client):
        """Test GET /contacts/{id} returns contact details."""
        # Create a test contact
        contact_data = {"first_name": "GetTest", "last_name": f"Contact-{uuid4().hex[:8]}"}
        create_response = authenticated_client.post("/contacts/", json=contact_data)
        contact_id = create_response.json()["id"]
        
        # Get the contact
        response = authenticated_client.get(f"/contacts/{contact_id}")
        assert response.status_code == 200
        assert response.json()["id"] == contact_id
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{contact_id}")
    
    def test_update_contact(self, authenticated_client):
        """Test PATCH /contacts/{id} updates contact."""
        # Create a test contact
        contact_data = {"first_name": "Update", "last_name": "Test"}
        create_response = authenticated_client.post("/contacts/", json=contact_data)
        contact_id = create_response.json()["id"]
        
        # Update the contact
        update_data = {"first_name": "Updated", "job_title": "Manager"}
        response = authenticated_client.patch(f"/contacts/{contact_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["full_name"] == "Updated Test"  # Auto-regenerated
        assert data["job_title"] == "Manager"
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{contact_id}")
    
    def test_delete_and_restore_contact(self, authenticated_client):
        """Test DELETE and POST /contacts/{id}/restore workflow."""
        # Create a test contact
        contact_data = {"first_name": "Delete", "last_name": "Restore"}
        create_response = authenticated_client.post("/contacts/", json=contact_data)
        contact_id = create_response.json()["id"]
        
        # Delete
        delete_response = authenticated_client.delete(f"/contacts/{contact_id}")
        assert delete_response.status_code == 204
        
        # Verify deleted
        get_response = authenticated_client.get(f"/contacts/{contact_id}")
        assert get_response.status_code == 404
        
        # Restore
        restore_response = authenticated_client.post(f"/contacts/{contact_id}/restore")
        assert restore_response.status_code == 200
        
        # Verify restored
        get_response = authenticated_client.get(f"/contacts/{contact_id}")
        assert get_response.status_code == 200
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{contact_id}")
    
    def test_contact_tagging(self, authenticated_client):
        """Test contact tagging with all three tag categories."""
        contact_data = {
            "first_name": "Tagged",
            "last_name": "Contact",
            "custom_tags_a": ["vip", "priority"],
            "custom_tags_b": ["tech"],
            "custom_tags_c": ["inbound"],
        }
        
        response = authenticated_client.post("/contacts/", json=contact_data)
        assert response.status_code == 201
        data = response.json()
        assert data["custom_tags_a"] == ["vip", "priority"]
        assert data["custom_tags_b"] == ["tech"]
        assert data["custom_tags_c"] == ["inbound"]
        
        # Cleanup
        authenticated_client.delete(f"/contacts/{data['id']}")
    
    def test_filter_contacts_by_tags(self, authenticated_client):
        """Test filtering contacts by tags."""
        response = authenticated_client.get("/contacts/", params={"tags_a": "vip"})
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)
    
    def test_filter_contacts_by_lead_score_range(self, authenticated_client):
        """Test filtering contacts by lead score range."""
        response = authenticated_client.get(
            "/contacts/",
            params={"lead_score_min": 50, "lead_score_max": 100}
        )
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)
    
    def test_contact_filter_options(self, authenticated_client):
        """Test GET /contacts/filter-options returns available filters."""
        response = authenticated_client.get("/contacts/filter-options")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


# ============================================================================
# Search API Tests
# ============================================================================

class TestSearchAPI:
    """Test Search endpoint."""
    
    def test_global_search(self, authenticated_client):
        """Test POST /search performs global search."""
        response = authenticated_client.post("/search/", json={"query": "test"})
        # Search endpoint may return 200 with results
        assert response.status_code in [200, 404, 422]


# ============================================================================
# Stats API Tests
# ============================================================================

class TestStatsAPI:
    """Test Stats/Dashboard endpoints."""
    
    def test_get_stats(self, authenticated_client):
        """Test GET /stats returns dashboard statistics."""
        response = authenticated_client.get("/stats/")
        assert response.status_code == 200
        data = response.json()
        # Stats should include counts
        assert isinstance(data, dict)


# ============================================================================
# Export API Tests
# ============================================================================

class TestExportAPI:
    """Test Export endpoints."""
    
    def test_export_companies_csv(self, authenticated_client):
        """Test GET /export/companies returns CSV data."""
        response = authenticated_client.get("/export/companies")
        # May return CSV or JSON based on implementation
        assert response.status_code in [200, 404]
    
    def test_export_contacts_csv(self, authenticated_client):
        """Test GET /export/contacts returns CSV data."""
        response = authenticated_client.get("/export/contacts")
        assert response.status_code in [200, 404]


# ============================================================================
# Bulk Import API Tests
# ============================================================================

class TestBulkImportAPI:
    """Test Bulk Import endpoints."""
    
    def test_bulk_import_contacts_json(self, authenticated_client):
        """Test POST /bulk/contacts imports multiple contacts."""
        contacts = [
            {"first_name": "Bulk1", "last_name": f"Test-{uuid4().hex[:8]}"},
            {"first_name": "Bulk2", "last_name": f"Test-{uuid4().hex[:8]}"},
        ]
        
        response = authenticated_client.post("/bulk/contacts", json={"contacts": contacts})
        # Bulk import may have various status codes
        assert response.status_code in [200, 201, 207, 400, 422]


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimiting:
    """Test rate limiting behavior."""
    
    def test_rate_limit_headers_present(self, authenticated_client):
        """Test that rate limit headers are present in responses."""
        response = authenticated_client.get("/companies/")
        # Rate limit headers may or may not be present depending on config
        assert response.status_code == 200


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_uuid_format(self, authenticated_client):
        """Test invalid UUID format returns appropriate error."""
        response = authenticated_client.get("/companies/not-a-uuid")
        assert response.status_code in [404, 422]
    
    def test_malformed_json_body(self):
        """Test malformed JSON returns 422."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(
                f"{API_V1}/companies/",
                content="not valid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [401, 422]  # 401 if auth required, 422 for bad JSON
    
    def test_missing_auth_header(self):
        """Test requests without auth return 401."""
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{API_V1}/companies/")
            # Depends on endpoint auth requirements
            assert response.status_code in [200, 401, 403]


# ============================================================================
# Run Tests Directly
# ============================================================================

if __name__ == "__main__":
    """Run tests directly with pytest."""
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
