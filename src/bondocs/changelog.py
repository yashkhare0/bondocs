"""Changelog management for Bondocs.

Handles updating CHANGELOG.md based on git changes.
"""

from pathlib import Path

from .diff import staged_diff, summarize
from .llm import LLMBackend
from .patcher import apply_patch
from .prompt import render_prompt


def get_changelog_path(working_dir: str) -> Path:
    """Get the path to the CHANGELOG.md file."""
    return Path(working_dir) / "CHANGELOG.md"


def generate_changelog_patch(
    summary: str, commit_message: str, changelog_content: str
) -> str:
    """Generate a patch for CHANGELOG.md based on a diff summary.

    Args:
        summary: Summary of git diff changes
        commit_message: The commit message
        changelog_content: Current content of the changelog

    Returns:
        A unified diff string for updating the changelog
    """
    prompt = render_prompt(
        document_content=changelog_content,
        summary=summary,
        doc_type="changelog",
        commit_message=commit_message,
    )

    llm = LLMBackend()
    return llm.chat(prompt)


def update_changelog(commit_message: str) -> bool:
    """Update the CHANGELOG.md file based on the current changes.

    Args:
        commit_message: The commit message to use for the changelog entry

    Returns:
        True if the changelog was updated successfully, False otherwise
    """
    # Get the current changelog content
    changelog_path = get_changelog_path(".")
    changelog_content = changelog_path.read_text() if changelog_path.exists() else ""

    # Get the diff summary
    diff = staged_diff()
    if not diff.strip():
        return False

    summary = summarize(diff)

    # Generate and apply the patch
    patch = generate_changelog_patch(summary, commit_message, changelog_content)
    if not patch.strip():
        return False

    return apply_patch(patch)
