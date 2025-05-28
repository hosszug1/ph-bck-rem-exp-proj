"""FastAPI dependencies for the background remover service."""

from fastapi import Request

from app.clients.redacted_service import RedactedServiceClient


def get_redacted_service_client(request: Request) -> RedactedServiceClient:
    """Get the RedactedServiceClient singleton from app state.

    Args:
        request: FastAPI request object containing app state

    Returns:
        RedactedServiceClient singleton instance
    """
    return request.app.state.redacted_service_client
