from unittest.mock import MagicMock, patch

import pytest
from bondocs.llm import LLMBackend


@pytest.fixture
def mock_config(monkeypatch):
    """Mock the config module to control settings for tests."""
    config_values = {
        "provider": "ollama",
        "fallback_provider": "openai",
        "model": "mistral-small3.1:latest",
        "max_tokens": 1024,
    }

    def mock_get(key, default=None):
        return config_values.get(key, default)

    def mock_env(key):
        # Mock environment variables for API keys
        env_vars = {
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "AZURE_AI_API_KEY": "test-azure-key",
        }
        return env_vars.get(key)

    monkeypatch.setattr("bondocs.llm.get", mock_get)
    monkeypatch.setattr("bondocs.llm.env", mock_env)

    # Function to update config for tests
    def update_config(**kwargs):
        config_values.update(kwargs)

    return update_config


@pytest.fixture
def mock_httpx_get(monkeypatch):
    """Mock httpx.get to control Ollama availability."""
    mock = MagicMock()
    monkeypatch.setattr("httpx.get", mock)
    return mock


def test_ollama_backend_selection(mock_config, mock_httpx_get):
    """Test that Ollama is selected when available."""
    # Configure httpx to simulate Ollama is available
    mock_httpx_get.return_value = MagicMock()

    # Test with default config (Ollama provider)
    with patch(
        "langchain_community.chat_models.ChatOllama.__init__", return_value=None
    ) as mock_ollama:
        backend = LLMBackend()
        mock_ollama.assert_called_once()


def test_fallback_to_openai(mock_config, mock_httpx_get):
    """Test fallback to OpenAI when Ollama is unavailable."""
    # Configure httpx to simulate Ollama is unavailable
    mock_httpx_get.side_effect = Exception("Connection refused")

    # Test with OpenAI fallback
    with patch(
        "langchain_openai.ChatOpenAI.__init__", return_value=None
    ) as mock_openai:
        backend = LLMBackend()
        mock_openai.assert_called_once()


def test_fallback_to_anthropic(mock_config, mock_httpx_get):
    """Test fallback to Anthropic when Ollama is unavailable."""
    # Configure httpx to simulate Ollama is unavailable
    mock_httpx_get.side_effect = Exception("Connection refused")

    # Set fallback provider to Anthropic
    mock_config(fallback_provider="anthropic")

    with patch(
        "langchain_anthropic.ChatAnthropic.__init__", return_value=None
    ) as mock_anthropic:
        backend = LLMBackend()
        mock_anthropic.assert_called_once()


def test_fallback_to_azure(mock_config, mock_httpx_get):
    """Test fallback to Azure when Ollama is unavailable."""
    # Configure httpx to simulate Ollama is unavailable
    mock_httpx_get.side_effect = Exception("Connection refused")

    # Set fallback provider to Azure
    mock_config(fallback_provider="azure")

    with patch(
        "langchain_openai.AzureChatOpenAI.__init__", return_value=None
    ) as mock_azure:
        backend = LLMBackend()
        mock_azure.assert_called_once()


def test_direct_provider_selection(mock_config):
    """Test direct provider selection without fallback."""
    # Test OpenAI as primary provider
    mock_config(provider="openai")

    with patch(
        "langchain_openai.ChatOpenAI.__init__", return_value=None
    ) as mock_openai:
        backend = LLMBackend()
        mock_openai.assert_called_once()

    # Test Anthropic as primary provider
    mock_config(provider="anthropic")

    with patch(
        "langchain_anthropic.ChatAnthropic.__init__", return_value=None
    ) as mock_anthropic:
        backend = LLMBackend()
        mock_anthropic.assert_called_once()

    # Test Azure as primary provider
    mock_config(provider="azure")

    with patch(
        "langchain_openai.AzureChatOpenAI.__init__", return_value=None
    ) as mock_azure:
        backend = LLMBackend()
        mock_azure.assert_called_once()


def test_error_on_missing_api_key(mock_config):
    """Test error is raised when API key is missing."""
    # Configure to use OpenAI but with missing API key
    mock_config(provider="openai")

    with patch("bondocs.llm.env", return_value=None):
        with pytest.raises(ValueError, match="OPENAI_API_KEY.*required"):
            backend = LLMBackend()

    # Configure to use Anthropic but with missing API key
    mock_config(provider="anthropic")

    with patch("bondocs.llm.env", return_value=None):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY.*required"):
            backend = LLMBackend()

    # Configure to use Azure but with missing API key
    mock_config(provider="azure")

    with patch("bondocs.llm.env", return_value=None):
        with pytest.raises(ValueError, match="AZURE_AI_API_KEY.*required"):
            backend = LLMBackend()


def test_unsupported_provider(mock_config):
    """Test error is raised for unsupported provider."""
    # Configure to use an unsupported provider
    mock_config(provider="unsupported")

    with pytest.raises(ValueError, match="Unsupported provider"):
        backend = LLMBackend()


def test_chat_response_handling(mock_config):
    """Test that chat responses are properly handled."""
    # Mock the backend response
    mock_backend = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Test response"
    mock_backend.return_value = mock_response

    backend = LLMBackend()
    backend.backend = mock_backend

    response = backend.chat("Test prompt")
    assert response == "Test response"

    # Test handling of list response
    mock_backend.return_value = [mock_response]
    response = backend.chat("Test prompt")
    assert response == "Test response"
