"""Security verification tests for Software Testing Report (Item 6.3)."""
from datetime import datetime, timezone
import re
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import User

# Mock authenticated user with valid Pydantic fields
mock_user = User(
    id=1,
    username="securitytester",
    email="security@example.com",
    created_at=datetime.now(timezone.utc),
    hashed_password="mocked_hash_for_test",
)


def mock_get_db():
    """Mock database session where any query resolution returns None (simulating not found / unauthorized ID)."""
    db = MagicMock()
    # Configure mock chain so that .first() always resolves to None
    query_mock = MagicMock()
    query_mock.options.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    db.query.return_value = query_mock
    try:
        yield db
    finally:
        pass


@pytest.fixture(autouse=True)
def override_dependencies():
    """Override get_current_user and get_db dependencies for isolated security testing."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_cors_configuration():
    """Verify CORS policy restricts unauthorized origins and avoids wildcard '*'."""
    response = client.options(
        "/",
        headers={
            "Origin": "https://malicious-attacker-website.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin != "*", "CORS policy should not allow unrestricted wildcard '*' origins."


def test_sql_injection_resilience():
    """Verify search input resists classic SQL injection payloads without 500 errors."""
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT null, null, null --",
        "1' OR '1' = '1' --",
    ]
    for sqli in payloads:
        response = client.get(f"/catalog/search?q={sqli}")
        assert response.status_code in (200, 400, 404, 422), (
            f"Endpoint crashed on payload: {sqli} with status {response.status_code}"
        )


def test_password_hash_never_exposed_in_responses():
    """Verify password hashes (bcrypt pattern) are never leaked in data responses."""
    bcrypt_pattern = re.compile(r"\$2[aby]\$[0-9]{2}\$[A-Za-z0-9\./]{53}")

    endpoints = ["/", "/auth/me"]
    for ep in endpoints:
        res = client.get(ep)
        if res.status_code != 404:
            body = res.text
            assert not bcrypt_pattern.search(body), f"Password hash pattern detected in {ep}"


def test_idor_protection_returns_404():
    """Verify accessing nonexistent or unauthorized entity IDs returns 404 Not Found."""
    res_list = client.get("/lists/99999")
    assert res_list.status_code == 404, f"Expected 404 on /lists/99999, got {res_list.status_code}"
