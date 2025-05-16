"""Runbook management for Bondocs.

Handles updating runbooks based on git changes.
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


class RunbookError(BondocsError):
    """Error raised during runbook operations."""

    pass


@handle_errors(RunbookError, severity=ErrorSeverity.WARNING)
def get_runbook_paths(working_dir: str) -> list[Path]:
    """Get all runbook paths in the project."""
    try:
        runbook_dir = Path(working_dir) / "docs" / "runbook"
        if not runbook_dir.exists():
            return []
        return list(runbook_dir.glob("*.md"))
    except Exception as e:
        raise RunbookError(f"Failed to get runbook paths: {str(e)}") from e


@handle_errors(RunbookError, severity=ErrorSeverity.ERROR)
def generate_runbook_patch(summary: str, runbook_content: str, file_path: str) -> str:
    """Generate a patch for a runbook based on a diff summary.

    Args:
        summary: Summary of git diff changes
        runbook_content: Current content of the runbook
        file_path: Path to the runbook file

    Returns:
        A unified diff string for updating the runbook

    Raises:
        RunbookError: If generating the runbook patch fails
    """
    try:
        prompt = render_prompt(
            document_content=runbook_content,
            summary=summary,
            doc_type="runbook",
            file_path=file_path,
        )

        return llm.generate_response(prompt)
    except Exception as e:
        raise RunbookError(f"Error generating runbook patch: {str(e)}") from e


@safe_execution("Failed to update runbooks", error_type=RunbookError)
def update_runbooks() -> bool:
    """Update all runbooks based on the current changes.

    Returns:
        True if all runbooks were updated successfully, False otherwise
    """
    try:
        # Get the diff summary
        diff = git.get_staged_diff()
        if not diff.strip():
            return False

        summary = summarize_diff(diff)
        success = True

        # Update each runbook
        for runbook_path in get_runbook_paths("."):
            try:
                runbook_content = doc_manager.get_document_content(runbook_path)

                # Generate and apply the patch
                patch = generate_runbook_patch(
                    summary=summary,
                    runbook_content=runbook_content,
                    file_path=str(runbook_path),
                )

                if not patch.strip():
                    continue

                if not doc_manager.apply_patch(patch):
                    log_error(
                        RunbookError(f"Failed to apply patch to {runbook_path}"),
                        severity=ErrorSeverity.WARNING,
                    )
                    success = False
            except Exception as e:
                log_error(
                    RunbookError(f"Error updating runbook {runbook_path}: {str(e)}"),
                    severity=ErrorSeverity.ERROR,
                )
                success = False

        return success
    except Exception as e:
        raise RunbookError(f"Error updating runbooks: {str(e)}") from e


@handle_errors(RunbookError, severity=ErrorSeverity.INFO)
def test_runbook_update() -> bool:
    """Test function for runbook updates."""
    return True
