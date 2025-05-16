"""Core modules for Bondocs.

This package contains the core functionality of Bondocs, including:
- Error handling
- Configuration
- Interfaces
"""

from bondocs.core.config import config
from bondocs.core.errors import (
    BondocsError,
    ConfigError,
    ErrorSeverity,
    GitError,
    LLMError,
    PatchError,
    display_warning,
    exit_with_error,
    handle_errors,
    log_error,
    safe_execution,
)
from bondocs.core.interfaces import (
    ConfigProvider,
    DocumentManager,
    GitInterface,
    LLMInterface,
)
