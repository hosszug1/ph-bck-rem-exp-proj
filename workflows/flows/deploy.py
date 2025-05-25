"""Deployment script for Prefect flows."""

import asyncio

from prefect import serve

from workflows.constants import BATCH_BACKGROUND_REMOVAL_DEPLOYMENT
from workflows.flows.background_remover import batch_background_removal_flow


async def deploy_flows() -> None:
    """Deploy flows for serving."""

    # Create deployment for batch background removal flow
    deployment = await batch_background_removal_flow.to_deployment(
        name=BATCH_BACKGROUND_REMOVAL_DEPLOYMENT,
        description="Batch background removal flow for parallel image processing",
        tags=["background-removal", "batch", "parallel"],
        version="1.0.0",
    )

    # Serve the deployment
    await serve(deployment)


if __name__ == "__main__":
    asyncio.run(deploy_flows())
