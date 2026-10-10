"""Epic 1 - Backend Infrastructure and Database Foundation."""


def test_us01_health_returns_ok(client):
    """US-01: GET /health returns 200 and {"status": "healthy"}.

    This feature is already implemented, so this test is expected to pass.
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json().get("status") == "healthy"