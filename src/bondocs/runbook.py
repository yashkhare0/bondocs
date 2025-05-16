"""Runbook management for Bondocs.

Handles updating runbooks based on git changes.
"""

from pathlib import Path

from .diff import staged_diff, summarize
from .patcher import apply_patch, generate_patch
from .prompt import render_runbook_prompt


def get_runbook_paths(working_dir: str) -> list[Path]:
    """Get all runbook paths in the project."""
    runbook_dir = Path(working_dir) / "docs" / "runbook"
    if not runbook_dir.exists():
        return []
    return list(runbook_dir.glob("*.md"))


def update_runbooks() -> bool:
    """Update all runbooks based on the current changes."""
    # Get the diff summary
    diff = staged_diff()
    if not diff.strip():
        return False

    summary = summarize(diff)
    success = True

    # Update each runbook
    for runbook_path in get_runbook_paths("."):
        runbook_content = runbook_path.read_text()

        # Generate the prompt
        prompt = render_runbook_prompt(
            readme=runbook_content,
            summary=summary,
            file_path=str(runbook_path),
        )

        # Generate and apply the patch
        patch = generate_patch(prompt)
        if not patch.strip():
            continue

        if not apply_patch(patch):
            success = False

    return success


def test_runbook_update() -> bool:
    """Test function for runbook updates."""
    return True
