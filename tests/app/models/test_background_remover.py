"""Tests for background remover models."""

import pytest
from pydantic import HttpUrl, ValidationError

from app.models.background_remover import (
    BatchImageRequest,
    BatchImageResponse,
    ImageRequest,
    ProcessingResult,
)


def test_image_request():
    """Test ImageRequest model."""
    # Valid URL
    image_request = ImageRequest(image_url="https://example.com/image.jpg")
    assert isinstance(image_request.image_url, HttpUrl)
    assert str(image_request.image_url) == "https://example.com/image.jpg"

    # Invalid URL
    with pytest.raises(ValidationError):
        ImageRequest(image_url="invalid-url")


def test_batch_image_request():
    """Test BatchImageRequest model."""
    # Valid URLs
    batch_request = BatchImageRequest(
        image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    )
    assert len(batch_request.image_urls) == 2
    assert all(isinstance(url, HttpUrl) for url in batch_request.image_urls)

    # Empty list
    batch_request_empty = BatchImageRequest(image_urls=[])
    assert len(batch_request_empty.image_urls) == 0

    # List with invalid URL
    with pytest.raises(ValidationError):
        BatchImageRequest(image_urls=["https://example.com/image1.jpg", "invalid-url"])


def test_processing_result():
    """Test ProcessingResult model."""
    # Success case
    success_result = ProcessingResult(
        url="https://example.com/image.jpg",
        success=True,
        processed_url="https://example.com/processed.jpg",
        original_url="https://example.com/original.jpg",
    )
    assert success_result.success is True
    assert success_result.error is None
    assert success_result.processed_url == "https://example.com/processed.jpg"

    # Error case
    error_result = ProcessingResult(
        url="https://example.com/image.jpg",
        success=False,
        error="Processing failed",
    )
    assert error_result.success is False
    assert error_result.error == "Processing failed"
    assert error_result.processed_url is None


def test_batch_image_response():
    """Test BatchImageResponse model."""
    # Create test results
    results = {
        "image1": ProcessingResult(
            url="https://example.com/image1.jpg",
            success=True,
            processed_url="https://example.com/processed1.jpg",
            original_url="https://example.com/original1.jpg",
        ),
        "image2": ProcessingResult(
            url="https://example.com/image2.jpg",
            success=False,
            error="Processing failed",
        ),
    }

    # Create response
    response = BatchImageResponse(
        total_count=2,
        success_count=1,
        results=results,
    )

    assert response.total_count == 2
    assert response.success_count == 1
    assert len(response.results) == 2
    assert response.results["image1"].success is True
    assert response.results["image2"].success is False
