import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(redacted_service_client_mock):
    """Fixture providing a TestClient for the parallel router."""
    app.state.redacted_service_client = redacted_service_client_mock
    return TestClient(app)
