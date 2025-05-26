import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(photoroom_client_mock):
    """Fixture providing a TestClient for the parallel router."""
    app.state.photoroom_client = photoroom_client_mock
    return TestClient(app)
