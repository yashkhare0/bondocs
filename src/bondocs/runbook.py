"""Runbook management for Bondocs.

Handles updating runbooks based on git changes.
"""

from pathlib import Path

from .diff import staged_diff, summarize
from .llm import LLMBackend
from .patcher import apply_patch
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
    prompt = render_prompt(
        document_content=runbook_content,
        summary=summary,
        doc_type="runbook",
        file_path=file_path,
    )

    llm = LLMBackend()
    return llm.chat(prompt)


def update_runbooks() -> bool:
    """Update all runbooks based on the current changes.

    Returns:
        True if all runbooks were updated successfully, False if any failed
    """
    # Get the diff summary
    diff = staged_diff()
    if not diff.strip():
        return False

    summary = summarize(diff)
    success = True

    # Update each runbook
    for runbook_path in get_runbook_paths("."):
        runbook_content = runbook_path.read_text()

        # Generate and apply the patch
        patch = generate_runbook_patch(
            summary=summary,
            runbook_content=runbook_content,
            file_path=str(runbook_path),
        )

        if not patch.strip():
            continue

        if not apply_patch(patch):
            success = False

    return success


def test_runbook_update() -> bool:
    """Test function for runbook updates."""
    return True
