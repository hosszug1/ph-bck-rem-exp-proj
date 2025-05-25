"""Client for interacting with the Photoroom API."""

import httpx
from fastapi import HTTPException, status

from app.constants import DEFAULT_TIMEOUT, IMAGE_FILE_PARAM, SEGMENTATION_ENDPOINT


class PhotoroomClient:
    """Client for Photoroom background removal API."""

    def __init__(self, api_url: str, api_key: str):
        """Initialize the Photoroom client.

        Args:
            api_key: The Photoroom API key (required)
        """
        if not api_key:
            raise ValueError("Photoroom API key is required")

        self.api_key = api_key
        self.base_url = api_url
        self.headers = {
            "x-api-key": self.api_key,
        }

    async def remove_background(self, image_bytes: bytes) -> bytes:
        """Remove background from image bytes.

        Args:
            image_bytes: The image data as bytes

        Returns:
            The processed image with background removed as bytes

        Raises:
            HTTPException: If the API call fails
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            files = {IMAGE_FILE_PARAM: image_bytes}

            try:
                response = await client.post(
                    f"{self.base_url}/{SEGMENTATION_ENDPOINT}",
                    headers=self.headers,
                    files=files,
                )
                response.raise_for_status()
                return response.content

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Photoroom API error: {e.response.text}",
                ) from e
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to connect to Photoroom API: {str(e)}",
                ) from e

    def remove_background_sync(self, image_bytes: bytes) -> bytes:
        """Remove background from image bytes (synchronous version for parallel processing).

        Args:
            image_bytes: The image data as bytes

        Returns:
            The processed image with background removed as bytes

        Raises:
            HTTPException: If the API call fails
        """
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            files = {IMAGE_FILE_PARAM: image_bytes}

            try:
                response = client.post(
                    f"{self.base_url}/{SEGMENTATION_ENDPOINT}",
                    headers=self.headers,
                    files=files,
                )
                response.raise_for_status()
                return response.content

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Photoroom API error: {e.response.text}",
                ) from e
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to connect to Photoroom API: {str(e)}",
                ) from e
