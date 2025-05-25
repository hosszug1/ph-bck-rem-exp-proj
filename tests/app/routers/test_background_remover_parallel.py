"""Tests for parallel background remover router."""

import http
from uuid import UUID

from fastapi.testclient import TestClient

from app.constants import (
    BACKGROUND_REMOVAL_DEPLOYMENT,
    BACKGROUND_REMOVAL_FLOW,
    MAX_BATCH_SIZE,
)
from app.routers.background_remover_parallel import router

# Module-level constants
TEST_URL = "https://example.com/test_image.jpg"
MOCK_FLOW_ID = "12345678-1234-5678-1234-567812345678"


async def test_start_batch_processing_success(mocker, photoroom_client_mock):
    """Test successful start of batch processing."""
    # Mock run_deployment
    mock_flow_run = mocker.MagicMock()
    mock_flow_run.id = UUID(MOCK_FLOW_ID)
    mock_run_deployment = mocker.patch(
        "app.routers.background_remover_parallel.run_deployment",
        return_value=mock_flow_run,
    )

    # Create a test client with our router
    client = TestClient(router)
    client.app.dependency_overrides = {
        "app.routers.background_remover_parallel.get_photoroom_client": lambda: photoroom_client_mock
    }

    # Setup photoroom_client_mock
    photoroom_client_mock.api_key = "test_api_key"
    photoroom_client_mock.base_url = "https://test.example.com"

    # Make request with multiple URLs
    urls = [f"{TEST_URL}?id=1", f"{TEST_URL}?id=2"]
    response = await client.post(
        "/api/v2/remove-backgrounds", json={"image_urls": urls}
    )

    # Check response
    assert response.status_code == http.HTTPStatus.OK
    response_data = response.json()

    assert len(response_data["flow_ids"]) == 2
    assert all(flow_id == MOCK_FLOW_ID for flow_id in response_data["flow_ids"])
    assert response_data["status"] == "RUNNING"
    assert response_data["image_count"] == 2

    # Verify run_deployment was called correctly
    assert mock_run_deployment.call_count == 2
    for call_args in mock_run_deployment.call_args_list:
        kwargs = call_args[1]
        assert (
            kwargs["name"]
            == f"{BACKGROUND_REMOVAL_FLOW}/{BACKGROUND_REMOVAL_DEPLOYMENT}"
        )
        assert "image_url" in kwargs["parameters"]
        assert kwargs["parameters"]["api_key"] == "test_api_key"
        assert kwargs["parameters"]["api_url"] == "https://test.example.com"


async def test_start_batch_processing_empty(client):
    """Test batch endpoint with empty URLs list."""
    response = await client.post("/api/v2/remove-backgrounds", json={"image_urls": []})

    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert "At least one image URL is required" in response.text


async def test_start_batch_processing_too_many(client):
    """Test batch endpoint with too many URLs."""
    # Create a list with MAX_BATCH_SIZE + 1 URLs
    urls = [f"{TEST_URL}?id={i}" for i in range(MAX_BATCH_SIZE + 1)]

    response = await client.post(
        "/api/v2/remove-backgrounds", json={"image_urls": urls}
    )

    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert "Maximum" in response.text


async def test_get_batch_results_success(mocker):
    """Test successful retrieval of batch results."""
    # Mock Prefect client
    mock_client = mocker.AsyncMock()
    mocker.patch(
        "app.routers.background_remover_parallel.get_client",
        return_value=mock_client,
    )
    mock_client.__aenter__.return_value = mock_client

    # Mock flow run with completed state
    mock_flow_run = mocker.AsyncMock()
    mock_flow_run.state.is_completed.return_value = True
    mock_flow_run.state.result.return_value = {
        "url": "https://processed.example.com/image.png",
        "original_url": TEST_URL,
        "error": None,
    }
    mock_client.read_flow_run.return_value = mock_flow_run

    # Create a test client with our router
    client = TestClient(router)

    # Make request with flow IDs
    response = await client.post(
        "/api/v2/remove-backgrounds/results", json={"flow_ids": [MOCK_FLOW_ID]}
    )

    # Check response
    assert response.status_code == http.HTTPStatus.OK
    response_data = response.json()

    assert response_data["total_count"] == 1
    assert response_data["success_count"] == 1
    assert MOCK_FLOW_ID in response_data["results"]
    assert response_data["results"][MOCK_FLOW_ID]["success"] is True
    assert (
        response_data["results"][MOCK_FLOW_ID]["processed_url"]
        == "https://processed.example.com/image.png"
    )

    # Verify client was called correctly
    mock_client.read_flow_run.assert_called_once_with(UUID(MOCK_FLOW_ID))


async def test_get_batch_results_empty(client):
    """Test results endpoint with empty flow IDs list."""
    response = await client.post(
        "/api/v2/remove-backgrounds/results", json={"flow_ids": []}
    )

    assert response.status_code == http.HTTPStatus.BAD_REQUEST
    assert "At least one flow ID is required" in response.text
