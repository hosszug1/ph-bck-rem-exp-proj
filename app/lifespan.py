"""FastAPI lifespan management for background remover service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.redacted_service import RedactedServiceClient
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the lifespan of the FastAPI application.

    This creates a RedactedServiceClient singleton on startup and stores it in app.state
    for use throughout the application lifecycle.
    """
    # Startup: Create RedactedServiceClient singleton with API key from settings
    app.state.redacted_service_client = RedactedServiceClient(
        api_key=settings.redacted_service_api_key,
        api_url=settings.redacted_service_api_url,
    )

    yield

    # Shutdown: Clean up if needed (RedactedServiceClient doesn't need cleanup)
    pass
