"""Prefect workflows for background removal processing."""

import httpx
from prefect import flow, get_run_logger, task

from app.clients.photoroom import PhotoroomClient


@task(retries=3, retry_delay_seconds=2, persist_result=True)
async def remove_background_single_image(
    image_url: str, api_url: str, api_key: str
) -> tuple[str, bytes | None, str | None]:
    """Remove background from a single image.

    This task processes one image and returns the result.
    Prefect can run multiple instances of this task in parallel across workers.

    Args:
        image_url: URL of the image to process
        api_url: Photoroom API URL
        api_key: Photoroom API key

    Returns:
        Tuple of (image_url, processed_image_bytes, error_message)
    """
    logger = get_run_logger()
    logger.info(f"Processing image: {image_url}")

    try:
        # Fetch image
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        # Process with Photoroom
        photoroom_client = PhotoroomClient(api_url, api_key)
        processed_image = await photoroom_client.remove_background(image_bytes)

        logger.info(f"Successfully processed: {image_url}")
        return image_url, processed_image, None

    except Exception as e:
        error_msg = f"Failed to process {image_url}: {str(e)}"
        logger.error(error_msg)
        return image_url, None, error_msg


@flow(name="batch-background-removal", persist_result=True)
async def batch_background_removal_flow(
    image_urls: list[str], api_url: str, api_key: str
) -> dict:
    """Flow to process multiple images in parallel.

    This flow creates separate tasks for each image, allowing Prefect
    to distribute them across multiple workers in production.

    Args:
        image_urls: list of image URLs to process
        api_url: Photoroom API URL
        api_key: Photoroom API key

    Returns:
        Dictionary with processing results and metadata
    """
    logger = get_run_logger()
    logger.info(f"Starting batch processing of {len(image_urls)} images")

    # Create tasks for each image - these will run in parallel
    tasks = [
        remove_background_single_image.submit(url, api_url, api_key)
        for url in image_urls
    ]

    # Wait for all tasks to complete
    results = []
    successful_results = []
    failed_results = []

    for task_future in tasks:
        try:
            url, image_bytes, error = await task_future.result()
            results.append(
                {
                    "url": url,
                    "success": error is None,
                    "error": error,
                    "has_data": image_bytes is not None,
                }
            )

            if error is None and image_bytes is not None:
                successful_results.append((url, image_bytes))
            else:
                failed_results.append({"url": url, "error": error})

        except Exception as e:
            # Handle task-level exceptions
            logger.error(f"Task execution failed: {str(e)}")
            failed_results.append({"url": "unknown", "error": str(e)})

    logger.info(
        f"Batch processing completed: {len(successful_results)} successful, {len(failed_results)} failed"
    )

    return {
        "total_images": len(image_urls),
        "successful_count": len(successful_results),
        "failed_count": len(failed_results),
        "successful_results": successful_results,
        "failed_results": failed_results,
        "processing_complete": True,
    }
