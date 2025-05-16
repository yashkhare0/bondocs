"""Git diff utilities for Bondocs (legacy module).

Provides functions for extracting and summarizing git diffs.
This module is kept for backward compatibility.
"""

from .git import git, summarize_diff


# Legacy functions for backward compatibility
def staged_diff() -> str:
    """Get the staged diff from git."""
    return git.get_staged_diff()


def summarize(diff: str) -> str:
    """Summarize the diff in a human-readable format."""
    return summarize_diff(diff)
