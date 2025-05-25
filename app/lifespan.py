"""FastAPI lifespan management for background remover service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.photoroom import PhotoroomClient
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the lifespan of the FastAPI application.

    This creates a PhotoroomClient singleton on startup and stores it in app.state
    for use throughout the application lifecycle.
    """
    # Startup: Create PhotoroomClient singleton with API key from settings
    app.state.photoroom_client = PhotoroomClient(
        api_key=settings.photoroom_api_key, api_url=settings.photoroom_api_url
    )

    yield

    # Shutdown: Clean up if needed (PhotoroomClient doesn't need cleanup)
    pass
