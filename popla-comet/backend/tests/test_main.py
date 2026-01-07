"""Tests for the main FastAPI application."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint returns correct information."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_api_status_endpoint():
    """Test the API status endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert data["status"] == "operational"
    assert "features" in data


@pytest.mark.asyncio
async def test_openapi_docs_available():
    """Test that OpenAPI documentation is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_404_not_found():
    """Test that non-existent endpoints return 404."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/nonexistent")
    
    assert response.status_code == 404
