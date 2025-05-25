"""Tests for background remover router."""

import http

from fastapi.testclient import TestClient

from app.constants import (
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_ZIP,
    SINGLE_IMAGE_FILENAME,
    ZIP_FILENAME,
)
from app.routers.background_remover import router

# Module-level constants
TEST_URL = "https://example.com/test_image.jpg"


async def test_remove_background_success(
    mocker, photoroom_client_mock, test_image_data, processed_image_data
):
    """Test successful background removal from URL."""
    # Mock fetch_image to return test image data
    mock_fetch = mocker.patch(
        "app.routers.background_remover.fetch_image", return_value=test_image_data
    )

    # Create a test client with our router
    client = TestClient(router)
    client.app.dependency_overrides = {
        "app.routers.background_remover.get_photoroom_client": lambda: photoroom_client_mock
    }

    # Setup photoroom_client_mock
    photoroom_client_mock.remove_background.return_value = processed_image_data

    # Make request
    response = await client.post(
        "/api/v1/remove-background", json={"image_url": TEST_URL}
    )

    # Check response
    assert response.status_code == http.HTTPStatus.OK
    assert response.content == processed_image_data
    assert response.headers["Content-Type"] == MEDIA_TYPE_IMAGE
    assert (
        response.headers["Content-Disposition"]
        == f"attachment; filename={SINGLE_IMAGE_FILENAME}"
    )

    # Verify dependencies were called correctly
    mock_fetch.assert_called_once_with(TEST_URL)
    photoroom_client_mock.remove_background.assert_called_once_with(test_image_data)


async def test_remove_backgrounds_batch_success(
    mocker, photoroom_client_mock, test_image_data, processed_image_data
):
    """Test successful batch background removal."""
    # Mock fetch_image to return test image data
    mock_fetch = mocker.patch(
        "app.routers.background_remover.fetch_image", return_value=test_image_data
    )

    # Mock create_zip_archive
    mock_zip = mocker.patch(
        "app.routers.background_remover.create_zip_archive",
        return_value=b"mock_zip_data",
    )

    # Create a test client with our router
    client = TestClient(router)
    client.app.dependency_overrides = {
        "app.routers.background_remover.get_photoroom_client": lambda: photoroom_client_mock
    }

    # Setup photoroom_client_mock
    photoroom_client_mock.remove_background.return_value = processed_image_data

    # Make request with multiple URLs
    urls = [f"{TEST_URL}?id=1", f"{TEST_URL}?id=2"]
    response = await client.post(
        "/api/v1/remove-backgrounds", json={"image_urls": urls}
    )

    # Check response
    assert response.status_code == http.HTTPStatus.OK
    assert response.content == b"mock_zip_data"
    assert response.headers["Content-Type"] == MEDIA_TYPE_ZIP
    assert (
        response.headers["Content-Disposition"]
        == f"attachment; filename={ZIP_FILENAME}"
    )

    # Verify dependencies were called correctly
    assert mock_fetch.call_count == 2
    assert photoroom_client_mock.remove_background.call_count == 2
    mock_zip.assert_called_once()

    # Check that zip was created with the right data
    zip_call_args = mock_zip.call_args[0][0]
    assert len(zip_call_args) == 2
    assert all(url in [item[0] for item in zip_call_args] for url in urls)


async def test_remove_backgrounds_batch_empty(client):
    """Test batch endpoint with empty URLs list."""
    response = await client.post("/api/v1/remove-backgrounds", json={"image_urls": []})

    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert "At least one image URL is required" in response.text


async def test_remove_backgrounds_batch_too_many(client):
    """Test batch endpoint with too many URLs."""
    # Create a list with MAX_BATCH_SIZE + 1 URLs
    from app.constants import MAX_BATCH_SIZE

    urls = [f"{TEST_URL}?id={i}" for i in range(MAX_BATCH_SIZE + 1)]

    response = await client.post(
        "/api/v1/remove-backgrounds", json={"image_urls": urls}
    )

    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert "Maximum" in response.text
