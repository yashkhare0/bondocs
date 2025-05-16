"""Changelog management for Bondocs.

Handles updating CHANGELOG.md based on git changes.
"""

from pathlib import Path

from .diff import staged_diff, summarize
from .patcher import apply_patch, generate_patch
from .prompt import render_changelog_prompt


def get_changelog_path(working_dir: str) -> Path:
    """Get the path to the CHANGELOG.md file."""
    return Path(working_dir) / "CHANGELOG.md"


def update_changelog(commit_message: str) -> bool:
    """Update the CHANGELOG.md file based on the current changes."""
    # Get the current changelog content
    changelog_path = get_changelog_path(".")
    changelog_content = changelog_path.read_text() if changelog_path.exists() else ""

    # Get the diff summary
    diff = staged_diff()
    if not diff.strip():
        return False

    summary = summarize(diff)

    # Generate the prompt
    prompt = render_changelog_prompt(
        readme=changelog_content,
        summary=summary,
        commit_message=commit_message,
    )

    # Generate and apply the patch
    patch = generate_patch(prompt)
    if not patch.strip():
        return False

    return apply_patch(patch)
