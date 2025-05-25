"""
Invoke tasks for development automation.

Run `invoke --list` to see all available tasks.
"""

from invoke import Context, task


@task
def run_lint(ctx: Context) -> None:
    """Run ruff to check and format the codebase."""
    ctx.run("uv run ruff format .")
    ctx.run("uv run ruff check . --fix")


@task
def run_tests(ctx: Context) -> None:
    """Run all tests with coverage."""

    ctx.run("pytest .")


@task
def gen_app_reqs(ctx: Context) -> None:
    """Generate requirements.txt for the fastapi app from uv.lock file."""
    ctx.run("uv export > app/requirements.txt")


@task
def gen_workflows_reqs(ctx: Context) -> None:
    """Generate requirements.txt for workflows from uv.lock file."""
    ctx.run("uv export > workflows/requirements.txt")


@task
def gen_all_reqs(ctx: Context) -> None:
    """Generate requirements.txt from uv.lock file."""
    gen_app_reqs(ctx)
    gen_workflows_reqs(ctx)
