"""Thin client implementations for external services."""

import httpx


class PhotoroomClient:
    """Simple client for Photoroom background removal API."""

    def __init__(self, api_url: str, api_key: str):
        """Initialize the Photoroom client.

        Args:
            api_url: The Photoroom API URL
            api_key: The Photoroom API key
        """
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {"x-api-key": self.api_key}

    async def remove_background(self, image_bytes: bytes) -> bytes:
        """Remove background from image bytes.

        Args:
            image_bytes: The image data as bytes

        Returns:
            The processed image with background removed as bytes
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image_file": image_bytes}

            response = await client.post(
                f"{self.api_url}/v1/segment",
                headers=self.headers,
                files=files,
            )
            response.raise_for_status()
            return response.content
