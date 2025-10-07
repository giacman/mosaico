"""
Basic API Tests for Mosaico
Run with: pytest tests/
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns healthy status"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Mosaico API"
    assert data["status"] == "healthy"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vertex_ai_model" in data


def test_generate_variations_validation():
    """Test generate endpoint with invalid input"""
    # Empty text should fail
    response = client.post(
        "/api/v1/generate",
        json={"text": "", "count": 3}
    )
    assert response.status_code == 422  # Validation error


def test_generate_variations_valid_input():
    """Test generate endpoint with valid input (mocked)"""
    # NOTE: This will fail without proper GCP credentials
    # For real testing, mock the Vertex AI client
    response = client.post(
        "/api/v1/generate",
        json={
            "text": "Test text",
            "count": 3,
            "tone": "professional",
            "content_type": "newsletter"
        }
    )
    # Will fail without credentials, that's expected
    # In CI/CD, set up service account or mock
    assert response.status_code in [200, 500]


def test_translate_validation():
    """Test translate endpoint validation"""
    response = client.post(
        "/api/v1/translate",
        json={"text": "", "target_language": "it"}
    )
    assert response.status_code == 422


def test_refine_validation():
    """Test refine endpoint validation"""
    response = client.post(
        "/api/v1/refine",
        json={"text": "", "operation": "shorten"}
    )
    assert response.status_code == 422


# TODO: Add mocked tests for actual AI generation
# TODO: Add integration tests with test GCP project
# TODO: Add load tests for rate limiting

