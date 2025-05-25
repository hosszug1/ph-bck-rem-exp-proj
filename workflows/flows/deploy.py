"""Deployment script for Prefect flows."""

import asyncio

from prefect import serve

from workflows.constants import BACKGROUND_REMOVAL_DEPLOYMENT, BACKGROUND_REMOVAL_FLOW
from workflows.flows.background_remover import background_removal_flow


async def deploy_flows() -> None:
    """Deploy flows for serving."""

    # Create deployment for background removal flow
    deployment = await background_removal_flow.to_deployment(
        name=f"{BACKGROUND_REMOVAL_DEPLOYMENT}/{BACKGROUND_REMOVAL_FLOW}",
        description="Background removal flow for parallel image processing",
        tags=["background-removal", "batch", "parallel"],
        version="1.0.0",
    )

    # Serve the deployment (easiest way to run both the worker and the code itself).
    await serve(deployment)


if __name__ == "__main__":
    asyncio.run(deploy_flows())
