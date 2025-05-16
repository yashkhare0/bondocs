"""Document management for Bondocs.

Handles reading, writing, and patching documentation files.
"""

import subprocess
import tempfile
from pathlib import Path

from .interfaces import DocumentManager, PatchError


class DocManager(DocumentManager):
    """Document manager implementation."""

    def get_document_content(self, path: Path) -> str:
        """Get the content of a document.

        Args:
            path: Path to the document

        Returns:
            The content of the document

        Raises:
            FileNotFoundError: If the document doesn't exist
        """
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Document not found: {path}") from None
        except Exception as e:
            raise PatchError(f"Error reading document {path}: {str(e)}") from e

    def update_document(self, path: Path, content: str) -> bool:
        """Update a document with new content.

        Args:
            path: Path to the document
            content: New content for the document

        Returns:
            True if the document was updated successfully, False otherwise
        """
        try:
            path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def apply_patch(self, patch: str) -> bool:
        """Apply a patch to a document.

        Args:
            patch: Unified diff patch to apply

        Returns:
            True if the patch was applied successfully, False otherwise
        """
        if not patch.strip():
            return False

        # Check if the patch targets a documentation file
        valid_targets = ["+++ b/README.md", "+++ b/CHANGELOG.md", "+++ b/docs/runbook"]
        if not any(target in patch for target in valid_targets):
            return False

        try:
            with tempfile.NamedTemporaryFile(
                "w+", suffix=".patch", encoding="utf-8"
            ) as f:
                f.write(patch)
                f.flush()
                proc = subprocess.run(
                    ["patch", "-p0", "-i", f.name], capture_output=True, text=True
                )
                if proc.returncode != 0:
                    # Log error for debugging but don't raise an exception
                    print(f"[red]Patch failed: {proc.stderr}[/]")
                    return False
                return True
        except Exception as e:
            # Log error for debugging but don't raise an exception
            print(f"[red]Error applying patch: {str(e)}[/]")
            return False

    def exists(self, path: Path) -> bool:
        """Check if a document exists.

        Args:
            path: Path to the document

        Returns:
            True if the document exists, False otherwise
        """
        return path.exists()


# Global singleton instance for convenience
doc_manager = DocManager()
