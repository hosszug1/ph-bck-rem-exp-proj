"""FastAPI dependencies for the background remover service."""

from fastapi import Request

from app.clients.photoroom import PhotoroomClient


def get_photoroom_client(request: Request) -> PhotoroomClient:
    """Get the PhotoroomClient singleton from app state.

    Args:
        request: FastAPI request object containing app state

    Returns:
        PhotoroomClient singleton instance
    """
    return request.app.state.photoroom_client
