"""Background removal router with endpoints for single and batch processing."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.clients.photoroom import PhotoroomClient
from app.constants import (
    MAX_BATCH_SIZE,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_ZIP,
    SINGLE_IMAGE_FILENAME,
    ZIP_FILENAME,
)
from app.dependencies import get_photoroom_client
from app.helpers.image import create_zip_archive, fetch_image
from app.models.background_remover import BatchImageRequest, ImageRequest

router = APIRouter(prefix="/api/v1", tags=["background-removal"])


@router.post("/remove-background")
async def remove_background(
    request: ImageRequest,
    photoroom_client: PhotoroomClient = Depends(get_photoroom_client),
) -> Response:
    """Remove background from a single image URL and return the processed image.

    Args:
        request: ImageRequest containing the image URL
        photoroom_client: PhotoroomClient dependency

    Returns:
        The processed image with background removed as bytes
    """
    # Fetch image
    image_bytes = await fetch_image(str(request.image_url))

    # Remove background
    processed_image = await photoroom_client.remove_background(image_bytes)

    # Return the processed image as bytes
    return Response(
        content=processed_image,
        media_type=MEDIA_TYPE_IMAGE,
        headers={
            "Content-Disposition": f"attachment; filename={SINGLE_IMAGE_FILENAME}"
        },
    )


@router.post("/remove-backgrounds")
async def remove_backgrounds_batch(
    request: BatchImageRequest,
    photoroom_client: PhotoroomClient = Depends(get_photoroom_client),
) -> Response:
    """Remove backgrounds from multiple image URLs and return as a ZIP archive.

    Args:
        request: BatchImageRequest containing multiple image URLs
        photoroom_client: PhotoroomClient dependency

    Returns:
        ZIP archive containing all successfully processed images
    """
    if not request.image_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image URL is required",
        )

    if len(request.image_urls) > MAX_BATCH_SIZE:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed per batch request",
        )

    # Process all images in parallel
    async def process_image_for_batch(url: str) -> tuple[str, bytes | None]:
        """Process image and return URL and processed bytes."""
        try:
            image_bytes = await fetch_image(url)
            processed_image = await photoroom_client.remove_background(image_bytes)
            return url, processed_image
        except Exception:
            return url, None

    tasks = [process_image_for_batch(str(url)) for url in request.image_urls]
    results = await asyncio.gather(*tasks)

    # Filter successful results
    successful_results = [(url, img) for url, img in results if img is not None]

    if not successful_results:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process any of the provided images",
        )

    # Create ZIP archive using helper function
    zip_content = create_zip_archive(successful_results)

    return Response(
        content=zip_content,
        media_type=MEDIA_TYPE_ZIP,
        headers={"Content-Disposition": f"attachment; filename={ZIP_FILENAME}"},
    )
