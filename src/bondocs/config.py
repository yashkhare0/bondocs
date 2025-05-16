"""Configuration management for Bondocs.

Handles loading and accessing configuration from environment variables and TOML files.
"""

import os
from pathlib import Path
from typing import Any

import tomllib
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


def load() -> dict[str, Any]:
    """Load configuration from .bondocs.toml and environment variables."""
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

    return config


def get(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    return load().get(key, default)


def env(key: str) -> str | None:
    """Get an environment variable value.

    Args:
        key: The environment variable name.

    Returns:
        The value of the environment variable or None if not set.
    """
    return os.getenv(key)
