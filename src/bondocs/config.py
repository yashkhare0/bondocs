"""Configuration management for Bondocs.

Handles loading and accessing configuration from environment variables and TOML files.
"""

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import tomllib  # type: ignore
from dotenv import load_dotenv

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


def _should_reload_config() -> bool:
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


def load() -> dict[str, Any]:
    """Load configuration from .bondocs.toml and environment variables.

    Returns:
        A dictionary containing the merged configuration from defaults,
        config file, and environment variables.
    """
    global _config_cache, _last_load_time

    # Use cached config if available and not expired
    if not _should_reload_config():
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
            print(f"[yellow]Warning: Failed to load .bondocs.toml: {e}[/]")

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
            print(f"[yellow]Warning: Invalid BONDOCS_MAX_TOKENS value: {max_tokens}[/]")

    # Update cache and timestamp
    _config_cache = config.copy()
    _last_load_time = time.time()

    return config


@lru_cache(maxsize=32)
def get(key: str, default: Optional[Any] = None) -> Any:
    """Get a specific configuration value.

    Args:
        key: The configuration key to retrieve
        default: Default value to return if the key doesn't exist

    Returns:
        The configuration value for the specified key, or the default value
        if the key doesn't exist
    """
    return load().get(key, default)


def env(key: str) -> Optional[str]:
    """Get an environment variable value.

    Args:
        key: The environment variable name.

    Returns:
        The value of the environment variable or None if not set.
    """
    return os.getenv(key)


def reset_cache() -> None:
    """Reset the configuration cache.

    This can be used in tests or when configuration changes are expected.
    """
    global _config_cache, _last_load_time
    _config_cache = {}
    _last_load_time = 0
    get.cache_clear()  # Clear the lru_cache for the get function
