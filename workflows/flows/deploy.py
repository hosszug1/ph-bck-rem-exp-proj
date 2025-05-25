"""Deployment script for Prefect flows."""

import click
from prefect.docker.docker_image import DockerImage

# from prefect import aserve
from workflows.constants import (
    BACKGROUND_REMOVAL_DEPLOYMENT,
    DEFAULT_WORKER_POOL,
    FLOW_DOCKERFILE,
)
from workflows.flows.background_remover import background_removal_flow


@click.group()
def cli() -> None:
    """CLI for managing Prefect flows."""
    pass


@cli.command()
@click.option(
    "--name",
    default=BACKGROUND_REMOVAL_DEPLOYMENT,
    show_default=True,
    help="Name of the deployment.",
)
@click.option(
    "--work-pool-name", default=DEFAULT_WORKER_POOL, help="Name of the work pool."
)
@click.option(
    "--image",
    required=True,
    help="Docker image to use for the deployment (only for docker pool type).",
)
@click.option(
    "--push",
    is_flag=True,
    help="Whether to push the Docker image (only for docker pool type).",
)
def deploy(
    name: str,
    work_pool_name: str,
    image: str,
    push: bool = False,
) -> None:
    """Deploy a Prefect flow."""
    background_removal_flow.deploy(
        name=name,
        work_pool_name=work_pool_name,
        image=DockerImage(name=image, dockerfile=FLOW_DOCKERFILE),
        push=push,
    )


if __name__ == "__main__":
    cli()
