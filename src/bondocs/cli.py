"""Command-line interface for Bondocs.

Provides commands for initializing and running Bondocs.
"""

import subprocess
from pathlib import Path

import click
from rich import print  # type: ignore

from bondocs.core.config import config
from bondocs.core.errors import (
    ErrorSeverity,
    GitError,
    display_warning,
    exit_with_error,
    handle_errors,
    safe_execution,
)
from bondocs.document import (
    apply_patch,
    doc_manager,
    generate_readme_patch,
    update_changelog,
    update_runbooks,
)
from bondocs.git import git, summarize_diff
from bondocs.utils.templates import (
    BONDOCS_CONFIG,
    DEFAULT_README,
    PRE_COMMIT_CONFIG,
)


@click.group()
def app():
    """Bondocs – keep your README in sync automatically."""


def _create_file(path: Path, content: str, file_type: str) -> None:
    """Create a file if it doesn't exist.

    Args:
        path: Path to the file to create
        content: Content to write to the file
        file_type: Type of file for logging messages
    """
    if not path.exists():
        doc_manager.update_document(path, content)
        print(f"[green]Created {file_type}[/]")
    else:
        display_warning(f"{file_type} already exists")


@handle_errors(GitError, severity=ErrorSeverity.WARNING)
def _get_staged_changes() -> tuple[str, str]:
    """Get the staged changes as a diff and summary.

    Returns:
        A tuple of (diff, summary) strings
    """
    diff = git.get_staged_diff()
    if not diff.strip():
        return "", ""

    return diff, summarize_diff(diff)


@app.command()
def init():
    """Initialize bondocs in the current project."""
    # Check if we're in a git repository
    if not git.is_git_repo():
        exit_with_error("Not a git repository. Please run 'git init' first.")

    # Create necessary files
    _create_file(
        Path(".pre-commit-config.yaml"), PRE_COMMIT_CONFIG, ".pre-commit-config.yaml"
    )
    _create_file(Path(".bondocs.toml"), BONDOCS_CONFIG, ".bondocs.toml")
    _create_file(Path("README.md"), DEFAULT_README, "README.md")

    # Install pre-commit hooks
    @safe_execution("Failed to install pre-commit hooks", exit_on_error=False)
    def install_hooks() -> bool:
        subprocess.check_call(
            ["pre-commit", "install"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True

    if install_hooks():
        print("[green]Installed pre-commit hooks[/]")
    else:
        print("Run: pip install pre-commit")

    print("\n[bold]Bondocs has been initialized![/]")
    print("Next steps:")
    print("1. Review and customize .bondocs.toml if needed")
    print("2. Make sure pre-commit is installed: pip install pre-commit")
    print("3. Start making changes - Bondocs will keep your README in sync!")


@app.command()
def run():
    """Run bondocs on the current git diff."""
    diff, summary = _get_staged_changes()
    if not summary:
        display_warning("No changes detected.")
        return

    print(f"[cyan]Changes detected:\n{summary}[/]")

    # Generate and apply README patch
    patch = generate_readme_patch(summary)
    if not patch.strip():
        display_warning("No README changes needed.")
        return

    if apply_patch(patch):
        print("[green]README.md updated ✨[/]")
        git.stage_file("README.md")
    else:
        exit_with_error("Failed to update README.md.")


@app.command()
@handle_errors(GitError, severity=ErrorSeverity.ERROR, exit_on_error=True)
def changelog():
    """Update CHANGELOG.md based on staged diff."""
    # Get commit message from last commit
    commit_message = git.get_last_commit_message()

    if update_changelog(commit_message):
        print("[green]CHANGELOG.md updated ✨[/]")
        git.stage_file("CHANGELOG.md")
    else:
        display_warning("No CHANGELOG.md changes needed.")


@app.command()
def runbook():
    """Update runbooks based on staged diff."""

    @safe_execution("Failed to stage runbooks", exit_on_error=False)
    def stage_runbooks() -> bool:
        subprocess.check_call(["git", "add", "docs/runbook/*.md"])
        return True

    if update_runbooks():
        print("[green]Runbooks updated ✨[/]")
        if stage_runbooks():
            print("[green]Runbooks re-staged.[/]")
    else:
        display_warning("No runbook changes needed.")


@app.command()
def diff():
    """Show proposed README patch without applying it."""
    diff, summary = _get_staged_changes()
    if not summary:
        display_warning("No changes detected.")
        return

    print(f"[cyan]Changes detected:\n{summary}[/]")

    # Generate patch
    patch = generate_readme_patch(summary)
    if not patch.strip():
        display_warning("No README changes needed.")
        return

    print("\n[green]Proposed README patch:[/]\n")
    print(patch)


@app.command()
def show_config():
    """Show current configuration."""
    cfg = config.get_config()
    print("[green]Current configuration:[/]")
    for key, value in cfg.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    app()
