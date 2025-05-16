"""Interface definitions for Bondocs.

This module contains abstract interfaces for the major components of Bondocs,
promoting loose coupling and better testability.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Protocol, Union


class ConfigProvider(Protocol):
    """Interface for configuration providers."""

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get the complete configuration."""
        pass

    @abstractmethod
    def get_value(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a specific configuration value."""
        pass

    @abstractmethod
    def get_env(self, key: str) -> Optional[str]:
        """Get an environment variable value."""
        pass


class DocumentManager(Protocol):
    """Interface for document management."""

    @abstractmethod
    def get_document_content(self, path: Path) -> str:
        """Get the content of a document.

        Args:
            path: Path to the document

        Returns:
            The content of the document

        Raises:
            FileNotFoundError: If the document doesn't exist
        """
        pass

    @abstractmethod
    def update_document(self, path: Path, content: str) -> bool:
        """Update a document with new content.

        Args:
            path: Path to the document
            content: New content for the document

        Returns:
            True if the document was updated successfully, False otherwise
        """
        pass

    @abstractmethod
    def apply_patch(self, patch: str) -> bool:
        """Apply a patch to a document.

        Args:
            patch: Unified diff patch to apply

        Returns:
            True if the patch was applied successfully, False otherwise
        """
        pass


class LLMInterface(Protocol):
    """Interface for LLM providers."""

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response to a prompt.

        Args:
            prompt: The prompt to generate a response for

        Returns:
            The generated response

        Raises:
            LLMError: If there was an error generating a response
        """
        pass


class GitInterface(Protocol):
    """Interface for Git operations."""

    @abstractmethod
    def get_staged_diff(self) -> str:
        """Get the staged diff.

        Returns:
            The staged diff as a string
        """
        pass

    @abstractmethod
    def stage_file(self, path: Union[str, Path]) -> bool:
        """Stage a file with git add.

        Args:
            path: Path to the file to stage

        Returns:
            True if the file was staged successfully, False otherwise
        """
        pass

    @abstractmethod
    def is_git_repo(self) -> bool:
        """Check if the current directory is a git repository.

        Returns:
            True if the current directory is a git repository, False otherwise
        """
        pass

    @abstractmethod
    def get_last_commit_message(self) -> str:
        """Get the message of the last commit.

        Returns:
            The message of the last commit

        Raises:
            GitError: If there was an error getting the commit message
        """
        pass


# Custom exception classes for standardized error handling
class BondocsError(Exception):
    """Base exception class for Bondocs errors."""

    pass


class ConfigError(BondocsError):
    """Exception raised for configuration errors."""

    pass


class LLMError(BondocsError):
    """Exception raised for LLM-related errors."""

    pass


class GitError(BondocsError):
    """Exception raised for Git-related errors."""

    pass


class PatchError(BondocsError):
    """Exception raised for patch-related errors."""

    pass
