"""Bondocs: Git-native, LLM-powered documentation guardrails.

Automatically keep your README.md and documentation in sync with code changes
using LLMs.
"""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0"

# Export core functionality
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

# Export document functionality
from bondocs.document import (
    apply_patch,
    doc_manager,
    generate_readme_patch,
    update_changelog,
    update_runbooks,
)

# Export git functionality
from bondocs.git import git, summarize_diff

# Export LLM functionality
from bondocs.providers import llm
