import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bondocs.cli import config, run
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing Click commands."""
    return CliRunner()


@pytest.fixture
def mock_provider_env(monkeypatch):
    """Set up environment variables for provider configuration."""
    monkeypatch.setenv("BONDOCS_PROVIDER", "ollama")
    monkeypatch.setenv("BONDOCS_FALLBACK_PROVIDER", "openai")
    monkeypatch.setenv("BONDOCS_MODEL", "mixtral")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")


def test_config_command_shows_fallback_provider(cli_runner, mock_provider_env):
    """Test that the config command shows the fallback provider."""
    with patch(
        "bondocs.config.load",
        return_value={
            "provider": "ollama",
            "fallback_provider": "openai",
            "model": "mixtral",
            "max_tokens": 800,
        },
    ):
        result = cli_runner.invoke(config)
        assert result.exit_code == 0
        assert "provider: ollama" in result.output
        assert "fallback_provider: openai" in result.output


def test_run_command_with_ollama_available(cli_runner):
    """Test run command when Ollama is available."""
    # Create a temporary test environment
    with cli_runner.isolated_filesystem():
        # Mock git repo
        subprocess.run(["git", "init", "-q"], check=True)
        Path("README.md").write_text("# Test Project\n\nInitial content.")
        Path("src").mkdir()
        Path("src/app.py").write_text('print("test")')
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit", "-q"], check=True)
        subprocess.run(["git", "add", "src/app.py"], check=True)

        # Mock Ollama is available
        with patch("httpx.get", return_value=MagicMock()):
            # Mock LLM backend
            with patch("bondocs.llm.LLMBackend") as mock_llm_backend:
                # Configure the mock to return a patch
                instance = mock_llm_backend.return_value
                instance.chat.return_value = """--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # Test Project

 Initial content.
+
+See `src/app.py` for example code.
"""

                # Run the command
                result = cli_runner.invoke(run)

                # Verify it ran without error
                assert result.exit_code == 0
                # Verify Ollama was used (we patched httpx.get to simulate it's available)
                mock_llm_backend.assert_called_once()


def test_run_command_with_ollama_unavailable(cli_runner, mock_provider_env):
    """Test run command when Ollama is unavailable."""
    # Create a temporary test environment
    with cli_runner.isolated_filesystem():
        # Mock git repo
        subprocess.run(["git", "init", "-q"], check=True)
        Path("README.md").write_text("# Test Project\n\nInitial content.")
        Path("src").mkdir()
        Path("src/app.py").write_text('print("test")')
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit", "-q"], check=True)
        subprocess.run(["git", "add", "src/app.py"], check=True)

        # Mock Ollama is unavailable
        with patch("httpx.get", side_effect=Exception("Connection refused")):
            # Mock LLM backend with fallback message
            with patch("builtins.print") as mock_print:
                # Mock the chat response
                with patch(
                    "bondocs.llm.LLMBackend.chat",
                    return_value="""--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # Test Project

 Initial content.
+
+See `src/app.py` for example code.
""",
                ):
                    # Run the command
                    result = cli_runner.invoke(run)

                    # Verify it ran without error
                    assert result.exit_code == 0

                    # Check if fallback warning message was printed
                    fallback_message_printed = False
                    for call in mock_print.call_args_list:
                        args = call[0][0]
                        if isinstance(args, str) and "Falling back to openai" in args:
                            fallback_message_printed = True
                            break

                    assert (
                        fallback_message_printed
                    ), "Fallback message should be printed"


def test_run_command_with_empty_diff(cli_runner):
    """Test run command with empty diff (should exit without error)."""
    # Create a temporary test environment
    with cli_runner.isolated_filesystem():
        # Mock git repo with no staged changes
        subprocess.run(["git", "init", "-q"], check=True)
        Path("README.md").write_text("# Test Project\n\nInitial content.")
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit", "-q"], check=True)

        # Mock the staged_diff function to return empty
        with patch("bondocs.cli.staged_diff", return_value=""):
            result = cli_runner.invoke(run)
            # Should exit early (sys.exit(0))
            assert result.exit_code == 0


def test_run_command_with_empty_patch(cli_runner):
    """Test run command with empty patch from LLM."""
    # Create a temporary test environment
    with cli_runner.isolated_filesystem():
        # Mock git repo
        subprocess.run(["git", "init", "-q"], check=True)
        Path("README.md").write_text("# Test Project\n\nInitial content.")
        Path("src").mkdir()
        Path("src/app.py").write_text('print("test")')
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit", "-q"], check=True)
        subprocess.run(["git", "add", "src/app.py"], check=True)

        # Mock non-empty diff but empty patch
        with patch(
            "bondocs.cli.staged_diff",
            return_value="diff --git a/src/app.py b/src/app.py",
        ):
            with patch("bondocs.cli.summarize", return_value="src/app.py: added"):
                with patch("bondocs.cli.generate_patch", return_value=""):
                    with patch("builtins.print") as mock_print:
                        result = cli_runner.invoke(run)

                        # Should print a warning about empty patch
                        mock_print.assert_called()
                        empty_patch_warning = False
                        for call in mock_print.call_args_list:
                            args = call[0][0]
                            if isinstance(args, str) and "empty patch" in args:
                                empty_patch_warning = True
                                break

                        assert (
                            empty_patch_warning
                        ), "Warning about empty patch should be printed"


def test_config_command_with_env_override(cli_runner, mock_provider_env):
    """Test config command with environment variable overrides."""
    result = cli_runner.invoke(config)
    assert result.exit_code == 0
    assert "provider: ollama" in result.output
    assert "fallback_provider: openai" in result.output
    assert "model: mixtral" in result.output
