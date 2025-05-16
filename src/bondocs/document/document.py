"""Document management for Bondocs.

Handles reading, updating, and patching documentation files.
"""

from pathlib import Path

from bondocs.core.errors import (
    BondocsError,
    ErrorSeverity,
    handle_errors,
    log_error,
    safe_execution,
)
from bondocs.core.interfaces import DocumentManager


class DocumentError(BondocsError):
    """Error raised during document operations."""

    pass


class FileSystemDocument(DocumentManager):
    """File system implementation of DocumentManager."""

    @handle_errors(FileNotFoundError, severity=ErrorSeverity.ERROR)
    def get_document_content(self, path: Path) -> str:
        """Get the content of a document.

        Args:
            path: Path to the document

        Returns:
            The content of the document

        Raises:
            FileNotFoundError: If the document doesn't exist
            DocumentError: If reading the document fails
        """
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise DocumentError(f"Failed to read document {path}: {str(e)}") from e

    @safe_execution("Failed to update document")
    def update_document(self, path: Path, content: str) -> bool:
        """Update a document with new content.

        Args:
            path: Path to the document
            content: New content for the document

        Returns:
            True if the document was updated successfully, False otherwise
        """
        try:
            # Ensure the directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            log_error(
                DocumentError(f"Failed to update document {path}: {str(e)}"),
                severity=ErrorSeverity.ERROR,
            )
            return False

    def apply_patch(self, patch: str) -> bool:
        """Apply a patch to a document.

        Args:
            patch: Unified diff patch to apply

        Returns:
            True if the patch was applied successfully, False otherwise
        """
        # We delegate to the patch utility for this
        # (implemented in patcher.py)
        return False


# Global singleton instance for convenience
doc_manager = FileSystemDocument()
