"""Diff operations for Bondocs.

Provides functions for summarizing Git diffs.
"""


def summarize_diff(diff: str) -> str:
    """Summarize the diff in a human-readable format.

    Args:
        diff: The diff to summarize

    Returns:
        A human-readable summary of the diff
    """
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
