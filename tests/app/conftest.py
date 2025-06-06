"""Common test fixtures for the app module."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.clients.redacted_service import RedactedServiceClient
from app.config import Settings
from app.main import app as main_app


@pytest.fixture
def test_image_url():
    """Fixture providing a test image URL."""
    return "https://example.com/test_image.jpg"


@pytest.fixture
def test_image_data():
    """Fixture providing mock image data."""
    return b"mock_image_data"


@pytest.fixture
def processed_image_data():
    """Fixture providing mock processed image data."""
    return b"mock_processed_image_data"


@pytest.fixture
def settings_override(monkeypatch):
    """Fixture providing settings override for testing."""
    # Mock environment variables for testing
    monkeypatch.setenv("REDACTED_SERVICE_API_KEY", "test_api_key")
    monkeypatch.setenv("REDACTED_SERVICE_API_URL", "https://test.example.com")
    return Settings()


@pytest.fixture
def redacted_service_client_mock(processed_image_data):
    """Fixture providing a mocked RedactedServiceClient."""
    client = MagicMock(spec=RedactedServiceClient)
    client.api_key = "test_api_key"
    client.base_url = "https://test.example.com"
    client.remove_background.return_value = processed_image_data
    client.remove_background_sync.return_value = processed_image_data
    return client


@pytest.fixture
def app(redacted_service_client_mock):
    """Fixture providing a test FastAPI app with mocked dependencies."""
    app = FastAPI()

    # Mimic the lifespan context to set up the app state
    app.state.redacted_service_client = redacted_service_client_mock

    return app


@pytest.fixture
def test_client(app):
    """Fixture providing a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def main_test_client(redacted_service_client_mock):
    """Fixture providing a TestClient for the main FastAPI app."""
    main_app.state.redacted_service_client = redacted_service_client_mock
    return TestClient(main_app)
