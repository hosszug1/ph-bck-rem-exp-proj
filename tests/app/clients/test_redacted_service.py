"""Tests for the RedactedServiceClient."""

import http

import httpx
import pytest

from app.clients.redacted_service import RedactedServiceClient
from app.constants import SEGMENTATION_ENDPOINT

# Module-level constants
API_KEY = "test_api_key"
API_URL = "https://test.example.com"
TEST_URL = "https://example.com/test_image.jpg"


def test_init():
    """Test RedactedServiceClient initialization."""
    client = RedactedServiceClient(api_key=API_KEY, api_url=API_URL)
    assert client.api_key == API_KEY
    assert client.base_url == API_URL


def test_remove_background_sync(mocker, test_image_data, processed_image_data):
    """Test remove_background_sync method."""
    # Mock httpx.Client.post
    mock_response = mocker.MagicMock()
    mock_response.status_code = http.HTTPStatus.OK
    mock_response.content = processed_image_data

    mock_client = mocker.MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    mocker.patch("httpx.Client", return_value=mock_client)

    client = RedactedServiceClient(api_key=API_KEY, api_url=API_URL)
    result = client.remove_background_sync(test_image_data)

    # Check result
    assert result == processed_image_data

    # Verify httpx.Client.post was called with correct arguments
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{API_URL}/{SEGMENTATION_ENDPOINT}"
    assert "headers" in call_args[1]
    assert call_args[1]["headers"]["x-api-key"] == API_KEY


def test_remove_background_sync_failure(mocker, test_image_data):
    """Test remove_background_sync method handles errors."""
    # Mock httpx.Client.post with error response
    mock_response = mocker.MagicMock()
    mock_response.status_code = http.HTTPStatus.BAD_REQUEST
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=mocker.MagicMock(), response=mock_response
    )

    mock_client = mocker.MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    mocker.patch("httpx.Client", return_value=mock_client)

    client = RedactedServiceClient(api_key=API_KEY, api_url=API_URL)

    # Should raise exception on error
    with pytest.raises(httpx.HTTPStatusError):
        client.remove_background_sync(test_image_data)


async def test_remove_background(mocker, test_image_data, processed_image_data):
    """Test remove_background async method."""
    # Mock httpx.AsyncClient.post
    mock_response = mocker.MagicMock()
    mock_response.status_code = http.HTTPStatus.OK
    mock_response.content = processed_image_data

    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    client = RedactedServiceClient(api_key=API_KEY, api_url=API_URL)
    result = await client.remove_background(test_image_data)

    # Check result
    assert result == processed_image_data

    # Verify httpx.AsyncClient.post was called with correct arguments
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{API_URL}/{SEGMENTATION_ENDPOINT}"
    assert "headers" in call_args[1]
    assert call_args[1]["headers"]["x-api-key"] == API_KEY
