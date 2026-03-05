"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health():
    """Health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_live():
    """Liveness probe returns 200."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_health_ready():
    """Readiness probe returns 200."""
    response = client.get("/health/ready")
    assert response.status_code == 200


def test_metrics():
    """Prometheus metrics endpoint returns 200."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "python_" in response.text


def test_v1_health():
    """Versioned health endpoint works."""
    response = client.get("/v1/health")
    assert response.status_code == 200
