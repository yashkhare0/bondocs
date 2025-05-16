"""Centralized error handling for Bondocs.

This module provides standardized error handling functions and patterns
for use throughout the Bondocs codebase.
"""

import logging
import sys
import traceback
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from rich import print
from rich.console import Console
from rich.panel import Panel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bondocs.log"), logging.StreamHandler()],
)

# Create a logger
logger = logging.getLogger("bondocs")

# Console for rich output
console = Console()

# Type variable for function return values
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


# Base exception class for Bondocs errors
class BondocsError(Exception):
    """Base exception class for Bondocs errors."""

    pass


# Specific error types
class ConfigError(BondocsError):
    """Exception raised for configuration errors."""

    pass


class GitError(BondocsError):
    """Exception raised for Git-related errors."""

    pass


class LLMError(BondocsError):
    """Exception raised for LLM-related errors."""

    pass


class PatchError(BondocsError):
    """Exception raised for patch-related errors."""

    pass


class DocumentError(BondocsError):
    """Error raised during document operations."""

    pass


class RunbookError(BondocsError):
    """Error raised during runbook operations."""

    pass


class ChangelogError(BondocsError):
    """Error raised during changelog operations."""

    pass


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def log_error(
    exception: Exception,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    exit_code: Optional[int] = None,
) -> None:
    """Log an error with consistent formatting.

    Args:
        exception: The exception to log
        severity: The severity level of the error
        exit_code: If provided, exit the program with this code after logging
    """
    error_type = type(exception).__name__
    error_message = str(exception)

    # Log to file
    if severity == ErrorSeverity.INFO:
        logger.info(f"{error_type}: {error_message}")
    elif severity == ErrorSeverity.WARNING:
        logger.warning(f"{error_type}: {error_message}")
    elif severity == ErrorSeverity.ERROR:
        logger.error(f"{error_type}: {error_message}")
    elif severity == ErrorSeverity.CRITICAL:
        logger.critical(f"{error_type}: {error_message}")

    # Pretty print to console
    color_map = {
        ErrorSeverity.INFO: "blue",
        ErrorSeverity.WARNING: "yellow",
        ErrorSeverity.ERROR: "red",
        ErrorSeverity.CRITICAL: "red",
    }
    color = color_map[severity]

    # Print to the console using rich
    print(f"[{color}]{error_type}[/]: {error_message}")

    # Exit if requested
    if exit_code is not None:
        sys.exit(exit_code)


def handle_errors(
    error_type: type[Exception] = Exception,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    exit_on_error: bool = False,
    default_return: Any = None,
    log_traceback: bool = False,
) -> Callable[[F], F]:
    """Decorator for standardized error handling.

    Args:
        error_type: The type of exception to catch
        severity: The severity level to log
        exit_on_error: Whether to exit the program on error
        default_return: The value to return on error (if not exiting)
        log_traceback: Whether to log the full traceback

    Returns:
        A decorated function with standardized error handling
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log_traceback:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                    )

                log_error(
                    e,
                    severity=severity,
                    exit_code=1 if exit_on_error else None,
                )
                return default_return

        return cast(F, wrapper)

    return decorator


def safe_execution(
    message: str = "Operation failed",
    exit_on_error: bool = False,
    error_type: type[Exception] = Exception,
) -> Callable[[F], F]:
    """Decorator for safely executing functions with user feedback.

    Args:
        message: The message to show on error
        exit_on_error: Whether to exit the program on error
        error_type: The type of exception to catch

    Returns:
        A decorated function with user-friendly error handling
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except error_type as e:
                logger.error(f"{message}: {str(e)}")
                console.print(
                    Panel(f"{message}: {str(e)}", title="Error", border_style="red")
                )

                if exit_on_error:
                    sys.exit(1)
                return None

        return cast(F, wrapper)

    return decorator


def exit_with_error(message: str, exit_code: int = 1) -> None:
    """Exit the program with an error message.

    Args:
        message: The error message to display
        exit_code: The exit code to use
    """
    console.print(Panel(message, title="Error", border_style="red"))
    logger.error(message)
    sys.exit(exit_code)


def display_warning(message: str) -> None:
    """Display a warning message to the user.

    Args:
        message: The warning message to display
    """
    console.print(Panel(message, title="Warning", border_style="yellow"))
    logger.warning(message)


def format_exception(exception: Exception) -> str:
    """Format an exception for display.

    Args:
        exception: The exception to format

    Returns:
        A formatted string representation of the exception
    """
    error_type = type(exception).__name__
    error_message = str(exception)
    return f"{error_type}: {error_message}"
