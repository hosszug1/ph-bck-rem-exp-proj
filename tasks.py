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
