"""Patch management for Bondocs.

Handles generating and applying patches to documentation files.
"""

import subprocess
import tempfile
from pathlib import Path

from bondocs.core.errors import (
    ErrorSeverity,
    PatchError,
    handle_errors,
    log_error,
    safe_execution,
)
from bondocs.document.document import doc_manager
from bondocs.providers import llm


@handle_errors(PatchError, severity=ErrorSeverity.ERROR)
def generate_readme_patch(summary: str) -> str:
    """Generate a patch for README.md based on the given summary.

    Args:
        summary: A summary of the changes to document

    Returns:
        A unified diff patch to apply to README.md

    Raises:
        PatchError: If generating the patch fails
    """
    try:
        # Get current README content
        readme_path = Path("README.md")
        if not readme_path.exists():
            return ""

        readme_content = doc_manager.get_document_content(readme_path)

        # Generate a patch using the LLM
        return llm.generate_response(
            f"Here's the current README.md:\n\n```\n{readme_content}\n```\n\n"
            f"Here's a summary of the changes to document:\n\n{summary}\n\n"
            "Generate a unified diff patch to update the README.md with these changes."
        )
    except Exception as e:
        raise PatchError(f"Error generating README patch: {str(e)}") from e


@safe_execution("Failed to apply patch", error_type=PatchError)
def apply_patch(patch: str) -> bool:
    """Apply a patch to the documentation.

    Args:
        patch: A unified diff patch to apply

    Returns:
        True if the patch was applied successfully, False otherwise
    """
    if not patch.strip():
        return False

    # Check if the patch targets a documentation file
    valid_targets = ["+++ b/README.md", "+++ b/CHANGELOG.md", "+++ b/docs/runbook"]
    if not any(target in patch for target in valid_targets):
        log_error(
            PatchError("Invalid patch target. Only documentation files are supported."),
            severity=ErrorSeverity.WARNING,
        )
        return False

    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".patch", encoding="utf-8") as f:
            f.write(patch)
            f.flush()
            proc = subprocess.run(
                ["patch", "-p0", "-i", f.name], capture_output=True, text=True
            )
            if proc.returncode != 0:
                # Log error for debugging
                log_error(
                    PatchError(f"Patch failed: {proc.stderr}"),
                    severity=ErrorSeverity.ERROR,
                )
                return False
            return True
    except Exception as e:
        # Log error for debugging
        raise PatchError(f"Error applying patch: {str(e)}") from e
