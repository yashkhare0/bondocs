"""Patch generation and application utilities for Bondocs.

Handles creating and applying documentation patches using LLMs.
"""

import subprocess
import tempfile
from pathlib import Path

from bondocs.llm import LLMBackend

from .prompt import render_prompt  # jinja2 template render


def generate_patch(summary: str) -> str:
    """Generate a patch for README.md based on a diff summary.

    Args:
        summary: Summary of git diff changes.

    Returns:
        A unified diff string for updating the README.
    """
    readme = (
        Path("README.md").read_text(encoding="utf-8")
        if Path("README.md").exists()
        else ""
    )
    prompt = render_prompt(readme=readme, summary=summary)
    llm = LLMBackend()
    return llm.chat(prompt)


def apply_patch(patch: str) -> bool:
    """Apply a patch to the README.md file.

    Args:
        patch: Unified diff string to apply.

    Returns:
        True if patch was applied successfully, False otherwise.
    """
    if not patch.strip():
        return False
    if "+++ b/README.md" not in patch:
        return False
    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".patch", encoding="utf-8") as f:
            f.write(patch)
            f.flush()
            proc = subprocess.run(
                ["patch", "-p0", "-i", f.name], capture_output=True, text=True
            )
            if proc.returncode != 0:
                print(f"[red]Patch failed: {proc.stderr}[/]")
                return False
            return True
    except Exception as e:
        print(f"[red]Error applying patch: {str(e)}[/]")
        return False
