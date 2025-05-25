"""Tests for image helper functions."""

import http
import io
import zipfile

import httpx
import pytest
from fastapi import HTTPException

from app.constants import PNG_EXTENSION
from app.helpers.image import create_zip_archive, fetch_image

# Module-level constants
TEST_URL = "https://example.com/test_image.jpg"


async def test_fetch_image_success(mocker, test_image_data):
    """Test successful image fetch."""
    # Mock httpx.AsyncClient.get
    mock_response = mocker.MagicMock()
    mock_response.status_code = http.HTTPStatus.OK
    mock_response.content = test_image_data
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = mocker.MagicMock()

    # Mock the client and its context manager
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    result = await fetch_image(TEST_URL)

    # Check result
    assert result == test_image_data

    # Verify httpx.AsyncClient.get was called with the correct URL
    mock_client.get.assert_called_once_with(TEST_URL)


async def test_fetch_image_not_an_image(mocker):
    """Test handling of non-image content types."""
    # Mock httpx.AsyncClient.get with non-image content type
    mock_response = mocker.MagicMock()
    mock_response.status_code = http.HTTPStatus.OK
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = mocker.MagicMock()

    # Mock the client and its context manager
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    with pytest.raises(HTTPException) as exc_info:
        await fetch_image(TEST_URL)

    assert exc_info.value.status_code == http.HTTPStatus.BAD_REQUEST
    assert "URL does not point to an image" in str(exc_info.value.detail)


async def test_fetch_image_request_failure(mocker):
    """Test handling of request failures."""
    # Mock httpx.AsyncClient.get that raises an exception
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=mocker.MagicMock(), response=mock_response
    )

    # Mock the client and its context manager
    mock_client = mocker.AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_image(TEST_URL)


def test_create_zip_archive(test_image_data):
    """Test creating a ZIP archive from processed images."""
    # Create test data
    processed_images = [
        (f"{TEST_URL}?id=1", test_image_data),
        (f"{TEST_URL}?id=2", test_image_data),
        ("https://example.com/invalid.jpg", None),  # Test handling of None
    ]

    # Create ZIP archive
    result = create_zip_archive(processed_images)

    # Verify the result is a valid ZIP file with the expected content
    assert result is not None
    assert isinstance(result, bytes)

    # Read the ZIP archive to verify contents
    with zipfile.ZipFile(io.BytesIO(result)) as zip_file:
        # Should only have 2 files (not 3, since one image was None)
        assert len(zip_file.namelist()) == 2

        # Verify file naming pattern
        for i, filename in enumerate(zip_file.namelist()):
            # Extract content
            content = zip_file.read(filename)
            assert content == test_image_data

            # Check filename follows expected pattern
            assert filename.startswith(f"image_{i + 1}_")
            assert filename.endswith(PNG_EXTENSION)
