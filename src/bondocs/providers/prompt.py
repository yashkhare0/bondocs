"""Prompt management for Bondocs LLM interactions.

Handles loading, formatting, and rendering of prompts for LLM interactions.
"""

import os
import re
from functools import lru_cache
from typing import Any, Literal, Optional

import jinja2

# Directory where the prompt templates are stored
_PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))


# Cache the system prompt to avoid re-parsing it for each request
@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Load the system prompt from the prompt.md file.

    Extracts the system prompt section from between the '---system---'
    delimiter and the first blank line that follows. Provides robust
    error handling for various edge cases.

    Returns:
        The extracted system prompt or an empty string if not found
    """
    prompt_path = os.path.join(_PROMPT_DIR, "prompt.md")

    try:
        with open(prompt_path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        # Fallback to default prompt
        return """You are a documentation assistant. Your task is to update the documentation based on changes to the codebase.
Please generate a unified diff to update the documentation."""  # noqa: E501

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

    return text.strip()  # Return the whole file as a fallback


# Cache the template loading to avoid repeated file system access
@lru_cache(maxsize=1)
def _load_template() -> jinja2.Template:
    """Load the Jinja2 template from the prompt.md file.

    Returns:
        A compiled Jinja2 template

    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    prompt_path = os.path.join(_PROMPT_DIR, "prompt.md")

    try:
        with open(prompt_path, encoding="utf-8") as f:
            template_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found at {prompt_path}") from None

    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env.from_string(template_text)


def render_template(
    context: dict[str, Any],
    doc_type: Literal["readme", "runbook", "changelog"] = "readme",
) -> str:
    """Render the prompt template with the given context.

    Args:
        context: The context dictionary with values for template variables
        doc_type: The type of document to update

    Returns:
        The rendered template as a string
    """
    # Set the document type in the context
    context["doc_type"] = doc_type

    # Load and render the template
    template = _load_template()
    return template.render(**context)


def render_prompt(
    document_content: str,
    summary: str,
    doc_type: Optional[Literal["readme", "runbook", "changelog"]] = "readme",
    **kwargs: Any,
) -> str:
    """Render the prompt template for document updates.

    Args:
        document_content: The content of the document to update
        summary: Summary of the changes
        doc_type: Type of document being updated
        **kwargs: Additional context variables to pass to the template
            - file_path: Path to the file being updated (required for runbooks)
            - commit_message: Commit message (used primarily for changelog updates)

    Returns:
        Rendered prompt template with all context variables

    Raises:
        ValueError: If required parameters are missing for a specific document type
    """
    # Parameter validation
    if doc_type == "runbook" and "file_path" not in kwargs:
        raise ValueError("file_path is required for runbook updates")

    # Create the template context
    context = {
        "readme": document_content,  # Keep for backward compatibility
        "document": document_content,
        "summary": summary,
        "doc_type": doc_type,
        **kwargs,
    }

    template = _load_template()
    return template.render(**context)


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


def reset_cache() -> None:
    """Reset the cached templates and system prompts.

    This is useful for testing or when templates have been modified.
    """
    _load_template.cache_clear()
    load_system_prompt.cache_clear()
