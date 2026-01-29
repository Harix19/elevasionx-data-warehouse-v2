import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_openapi_schema_generated(async_client: AsyncClient):
    """Test that the OpenAPI schema can be generated and is a valid JSON."""
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "components" in schema
    assert schema["info"]["title"] == "Leads Data Warehouse API"


@pytest.mark.anyio
async def test_docs_page_loads(async_client: AsyncClient):
    """Test that the Swagger UI page loads."""
    response = await async_client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
