"""Prefect workflows for background removal processing."""

import time
from pathlib import Path

import httpx
from prefect import flow, get_run_logger

from workflows.clients.minio import MinioClient
from workflows.clients.redacted_service import RedactedServiceClient
from workflows.constants import (
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_RETRY_DELAY,
    MINIO_ACCESS_KEY,
    MINIO_BUCKET_NAME,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)


@flow(
    name="background-removal",
    retries=DEFAULT_RETRIES,
    retry_delay_seconds=DEFAULT_RETRY_DELAY,
    persist_result=True,
)
def background_removal_flow(image_url: str, api_url: str, api_key: str) -> dict:
    """Flow to process a single image and store result in MinIO.

    Args:
        image_url: URL of the image to process
        api_url: RedactedService API URL
        api_key: RedactedService API key

    Returns:
        Dictionary with processing results including the MinIO URL
    """
    logger = get_run_logger()
    logger.info(f"Processing image: {image_url}")

    # Fetch image
    with httpx.Client(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
        response = client.get(image_url)
        response.raise_for_status()
        image_bytes = response.content

    # Process with RedactedService
    redacted_service_client = RedactedServiceClient(api_url, api_key)
    processed_image = redacted_service_client.remove_background(image_bytes)

    # Generate a filename based on the original URL
    url_path = Path(image_url).name if "/" in image_url else f"image_{int(time.time())}"
    timestamp = int(time.time())
    filename = f"processed_{timestamp}_{url_path}"
    if not filename.lower().endswith(".png"):
        filename += ".png"

    # Upload to MinIO
    minio_client = MinioClient(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
    )

    # Upload the processed image to MinIO
    processed_url = minio_client.upload_image(
        processed_image,
        filename=filename,
        bucket_name=MINIO_BUCKET_NAME,
    )

    logger.info(f"Successfully processed and uploaded: {processed_url}")

    return {
        "url": processed_url,
        "original_url": image_url,
        "success": True,
        "error": None,
    }
