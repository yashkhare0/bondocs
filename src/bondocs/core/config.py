"""Configuration management for Bondocs.

Handles loading and accessing configuration from environment variables and TOML files.
"""

import os
import time
from pathlib import Path
from typing import Any, Optional

import tomllib  # type: ignore
from dotenv import load_dotenv

from .errors import (
    BondocsError,
    ErrorSeverity,
    handle_errors,
    log_error,
    safe_execution,
)
from .interfaces import ConfigProvider

# Load environment variables from .env file
load_dotenv()

# Updated defaults to match new system
DEFAULTS = {
    "provider": "ollama",
    "fallback_provider": "openai",
    "model": "mistral-small3.1:latest",
    "max_tokens": 1024,
}

# Cache timeout in seconds
CACHE_TIMEOUT = 30
_last_load_time: float = 0
_config_cache: dict[str, Any] = {}


class ConfigError(BondocsError):
    """Error raised during configuration operations."""

    pass


class Config(ConfigProvider):
    """Configuration provider implementation."""

    def __init__(self):
        """Initialize the configuration provider."""
        # Initial config load
        self.get_config()

    def _should_reload_config(self) -> bool:
        """Check if the config cache should be reloaded.

        Returns:
            True if the cache is empty or has expired, False otherwise
        """
        global _last_load_time
        current_time = time.time()

        # If cache is empty or expired, reload
        if not _config_cache or (current_time - _last_load_time) > CACHE_TIMEOUT:
            return True

        # Check if the config file has been modified since last load
        path = Path(".") / ".bondocs.toml"
        if path.exists():
            return path.stat().st_mtime > _last_load_time

        return False

    @handle_errors(ConfigError, severity=ErrorSeverity.WARNING)
    def get_config(self) -> dict[str, Any]:
        """Get the complete configuration.

        Returns:
            The complete configuration as a dictionary

        Raises:
            ConfigError: If loading the configuration fails
        """
        global _config_cache, _last_load_time

        # Use cached config if available and not expired
        if not self._should_reload_config():
            return _config_cache.copy()

        # Start with defaults
        config = DEFAULTS.copy()

        # Load from .bondocs.toml if it exists
        path = Path(".") / ".bondocs.toml"
        if path.exists():
            try:
                toml_config = tomllib.loads(path.read_text())
                config.update(toml_config)
            except Exception as e:
                log_error(
                    ConfigError(f"Failed to load .bondocs.toml: {e}"),
                    severity=ErrorSeverity.WARNING,
                )

        # Environment variables take precedence
        if provider := os.getenv("BONDOCS_PROVIDER"):
            config["provider"] = provider
        if fallback_provider := os.getenv("BONDOCS_FALLBACK_PROVIDER"):
            config["fallback_provider"] = fallback_provider
        if model := os.getenv("BONDOCS_MODEL"):
            config["model"] = model
        if max_tokens := os.getenv("BONDOCS_MAX_TOKENS"):
            try:
                config["max_tokens"] = int(max_tokens)
            except ValueError:
                log_error(
                    ConfigError(f"Invalid BONDOCS_MAX_TOKENS value: {max_tokens}"),
                    severity=ErrorSeverity.WARNING,
                )

        # Update cache and timestamp
        _config_cache = config.copy()
        _last_load_time = time.time()

        return config

    def get_value(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a specific configuration value.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if the key doesn't exist

        Returns:
            The configuration value for the specified key, or the default value
            if the key doesn't exist
        """
        return self.get_config().get(key, default)

    @handle_errors(ConfigError, severity=ErrorSeverity.INFO)
    def get_env(self, key: str) -> Optional[str]:
        """Get an environment variable value.

        Args:
            key: The environment variable name.

        Returns:
            The value of the environment variable or None if not set.

        Raises:
            ConfigError: If accessing the environment variable fails
        """
        try:
            return os.getenv(key)
        except Exception as e:
            raise ConfigError(
                f"Failed to get environment variable {key}: {str(e)}"
            ) from e

    @safe_execution("Failed to reset configuration cache")
    def reset_cache(self) -> None:
        """Reset the configuration cache.

        This can be used in tests or when configuration changes are expected.
        """
        global _config_cache, _last_load_time
        _config_cache = {}
        _last_load_time = 0
        # No need to clear lru_cache as we're not using it anymore


# Global singleton instance for convenience
config = Config()


# Legacy functions for backward compatibility
def load() -> dict[str, Any]:
    """Load configuration (legacy function)."""
    return config.get_config()


def get(key: str, default: Optional[Any] = None) -> Any:
    """Get a configuration value (legacy function)."""
    return config.get_value(key, default)


def env(key: str) -> Optional[str]:
    """Get an environment variable (legacy function)."""
    return config.get_env(key)


def reset_cache() -> None:
    """Reset the configuration cache (legacy function)."""
    config.reset_cache()
