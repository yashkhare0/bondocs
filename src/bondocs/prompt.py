"""Prompt template handling for Bondocs.

Manages the loading and rendering of prompts for LLM interactions.
"""

from pathlib import Path
from typing import Literal

from jinja2 import Template


def _load_template() -> Template:
    template_path = Path(__file__).parent / "prompt.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {template_path}")
    return Template(template_path.read_text())


def load_system_prompt() -> str:
    """Load the system prompt from the top of prompt.md (after ---system---)."""
    template_path = Path(__file__).parent / "prompt.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {template_path}")
    text = template_path.read_text()
    if text.startswith("---system---"):
        # Get everything after ---system--- up to the first blank line
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
        return "\n".join(system_lines).strip()
    return ""


def render_runbook_prompt(
    readme: str,
    summary: str,
    file_path: str,
) -> str:
    """Render the prompt template for runbook updates.

    Args:
        readme: The content of the runbook to update
        summary: Summary of the changes
        file_path: Path to the runbook file being updated
    """
    template = _load_template()
    return template.render(
        readme=readme,
        summary=summary,
        doc_type="runbook",
        file_path=file_path,
        commit_message=None,
    )


def render_changelog_prompt(
    readme: str,
    summary: str,
    commit_message: str,
) -> str:
    """Render the prompt template for changelog updates.

    Args:
        readme: The content of the changelog to update
        summary: Summary of the changes
        commit_message: Commit message for the changelog update
    """
    template = _load_template()
    return template.render(
        readme=readme,
        summary=summary,
        doc_type="changelog",
        file_path=None,
        commit_message=commit_message,
    )


# Keep the generic function for backward compatibility
def render_prompt(
    readme: str,
    summary: str,
    doc_type: Literal["runbook", "changelog"] | None = None,
    file_path: str | None = None,
    commit_message: str | None = None,
) -> str:
    """Render the prompt template with the given README and summary.

    Args:
        readme: The content of the document to update
        summary: Summary of the changes
        doc_type: Type of document being updated (e.g. "runbook", "changelog")
        file_path: Path to the file being updated
        commit_message: Commit message (for changelog updates)
    """
    template = _load_template()
    return template.render(
        readme=readme,
        summary=summary,
        doc_type=doc_type,
        file_path=file_path,
        commit_message=commit_message,
    )
