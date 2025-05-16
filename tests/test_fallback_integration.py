import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from bondocs.config import load
from bondocs.llm import LLMBackend


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace with configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_cwd = os.getcwd()
        os.chdir(temp_dir)

        # Create a minimal .bondocs.toml file
        bondocs_config = """
        # Bondocs configuration
        provider = "ollama"
        fallback_provider = "openai"
        model = "mixtral"
        max_tokens = 800
        """
        Path(".bondocs.toml").write_text(bondocs_config)

        # Initialize git repo
        subprocess.run(["git", "init", "-q"], check=True)
        Path("README.md").write_text("# Test Project\n\nInitial content.")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit", "-q"], check=True)

        yield temp_dir

        # Clean up
        os.chdir(old_cwd)


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Set up environment variables for API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("AZURE_AI_API_KEY", "test-azure-key")


def test_config_loading_in_workspace(temp_workspace):
    """Test that configuration is properly loaded from the workspace."""
    config = load()
    assert config["provider"] == "ollama"
    assert config["fallback_provider"] == "openai"
    assert config["model"] == "mixtral"
    assert config["max_tokens"] == 800


def test_fallback_behavior_with_ollama_unavailable(temp_workspace, mock_api_keys):
    """Test the fallback behavior when Ollama is unavailable."""
    # We'll patch the httpx.get to simulate Ollama being unavailable
    with patch("httpx.get", side_effect=Exception("Connection refused")):
        # And patch the OpenAI client to verify it's created
        with patch(
            "langchain_openai.ChatOpenAI.__init__", return_value=None
        ) as mock_openai:
            # Initialize the LLM backend
            backend = LLMBackend()

            # Verify OpenAI was used as fallback
            mock_openai.assert_called_once()

            # Verify the model name passed to OpenAI is correct
            assert mock_openai.call_args[1]["model_name"] == "mixtral"


def test_env_var_override_in_workspace(temp_workspace, mock_api_keys):
    """Test that environment variables override workspace config."""
    # Set environment variables to override the workspace config
    os.environ["BONDOCS_PROVIDER"] = "anthropic"
    os.environ["BONDOCS_FALLBACK_PROVIDER"] = "azure"
    os.environ["BONDOCS_MODEL"] = "claude-3-opus"

    # Reload config
    config = load()
    assert config["provider"] == "anthropic"
    assert config["fallback_provider"] == "azure"
    assert config["model"] == "claude-3-opus"

    # Clean up
    del os.environ["BONDOCS_PROVIDER"]
    del os.environ["BONDOCS_FALLBACK_PROVIDER"]
    del os.environ["BONDOCS_MODEL"]


def test_new_file_with_ollama_fallback(temp_workspace, mock_api_keys):
    """Test adding a new file with ollama fallback."""
    # Create and stage a new file
    Path("src").mkdir(exist_ok=True)
    Path("src/app.py").write_text('print("Hello from Bondocs!")')
    subprocess.run(["git", "add", "src/app.py"], check=True)

    # Mock the LLMBackend to simulate the fallback behavior
    with patch("bondocs.llm.LLMBackend") as mock_llm:
        # Configure the mock to return a patch
        instance = mock_llm.return_value
        instance.chat.return_value = """--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # Test Project

 Initial content.
+
+Check out `src/app.py` for a greeting message.
"""

        # When running the bondocs CLI
        with patch("httpx.get", side_effect=Exception("Connection refused")):
            from bondocs.cli import run

            run()

            # Verify that LLMBackend was properly created
            mock_llm.assert_called_once()

            # Verify the README was updated
            readme_content = Path("README.md").read_text()
            assert "Check out `src/app.py`" in readme_content


def test_change_provider_in_config(temp_workspace, mock_api_keys):
    """Test changing provider in configuration file."""
    # Update the config file to use a different provider
    new_config = """
    # Bondocs configuration
    provider = "anthropic"
    fallback_provider = "azure"
    model = "claude-3-sonnet"
    max_tokens = 1000
    """
    Path(".bondocs.toml").write_text(new_config)

    # Reload the config
    config = load()
    assert config["provider"] == "anthropic"
    assert config["fallback_provider"] == "azure"

    # Test with the anthropic provider directly (no fallback)
    with patch(
        "langchain_anthropic.ChatAnthropic.__init__", return_value=None
    ) as mock_anthropic:
        backend = LLMBackend()
        mock_anthropic.assert_called_once()

        # Verify the model name passed to Anthropic is correct
        assert mock_anthropic.call_args[1]["model"] == "claude-3-sonnet"
