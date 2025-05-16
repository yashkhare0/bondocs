"""Prompt template handling for Bondocs.

Manages the loading and rendering of prompts for LLM interactions.
"""

import re
from pathlib import Path
from typing import Literal, Optional

from jinja2 import Template


def _load_template() -> Template:
    """Load the Jinja2 template from the prompt.md file."""
    template_path = Path(__file__).parent / "prompt.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {template_path}")
    return Template(template_path.read_text())


def load_system_prompt() -> str:
    """Load the system prompt from the prompt.md file.

    Extracts the system prompt section from between the '---system---'
    delimiter and the first blank line that follows. Provides robust
    error handling for various edge cases.

    Returns:
        The extracted system prompt or an empty string if not found

    Raises:
        FileNotFoundError: If the prompt template file doesn't exist
    """
    template_path = Path(__file__).parent / "prompt.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {template_path}")

    text = template_path.read_text()

    # Define the pattern to match system prompt section
    system_pattern = r"^---system---\s*\n(.*?)(?:\n\s*\n|\n*$)"
    match = re.search(system_pattern, text, re.DOTALL | re.MULTILINE)

    if match:
        return match.group(1).strip()

    # Fallback to the previous approach if regex doesn't match
    if text.startswith("---system---"):
        lines = text.splitlines()
        system_lines = []
        found = False

        for line in lines:
            if found:
                if line.strip() == "":
                    break
                system_lines.append(line)
            elif line.strip() == "---system---":
                found = True

        if system_lines:
            return "\n".join(system_lines).strip()

    return ""


def render_prompt(
    document_content: str,
    summary: str,
    doc_type: Optional[Literal["readme", "runbook", "changelog"]] = "readme",
    file_path: Optional[str] = None,
    commit_message: Optional[str] = None,
) -> str:
    """Render the prompt template for document updates.

    Args:
        document_content: The content of the document to update
        summary: Summary of the changes
        doc_type: Type of document being updated
        file_path: Path to the file being updated (required for runbooks)
        commit_message: Commit message (used primarily for changelog updates)

    Returns:
        Rendered prompt template with all context variables

    Raises:
        ValueError: If required parameters are missing for a specific document type
    """
    if doc_type == "runbook" and not file_path:
        raise ValueError("file_path is required for runbook updates")

    template = _load_template()
    return template.render(
        readme=document_content,  # Keep for backward compatibility
        document=document_content,
        summary=summary,
        doc_type=doc_type,
        file_path=file_path,
        commit_message=commit_message,
    )


# Legacy function aliases for backward compatibility
def render_runbook_prompt(
    readme: str,
    summary: str,
    file_path: str,
) -> str:
    """Render the prompt template for runbook updates (legacy function).

    Args:
        readme: The content of the runbook to update
        summary: Summary of the changes
        file_path: Path to the runbook file being updated
    """
    return render_prompt(
        document_content=readme,
        summary=summary,
        doc_type="runbook",
        file_path=file_path,
    )


def render_changelog_prompt(
    readme: str,
    summary: str,
    commit_message: str,
) -> str:
    """Render the prompt template for changelog updates (legacy function).

    Args:
        readme: The content of the changelog to update
        summary: Summary of the changes
        commit_message: Commit message for the changelog update
    """
    return render_prompt(
        document_content=readme,
        summary=summary,
        doc_type="changelog",
        commit_message=commit_message,
    )
