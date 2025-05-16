"""Git operations for Bondocs.

Handles Git-related operations like getting diffs and staging files.
"""

import subprocess
from pathlib import Path
from typing import Union

from bondocs.core.errors import GitError, handle_errors
from bondocs.core.interfaces import GitInterface


class Git(GitInterface):
    """Git interface implementation."""

    @handle_errors(GitError)
    def get_staged_diff(self) -> str:
        """Get the staged diff.

        Returns:
            The staged diff as a string

        Raises:
            GitError: If there was an error getting the diff
        """
        try:
            return subprocess.check_output(
                ["git", "diff", "--cached", "-U0"],
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get staged diff: {str(e)}") from e
        except Exception as e:
            raise GitError(f"Unexpected error getting staged diff: {str(e)}") from e

    @handle_errors(Exception, default_return=False)
    def stage_file(self, path: Union[str, Path]) -> bool:
        """Stage a file with git add.

        Args:
            path: Path to the file to stage

        Returns:
            True if the file was staged successfully, False otherwise
        """
        subprocess.check_call(["git", "add", str(path)])
        return True

    @handle_errors(Exception, default_return=False)
    def is_git_repo(self) -> bool:
        """Check if the current directory is a git repository.

        Returns:
            True if the current directory is a git repository, False otherwise
        """
        subprocess.check_call(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True

    @handle_errors(GitError)
    def get_last_commit_message(self) -> str:
        """Get the message of the last commit.

        Returns:
            The message of the last commit

        Raises:
            GitError: If there was an error getting the commit message
        """
        try:
            return subprocess.check_output(
                ["git", "log", "-1", "--pretty=%B"],
                text=True,
            ).strip()
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to get last commit message: {str(e)}") from e
        except Exception as e:
            raise GitError(
                f"Unexpected error getting last commit message: {str(e)}"
            ) from e


# Global singleton instance for convenience
git = Git()


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
