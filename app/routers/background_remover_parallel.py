"""Parallel background removal router using Prefect for orchestration."""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from prefect import get_client
from prefect.deployments import run_deployment

from app.clients.redacted_service import RedactedServiceClient
from app.constants import (
    BACKGROUND_REMOVAL_DEPLOYMENT,
    BACKGROUND_REMOVAL_FLOW,
    MAX_BATCH_SIZE,
)
from app.dependencies import get_redacted_service_client
from app.models.background_remover import (
    BatchImageRequest,
    BatchImageResponse,
    BatchResultsRequest,
    ProcessingResult,
)

router = APIRouter(prefix="/api/v2", tags=["prefect-background-removal"])


@router.post("/remove-backgrounds")
async def start_batch_processing(
    request: BatchImageRequest,
    redacted_service_client: RedactedServiceClient = Depends(
        get_redacted_service_client
    ),
) -> dict:
    """Start batch background removal using individual Prefect flows.

    This endpoint starts a Prefect flow for each image and returns immediately with flow IDs.

    Args:
        request: BatchImageRequest containing multiple image URLs
        redacted_service_client: RedactedServiceClient dependency

    Returns:
        Dictionary containing flow_ids for tracking
    """
    if not request.image_urls:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="At least one image URL is required",
        )

    if len(request.image_urls) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Maximum {MAX_BATCH_SIZE} images allowed per batch request",
        )

    # Get API credentials
    api_key = redacted_service_client.api_key
    api_url = redacted_service_client.base_url

    # Start a flow for each image
    flow_ids = []
    for url in request.image_urls:
        flow_run = await run_deployment(
            name=f"{BACKGROUND_REMOVAL_FLOW}/{BACKGROUND_REMOVAL_DEPLOYMENT}",
            parameters={
                "image_url": str(url),
                "api_url": api_url,
                "api_key": api_key,
            },
            timeout=0,  # Don't wait for completion
        )
        flow_ids.append(str(flow_run.id))

    return {
        "flow_ids": flow_ids,
        "message": f"Started processing {len(request.image_urls)} images",
        "status": "RUNNING",
        "image_count": len(request.image_urls),
    }


@router.post("/remove-backgrounds/results")
async def get_batch_results(request: BatchResultsRequest) -> BatchImageResponse:
    """Get results for multiple flows.

    Returns processing results for the specified flow IDs, including partial results
    if some flows are still running.

    Args:
        request: BatchResultsRequest containing flow_ids list

    Returns:
        BatchImageResponse with information about processing success and URLs to the images
    """
    flow_ids = request.flow_ids
    if not flow_ids:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="At least one flow ID is required",
        )

    results = {}  # Changed from list to dictionary
    success_count = 0
    total_count = len(flow_ids)

    # Get Prefect client
    async with get_client() as client:
        for flow_id in flow_ids:
            try:
                # Convert string to UUID
                flow_uuid = UUID(flow_id)

                # Get flow run details
                flow_run = await client.read_flow_run(flow_uuid)

                # Default to not completed state
                results[flow_id] = ProcessingResult(
                    url=flow_id,
                    success=False,
                    error=None,
                    processed_url=None,
                    original_url=None,
                )

                # Check if flow is completed
                if flow_run.state.is_completed():
                    # Get flow result
                    result_data = await flow_run.state.result()
                    # Flow completed successfully
                    success_count += 1
                    results[flow_id] = ProcessingResult(
                        url=flow_id,
                        success=True,
                        error=result_data.get("error"),
                        processed_url=result_data.get("url"),
                        original_url=result_data.get("original_url", "unknown"),
                    )
            except Exception as e:
                # Error getting flow
                results[flow_id] = ProcessingResult(
                    url=flow_id,
                    success=False,
                    error=f"Error checking flow: {str(e)}",
                    processed_url=None,
                    original_url="unknown",
                )

    # Return response with all results
    return BatchImageResponse(
        total_count=total_count,
        success_count=success_count,
        results=results,
    )
