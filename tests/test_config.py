import os
from unittest.mock import patch

import pytest
from bondocs.config import DEFAULTS, env, get, load


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing."""
    test_env = {
        "BONDOCS_PROVIDER": "openai",
        "BONDOCS_FALLBACK_PROVIDER": "anthropic",
        "BONDOCS_MODEL": "gpt-4-turbo",
        "BONDOCS_MAX_TOKENS": "2048",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "AZURE_AI_API_KEY": "test-azure-key",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def mock_toml_file():
    """Create a mock TOML file content."""
    return """
# Bondocs configuration
provider = "ollama"
fallback_provider = "openai"
model = "mixtral"
max_tokens = 800
temperature = 0.2

[documentation]
watch_files = ["src/**/*.py", "tests/**/*.py"]
sections = ["Usage", "API Reference"]

[ignore]
patterns = ["*.pyc", "__pycache__"]
"""


def test_defaults():
    """Test default configuration values."""
    assert DEFAULTS["provider"] == "ollama"
    assert DEFAULTS["fallback_provider"] == "openai"
    assert DEFAULTS["model"] == "mistral-small3.1:latest"
    assert DEFAULTS["max_tokens"] == 1024


def test_load_defaults():
    """Test loading default configuration when no file or env vars exist."""
    with patch("pathlib.Path.exists", return_value=False):
        config = load()
        assert config["provider"] == DEFAULTS["provider"]
        assert config["fallback_provider"] == DEFAULTS["fallback_provider"]
        assert config["model"] == DEFAULTS["model"]
        assert config["max_tokens"] == DEFAULTS["max_tokens"]


def test_load_from_toml(mock_toml_file):
    """Test loading configuration from TOML file."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value=mock_toml_file),
    ):
        config = load()
        assert config["provider"] == "ollama"
        assert config["fallback_provider"] == "openai"
        assert config["model"] == "mixtral"
        assert config["max_tokens"] == 800
        assert config["temperature"] == 0.2
        assert "documentation" in config
        assert "ignore" in config


def test_load_from_env(mock_env_vars):
    """Test that environment variables override defaults."""
    with patch("pathlib.Path.exists", return_value=False):
        config = load()
        assert config["provider"] == "openai"
        assert config["fallback_provider"] == "anthropic"
        assert config["model"] == "gpt-4-turbo"
        assert config["max_tokens"] == 2048


def test_env_overrides_toml(mock_env_vars, mock_toml_file):
    """Test that environment variables override TOML settings."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value=mock_toml_file),
    ):
        config = load()
        assert config["provider"] == "openai"  # From env, not toml
        assert config["fallback_provider"] == "anthropic"  # From env, not toml
        assert config["model"] == "gpt-4-turbo"  # From env, not toml
        assert config["max_tokens"] == 2048  # From env, not toml
        # But other TOML settings remain
        assert "documentation" in config
        assert "ignore" in config


def test_get_function():
    """Test the get function for retrieving specific config values."""
    with patch("bondocs.config.load", return_value={"test_key": "test_value"}):
        assert get("test_key") == "test_value"
        assert get("non_existent_key") is None
        assert get("non_existent_key", "default") == "default"


def test_env_function():
    """Test the env function for retrieving environment variables."""
    with patch.dict(os.environ, {"TEST_ENV_VAR": "test_value"}):
        assert env("TEST_ENV_VAR") == "test_value"
        assert env("NON_EXISTENT_VAR") is None


def test_invalid_max_tokens():
    """Test handling of invalid BONDOCS_MAX_TOKENS value."""
    with (
        patch.dict(os.environ, {"BONDOCS_MAX_TOKENS": "not_a_number"}),
        patch("pathlib.Path.exists", return_value=False),
    ):
        config = load()
        # Should fall back to default value
        assert config["max_tokens"] == DEFAULTS["max_tokens"]


def test_toml_parse_error():
    """Test handling of TOML parse errors."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="invalid toml content"),
        patch("builtins.print") as mock_print,
    ):
        config = load()
        # Should fall back to defaults
        assert config["provider"] == DEFAULTS["provider"]
        # Should print a warning
        mock_print.assert_called()
