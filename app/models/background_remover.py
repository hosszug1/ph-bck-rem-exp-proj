"""Pydantic models for the background remover service."""

from pydantic import BaseModel, HttpUrl


class ImageRequest(BaseModel):
    """Request model for single image background removal."""

    image_url: HttpUrl


class BatchImageRequest(BaseModel):
    """Request model for batch image background removal."""

    image_urls: list[HttpUrl]


class ProcessingResult(BaseModel):
    """Result of processing a single image."""

    url: str
    success: bool
    error: str | None = None
    storage_url: str | None = None
    original_url: str | None = None


class BatchImageResponse(BaseModel):
    """Response model for batch image background removal."""

    total_count: int
    success_count: int
    results: dict[str, ProcessingResult]
