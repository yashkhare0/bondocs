"""Changelog management for Bondocs.

Handles updating CHANGELOG.md based on git changes.
"""

from pathlib import Path

from bondocs.core.errors import (
    BondocsError,
    ErrorSeverity,
    handle_errors,
    log_error,
    safe_execution,
)
from bondocs.document.document import doc_manager
from bondocs.git import git, summarize_diff
from bondocs.providers import llm
from bondocs.providers.prompt import render_prompt


class ChangelogError(BondocsError):
    """Error raised during changelog operations."""

    pass


@handle_errors(ChangelogError, severity=ErrorSeverity.WARNING)
def get_changelog_path(working_dir: str) -> Path:
    """Get the path to the CHANGELOG.md file."""
    try:
        return Path(working_dir) / "CHANGELOG.md"
    except Exception as e:
        raise ChangelogError(f"Failed to get changelog path: {str(e)}") from e


@handle_errors(ChangelogError, severity=ErrorSeverity.ERROR)
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

    Raises:
        ChangelogError: If generating the changelog patch fails
    """
    try:
        prompt = render_prompt(
            document_content=changelog_content,
            summary=summary,
            doc_type="changelog",
            commit_message=commit_message,
        )

        return llm.generate_response(prompt)
    except Exception as e:
        raise ChangelogError(f"Error generating changelog patch: {str(e)}") from e


@safe_execution("Failed to update changelog", error_type=ChangelogError)
def update_changelog(commit_message: str) -> bool:
    """Update the CHANGELOG.md file based on the current changes.

    Args:
        commit_message: The commit message to use for the changelog entry

    Returns:
        True if the changelog was updated successfully, False otherwise
    """
    # Get the current changelog content
    changelog_path = get_changelog_path(".")
    try:
        changelog_content = doc_manager.get_document_content(changelog_path)
    except FileNotFoundError:
        changelog_content = ""
        log_error(
            ChangelogError("CHANGELOG.md not found, a new one will be created."),
            severity=ErrorSeverity.INFO,
        )

    # Get the diff summary
    try:
        diff = git.get_staged_diff()
        if not diff.strip():
            log_error(
                ChangelogError("No staged changes found."), severity=ErrorSeverity.INFO
            )
            return False

        summary = summarize_diff(diff)

        # Generate and apply the patch
        patch = generate_changelog_patch(summary, commit_message, changelog_content)
        if not patch.strip():
            log_error(
                ChangelogError("Generated patch is empty."),
                severity=ErrorSeverity.WARNING,
            )
            return False

        result = doc_manager.apply_patch(patch)
        if not result:
            log_error(
                ChangelogError("Failed to apply changelog patch."),
                severity=ErrorSeverity.ERROR,
            )

        return result
    except Exception as e:
        raise ChangelogError(f"Error updating changelog: {str(e)}") from e
