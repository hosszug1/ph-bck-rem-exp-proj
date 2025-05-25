"""Image processing helper functions."""

import io
import zipfile
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.constants import (
    DEFAULT_IMAGE_NAME,
    DEFAULT_TIMEOUT,
    PNG_EXTENSION,
    SAFE_FILENAME_CHARS,
)


async def fetch_image(url: str) -> bytes:
    """Fetch image from URL and return as bytes.

    Args:
        url: The image URL to fetch

    Returns:
        The image data as bytes

    Raises:
        HTTPException: If image fetch fails
    """
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(str(url))
        response.raise_for_status()

        # Check if content type is an image
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL does not point to an image. Content-Type: {content_type}",
            )

        return response.content


def create_zip_archive(processed_images: list[tuple[str, bytes]]) -> bytes:
    """Create a ZIP archive containing processed images.

    Args:
        processed_images: List of tuples containing (original_url, processed_image_bytes)

    Returns:
        ZIP archive bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, (url, processed_image) in enumerate(processed_images):
            if processed_image is not None:
                # Generate a safe filename from URL
                parsed_url = urlparse(url)
                filename = f"image_{i + 1}_{parsed_url.path.split('/')[-1] or DEFAULT_IMAGE_NAME}{PNG_EXTENSION}"
                # Remove any problematic characters
                filename = "".join(
                    c for c in filename if c.isalnum() or c in SAFE_FILENAME_CHARS
                )
                if not filename.endswith(PNG_EXTENSION):
                    filename += PNG_EXTENSION

                zip_file.writestr(filename, processed_image)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
