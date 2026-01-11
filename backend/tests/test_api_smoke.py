"""Basic smoke tests for the Flask app."""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
