"""Pydantic models for the background remover service."""

from pydantic import BaseModel, HttpUrl


class ImageRequest(BaseModel):
    """Request model for single image background removal."""

    image_url: HttpUrl


class BatchImageRequest(BaseModel):
    """Request model for batch image background removal."""

    image_urls: list[HttpUrl]


class ImageResponse(BaseModel):
    """Response model for single image background removal."""

    success: bool
    message: str
    original_url: str
    error: str | None = None


class BatchImageResponse(BaseModel):
    """Response model for batch image background removal."""

    results: list[ImageResponse]
    total_processed: int
    successful: int
    failed: int
