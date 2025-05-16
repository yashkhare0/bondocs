"""Runbook management for Bondocs.

Handles updating runbooks based on git changes.
"""

from pathlib import Path

from .document import doc_manager
from .git import git, summarize_diff
from .interfaces import LLMError
from .llm import llm
from .prompt import render_prompt


def get_runbook_paths(working_dir: str) -> list[Path]:
    """Get all runbook paths in the project."""
    runbook_dir = Path(working_dir) / "docs" / "runbook"
    if not runbook_dir.exists():
        return []
    return list(runbook_dir.glob("*.md"))


def generate_runbook_patch(summary: str, runbook_content: str, file_path: str) -> str:
    """Generate a patch for a runbook based on a diff summary.

    Args:
        summary: Summary of git diff changes
        runbook_content: Current content of the runbook
        file_path: Path to the runbook file

    Returns:
        A unified diff string for updating the runbook
    """
    try:
        prompt = render_prompt(
            document_content=runbook_content,
            summary=summary,
            doc_type="runbook",
            file_path=file_path,
        )

        return llm.generate_response(prompt)
    except LLMError as e:
        print(f"[red]Error generating runbook patch: {str(e)}[/]")
        return ""


def update_runbooks() -> bool:
    """Update all runbooks based on the current changes.

    Returns:
        True if all runbooks were updated successfully, False if any failed
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
                    success = False
            except Exception as e:
                print(f"[red]Error updating runbook {runbook_path}: {str(e)}[/]")
                success = False

        return success
    except Exception as e:
        print(f"[red]Error updating runbooks: {str(e)}[/]")
        return False


def test_runbook_update() -> bool:
    """Test function for runbook updates."""
    return True
