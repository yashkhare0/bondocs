"""Tests for the error handling system."""

from unittest.mock import patch

from bondocs.core.errors import (
    BondocsError,
    ErrorSeverity,
    display_warning,
    exit_with_error,
    format_exception,
    handle_errors,
    log_error,
    safe_execution,
)


class TestError(BondocsError):
    """Test error class."""

    pass


# Test the error inheritance
def test_error_inheritance():
    """Test that custom errors inherit from BondocsError."""
    error = TestError("test error")
    assert isinstance(error, BondocsError)
    assert isinstance(error, Exception)
    assert str(error) == "test error"


# Test the handle_errors decorator
def test_handle_errors_decorator():
    """Test the handle_errors decorator."""

    @handle_errors(TestError, default_return="default")
    def raises_error():
        raise TestError("test error")

    @handle_errors(TestError, default_return="default")
    def returns_value():
        return "value"

    # Test with error
    assert raises_error() == "default"

    # Test without error
    assert returns_value() == "value"


# Test the safe_execution decorator
def test_safe_execution_decorator():
    """Test the safe_execution decorator."""

    @safe_execution("Test operation failed", exit_on_error=False)
    def raises_error():
        raise Exception("test error")

    @safe_execution("Test operation failed", exit_on_error=False)
    def returns_value():
        return "value"

    # Test with error
    assert raises_error() is None

    # Test without error
    assert returns_value() == "value"


# Test logging with different severity levels
@patch("bondocs.core.errors.logger")
def test_log_error_severity(mock_logger):
    """Test logging errors with different severity levels."""
    error = TestError("test error")

    # Test INFO level
    log_error(error, severity=ErrorSeverity.INFO)
    mock_logger.info.assert_called_once()
    mock_logger.info.reset_mock()

    # Test WARNING level
    log_error(error, severity=ErrorSeverity.WARNING)
    mock_logger.warning.assert_called_once()
    mock_logger.warning.reset_mock()

    # Test ERROR level
    log_error(error, severity=ErrorSeverity.ERROR)
    mock_logger.error.assert_called_once()
    mock_logger.error.reset_mock()

    # Test CRITICAL level
    log_error(error, severity=ErrorSeverity.CRITICAL)
    mock_logger.critical.assert_called_once()


# Test exit_with_error
@patch("bondocs.core.errors.sys.exit")
@patch("bondocs.core.errors.console.print")
@patch("bondocs.core.errors.logger.error")
def test_exit_with_error(mock_logger_error, mock_console_print, mock_exit):
    """Test exiting with an error message."""
    exit_with_error("test error", exit_code=42)
    mock_logger_error.assert_called_once()
    mock_console_print.assert_called_once()
    mock_exit.assert_called_once_with(42)


# Test display_warning
@patch("bondocs.core.errors.console.print")
@patch("bondocs.core.errors.logger.warning")
def test_display_warning(mock_logger_warning, mock_console_print):
    """Test displaying a warning message."""
    display_warning("test warning")
    mock_logger_warning.assert_called_once()
    mock_console_print.assert_called_once()


# Test format_exception
def test_format_exception():
    """Test formatting an exception."""
    error = TestError("test error")
    formatted = format_exception(error)
    assert "TestError: test error" == formatted
