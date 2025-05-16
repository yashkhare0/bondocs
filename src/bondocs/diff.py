"""Git diff utilities for Bondocs.

Provides functions for extracting and summarizing git diffs.
"""

import subprocess


def staged_diff() -> str:
    """Get the staged diff from git."""
    try:
        return subprocess.check_output(
            ["git", "diff", "--cached", "-U0"],
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError:
        return ""


def summarize(diff: str) -> str:
    """Summarize the diff in a human-readable format."""
    if not diff:
        return "No changes"

    # Split into files
    files = diff.split("diff --git")
    if len(files) <= 1:
        return "No changes"

    summary = []
    for file in files[1:]:  # Skip the first empty split
        # Get the file name
        try:
            file_name = file.split("+++ b/")[1].split("\n")[0]
        except IndexError:
            continue

        # Count additions and deletions
        additions = file.count("\n+") - file.count("\n+++")
        deletions = file.count("\n-") - file.count("\n---")

        if additions or deletions:
            summary.append(f"{file_name}: +{additions} -{deletions}")

    return "\n".join(summary) if summary else "No changes"
