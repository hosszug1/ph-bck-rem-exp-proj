"""Parallel background removal router using Prefect for orchestration."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.clients.photoroom import PhotoroomClient
from app.constants import (
    BATCH_BACKGROUND_REMOVAL_DEPLOYMENT,
    BATCH_BACKGROUND_REMOVAL_FLOW,
    MAX_BATCH_SIZE,
    MEDIA_TYPE_ZIP,
)
from app.dependencies import get_photoroom_client
from app.helpers.image import create_zip_archive
from app.models.background_remover import BatchImageRequest
from prefect import get_client
from prefect.deployments import run_deployment

router = APIRouter(prefix="/api/v1/prefect", tags=["prefect-background-removal"])


@router.post("/remove-backgrounds-async")
async def start_batch_processing(
    request: BatchImageRequest,
    photoroom_client: PhotoroomClient = Depends(get_photoroom_client),
) -> dict:
    """Start batch background removal using Prefect flow (fire and forget).

    This endpoint starts a Prefect flow and returns immediately with the flow ID.
    Use the status endpoint to check progress and get results.

    Args:
        request: BatchImageRequest containing multiple image URLs
        photoroom_client: PhotoroomClient dependency

    Returns:
        Dictionary containing flow_id for tracking
    """
    if not request.image_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image URL is required",
        )

    if len(request.image_urls) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_BATCH_SIZE} images allowed per batch request",
        )

    # Get API credentials
    api_key = photoroom_client.api_key
    api_url = photoroom_client.base_url

    # Start the deployment asynchronously
    flow_run = await run_deployment(
        name=f"{BATCH_BACKGROUND_REMOVAL_DEPLOYMENT}/{BATCH_BACKGROUND_REMOVAL_FLOW}",
        parameters={
            "image_urls": [str(url) for url in request.image_urls],
            "api_url": api_url,
            "api_key": api_key,
        },
        flow_run_name=f"batch-processing-{len(request.image_urls)}-images",
    )

    return {
        "flow_id": str(flow_run.id),
        "message": f"Started processing {len(request.image_urls)} images",
        "status": "RUNNING",
        "image_count": len(request.image_urls),
    }


@router.get("/status/{flow_id}")
async def get_batch_status(flow_id: str) -> dict:
    """Get the status of a batch processing flow.

    Returns detailed status including partial results if available.

    Args:
        flow_id: The flow ID returned from start_batch_processing

    Returns:
        Dictionary with flow status, progress, and partial results
    """
    # Convert string to UUID
    flow_uuid = UUID(flow_id)

    # Get Prefect client
    async with get_client() as client:
        # Get flow run details
        flow_run = await client.read_flow_run(flow_uuid)

        if not flow_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        # Get task runs for this flow
        task_runs = await client.read_task_runs(
            flow_run_filter={"id": {"any_": [flow_uuid]}}
        )

        # Analyze task progress
        total_tasks = len(task_runs)
        completed_tasks = len(
            [t for t in task_runs if t.state and t.state.is_completed()]
        )
        successful_tasks = len(
            [
                t
                for t in task_runs
                if t.state and t.state.is_completed() and not t.state.is_failed()
            ]
        )
        failed_tasks = len([t for t in task_runs if t.state and t.state.is_failed()])

        # Get flow state
        flow_state = flow_run.state
        is_running = flow_state and flow_state.is_running()
        is_completed = flow_state and flow_state.is_completed()
        is_failed = flow_state and flow_state.is_failed()

        response_data = {
            "flow_id": flow_id,
            "status": flow_state.type if flow_state else "UNKNOWN",
            "is_running": is_running,
            "is_completed": is_completed,
            "is_failed": is_failed,
            "progress": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "completion_percentage": round(
                    (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                    2,
                ),
            },
            "start_time": flow_run.start_time.isoformat()
            if flow_run.start_time
            else None,
            "end_time": flow_run.end_time.isoformat() if flow_run.end_time else None,
        }

        # If flow is completed, try to get results
        if is_completed and not is_failed:
            try:
                result = await flow_run.state.result()
                if result and isinstance(result, dict):
                    response_data["results"] = {
                        "total_images": result.get("total_images", 0),
                        "successful_count": result.get("successful_count", 0),
                        "failed_count": result.get("failed_count", 0),
                        "processing_complete": result.get("processing_complete", False),
                    }

                    # Don't include actual image data in status response
                    if "failed_results" in result:
                        response_data["results"]["failed_urls"] = [
                            f["url"] for f in result["failed_results"]
                        ]

            except Exception as e:
                response_data["result_error"] = f"Could not retrieve results: {str(e)}"

        return response_data


@router.get("/download/{flow_id}")
async def download_batch_results(flow_id: str) -> Response:
    """Download results from a completed batch processing flow.

    Returns a ZIP file with all successfully processed images.
    For partial results, includes only completed images with appropriate messaging.

    Args:
        flow_id: The flow ID returned from start_batch_processing

    Returns:
        ZIP file response with processed images
    """
    # Convert string to UUID
    flow_uuid = UUID(flow_id)

    # Get Prefect client
    async with get_client() as client:
        # Get flow run details
        flow_run = await client.read_flow_run(flow_uuid)

        if not flow_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        # Check if flow has any results
        flow_state = flow_run.state
        if not flow_state or not (flow_state.is_completed() or flow_state.is_running()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Flow has not completed or is not running. No results available.",
            )

        if flow_state.is_completed():
            # Flow is complete, get final results
            result = await flow_state.result()
        else:
            # Flow is still running, get partial results
            # This is a simplified approach - in production you'd implement
            # more sophisticated partial result collection
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Flow is still running. Please check status endpoint for progress.",
            )

        if not result or not isinstance(result, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve flow results",
            )

        successful_results = result.get("successful_results", [])

        if not successful_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No successfully processed images found",
            )

        # Create ZIP archive
        zip_content = create_zip_archive(successful_results)

        # Determine filename based on completion status
        total_count = result.get("total_images", len(successful_results))
        successful_count = len(successful_results)
        is_partial = successful_count < total_count

        filename_prefix = "partial_" if is_partial else "complete_"
        filename = (
            f"{filename_prefix}batch_results_{successful_count}_of_{total_count}.zip"
        )

        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Flow-ID": flow_id,
            "X-Total-Images": str(total_count),
            "X-Successful-Images": str(successful_count),
            "X-Is-Partial": str(is_partial).lower(),
        }

        return Response(
            content=zip_content,
            media_type=MEDIA_TYPE_ZIP,
            headers=headers,
        )
