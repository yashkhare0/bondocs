"""Command-line interface for Bondocs.

Provides commands for initializing and running Bondocs.
"""

import sys
from pathlib import Path

import click
from rich import print  # type: ignore

from .changelog import update_changelog
from .config import config
from .document import doc_manager
from .git import git, summarize_diff
from .interfaces import GitError
from .patcher import apply_patch, generate_readme_patch
from .runbook import update_runbooks
from .templates import BONDOCS_CONFIG, DEFAULT_README, PRE_COMMIT_CONFIG


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
        print(f"[yellow]Warning: {file_type} already exists[/]")


def _get_staged_changes() -> tuple[str, str]:
    """Get the staged changes as a diff and summary.

    Returns:
        A tuple of (diff, summary) strings
    """
    try:
        diff = git.get_staged_diff()
        if not diff.strip():
            return "", ""

        return diff, summarize_diff(diff)
    except GitError as e:
        print(f"[red]Error getting git changes: {str(e)}[/]")
        return "", ""


@app.command()
def init():
    """Initialize bondocs in the current project."""
    # Check if we're in a git repository
    if not git.is_git_repo():
        print("[red]Error: Not a git repository. Please run 'git init' first.[/]")
        sys.exit(1)

    # Create necessary files
    _create_file(
        Path(".pre-commit-config.yaml"), PRE_COMMIT_CONFIG, ".pre-commit-config.yaml"
    )
    _create_file(Path(".bondocs.toml"), BONDOCS_CONFIG, ".bondocs.toml")
    _create_file(Path("README.md"), DEFAULT_README, "README.md")

    # Install pre-commit hooks
    try:
        import subprocess

        subprocess.check_call(
            ["pre-commit", "install"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[green]Installed pre-commit hooks[/]")
    except Exception:
        print(
            "[yellow]Warning: Failed to install pre-commit hooks. "
            "Please install pre-commit first.[/]"
        )
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
        print("[yellow]No changes detected.[/]")
        return

    print(f"[cyan]Changes detected:\n{summary}[/]")

    # Generate and apply README patch
    patch = generate_readme_patch(summary)
    if not patch.strip():
        print("[yellow]No README changes needed.[/]")
        return

    if apply_patch(patch):
        print("[green]README.md updated ✨[/]")
        git.stage_file("README.md")
    else:
        print("[red]Failed to update README.md.[/]")


@app.command()
def changelog():
    """Update CHANGELOG.md based on staged diff."""
    # Get commit message from last commit
    try:
        commit_message = git.get_last_commit_message()
    except GitError as e:
        print(f"[red]Error: {str(e)}[/]")
        sys.exit(1)

    if update_changelog(commit_message):
        print("[green]CHANGELOG.md updated ✨[/]")
        git.stage_file("CHANGELOG.md")
    else:
        print("[yellow]No CHANGELOG.md changes needed.[/]")


@app.command()
def runbook():
    """Update runbooks based on staged diff."""
    if update_runbooks():
        print("[green]Runbooks updated ✨[/]")
        try:
            import subprocess

            subprocess.check_call(["git", "add", "docs/runbook/*.md"])
            print("[green]Runbooks re-staged.[/]")
        except Exception:
            print("[yellow]Warning: Failed to re-stage runbooks[/]")
    else:
        print("[yellow]No runbook changes needed.[/]")


@app.command()
def diff():
    """Show proposed README patch without applying it."""
    diff, summary = _get_staged_changes()
    if not summary:
        print("[yellow]No changes detected.[/]")
        return

    print(f"[cyan]Changes detected:\n{summary}[/]")

    # Generate patch
    patch = generate_readme_patch(summary)
    if not patch.strip():
        print("[yellow]No README changes needed.[/]")
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
