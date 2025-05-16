"""Patch generation and application utilities for Bondocs.

Handles creating and applying documentation patches using LLMs.
"""

from pathlib import Path

from .document import doc_manager
from .interfaces import LLMError
from .llm import llm
from .prompt import render_prompt


def generate_readme_patch(summary: str) -> str:
    """Generate a patch for README.md based on a diff summary.

    Args:
        summary: Summary of git diff changes.

    Returns:
        A unified diff string for updating the README.
    """
    try:
        # Get the README content, defaulting to empty string if not found
        readme_path = Path("README.md")
        try:
            readme = doc_manager.get_document_content(readme_path)
        except FileNotFoundError:
            readme = ""

        # Generate the prompt
        prompt = render_prompt(
            document_content=readme, summary=summary, doc_type="readme"
        )

        # Generate the patch
        return llm.generate_response(prompt)
    except LLMError as e:
        print(f"[red]Error generating README patch: {str(e)}[/]")
        return ""


def apply_patch(patch: str) -> bool:
    """Apply a patch to a documentation file.

    Args:
        patch: Unified diff string to apply.

    Returns:
        True if patch was applied successfully, False otherwise.
    """
    try:
        return doc_manager.apply_patch(patch)
    except Exception as e:
        print(f"[red]Error applying patch: {str(e)}[/]")
        return False


# For backward compatibility
generate_patch = generate_readme_patch
