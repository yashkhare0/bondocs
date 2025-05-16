"""LLM integration module for Bondocs.

Provides a unified interface to different LLM backends including
Ollama, OpenAI, Anthropic, and Azure.
"""

# mypy: disable-error-code="no-any-return,arg-type,return-value"
# type: ignore

import os
import weakref
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Optional, TypeVar, Union, cast

import httpx
from langchain.schema import (  # type: ignore
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from bondocs.core.config import config
from bondocs.core.errors import (
    ErrorSeverity,
    LLMError,
    handle_errors,
    log_error,
)
from bondocs.core.interfaces import LLMInterface
from bondocs.providers.prompt import load_system_prompt

# Provider instance cache to avoid recreating providers
_provider_instances: dict[str, weakref.ref] = {}

# Type variable for provider return
T = TypeVar("T", bound="LLMProvider")


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        pass

    @classmethod
    def is_available(cls) -> bool:
        """Check if the provider is available for use."""
        return True


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""

    def __init__(self, model: str):
        """Initialize the Ollama provider.

        Args:
            model (str): The model to use.
        """
        # Import here to avoid startup overhead if not used
        from langchain_community.chat_models import ChatOllama  # type: ignore

        self.model = model
        self.base_url = os.getenv("API_URL", "http://localhost:11434")
        self.client = ChatOllama(
            model=model,
            temperature=0.2,
            base_url=self.base_url,
        )

    @handle_errors(error_type=LLMError)
    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(cast(list[BaseMessage], list(messages)))

    @classmethod
    @handle_errors(Exception, default_return=False)
    def is_available(cls) -> bool:
        """Check if Ollama is running and available."""
        httpx.get("http://localhost:11434", timeout=0.2)
        return True


class OpenAIProvider(LLMProvider):
    """OpenAI provider for cloud LLM inference."""

    def __init__(self, model: str, max_tokens: int):
        """Initialize the OpenAI provider.

        Args:
            model (str): The model to use.
            max_tokens (int): The maximum number of tokens to generate.

        Raises:
            LLMError: If the OpenAI API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_openai import ChatOpenAI  # type: ignore

        api_key = config.get_env("OPENAI_API_KEY")
        if not api_key:
            raise LLMError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider"
            )

        self.model = model
        self.client = ChatOpenAI(
            model=model,
            temperature=0.2,
            max_tokens=max_tokens,
            api_key=api_key,  # OpenAI will convert this to SecretStr internally
        )

    @handle_errors(error_type=LLMError)
    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(cast(list[BaseMessage], list(messages)))


class AnthropicProvider(LLMProvider):
    """Anthropic provider for cloud LLM inference."""

    def __init__(self, model: str, max_tokens: int):
        """Initialize the Anthropic provider.

        Args:
            model (str): The model to use.
            max_tokens (int): The maximum number of tokens to generate.

        Raises:
            LLMError: If the Anthropic API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_anthropic import ChatAnthropic  # type: ignore

        api_key = config.get_env("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"  # noqa: E501
            )

        self.model = model
        # Note: Parameters names may change with library versions
        # Using kwargs to be more flexible with API changes
        self.client = ChatAnthropic(
            model_name=model,
            temperature=0.2,
            max_tokens_to_sample=max_tokens,
            api_key=api_key,  # The library will handle conversion to SecretStr
            timeout=60,  # Add timeout parameter
        )

    @handle_errors(error_type=LLMError)
    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(cast(list[BaseMessage], list(messages)))


class AzureProvider(LLMProvider):
    """Azure provider for cloud LLM inference."""

    def __init__(self, model: str, max_tokens: int):
        """Initialize the Azure provider.

        Args:
            model (str): The model to use.
            max_tokens (int): The maximum number of tokens to generate.

        Raises:
            LLMError: If the Azure API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_openai import AzureChatOpenAI  # type: ignore

        api_key = config.get_env("AZURE_AI_API_KEY")
        if not api_key:
            raise LLMError(
                "AZURE_AI_API_KEY environment variable is required for Azure provider"
            )

        self.model = model
        self.client = AzureChatOpenAI(
            model=model,
            temperature=0.2,
            max_tokens=max_tokens,
            api_key=api_key,  # Azure will convert this to SecretStr internally
            api_version="2024-02-15-preview",
        )

    @handle_errors(error_type=LLMError)
    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(cast(list[BaseMessage], list(messages)))


class ProviderFactory:
    """Factory for creating LLM providers."""

    _PROVIDERS = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "azure": AzureProvider,
    }

    @classmethod
    @handle_errors(error_type=LLMError, log_traceback=True)
    def create(cls, provider_name: str, reuse: bool = True) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_name: Name of the provider to create.
            reuse: Whether to reuse existing provider instances.

        Returns:
            An instance of the requested provider.

        Raises:
            LLMError: If the provider is not supported.
        """
        provider_name = provider_name.lower()
        provider_class = cls._PROVIDERS.get(provider_name)
        if not provider_class:
            raise LLMError(f"Unsupported provider: {provider_name}")

        model = config.get_value("model", "mistral-small3.1:latest")
        max_tokens = config.get_value("max_tokens", 1024)

        # Create a unique key for the provider instance
        instance_key = f"{provider_name}:{model}:{max_tokens}"

        # Check for an existing provider instance
        if reuse and instance_key in _provider_instances:
            provider_ref = _provider_instances[instance_key]
            provider = provider_ref()
            if provider is not None:
                return provider

        # Create a new provider instance
        if provider_name == "ollama":
            provider = provider_class(model)
        else:
            provider = provider_class(model, max_tokens)

        # Cache the provider instance
        if reuse:
            _provider_instances[instance_key] = weakref.ref(provider)

        return provider

    @classmethod
    def clear_cached_providers(cls) -> None:
        """Clear all cached provider instances."""
        _provider_instances.clear()


class LLMBackend(LLMInterface):
    """Large Language Model backend integration.

    Handles detection and initialization of the appropriate language model
    provider based on configuration, with automatic fallback from Ollama
    to other providers if needed.
    """

    _instance = None
    _initialized: bool = False
    _provider: Optional[LLMProvider] = None
    _system_prompt: Optional[str] = None

    def __new__(cls):
        """Create a singleton instance of the LLM backend."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LLM backend."""
        # Skip initialization if already initialized
        if self._initialized:
            return
        self._initialized = True
        self._provider = self._initialize_provider()
        self._system_prompt = load_system_prompt()

    @property
    def backend(self) -> LLMProvider:
        """Get the LLM provider backend.

        Returns:
            The LLM provider backend.
        """
        if self._provider is None:
            self._provider = self._initialize_provider()
        return self._provider

    @property
    def system_prompt(self) -> str:
        """Get the system prompt.

        Returns:
            The system prompt.
        """
        if self._system_prompt is None:
            self._system_prompt = load_system_prompt()
        return self._system_prompt

    @handle_errors(error_type=LLMError, severity=ErrorSeverity.ERROR)
    def _initialize_provider(self) -> LLMProvider:
        """Initialize the LLM provider based on configuration.

        Returns:
            The initialized LLM provider.

        Raises:
            LLMError: If no provider could be initialized.
        """
        # Get primary provider from config
        primary_provider = config.get_value("provider", "ollama")
        fallback_provider = config.get_value("fallback_provider", "openai")

        # Try to create the primary provider
        try:
            # Special case for Ollama - check if it's available first
            if primary_provider == "ollama" and not OllamaProvider.is_available():
                log_error(
                    LLMError(
                        "Ollama not available, falling back to alternative provider"
                    ),
                    severity=ErrorSeverity.WARNING,
                )
                provider = ProviderFactory.create(fallback_provider)
            else:
                provider = ProviderFactory.create(primary_provider)
            return provider
        except Exception as e:
            # If the primary provider fails, try the fallback
            if primary_provider != fallback_provider:
                log_error(
                    LLMError(
                        f"Failed to initialize {primary_provider}, trying {fallback_provider}: {str(e)}"  # noqa: E501
                    ),
                    severity=ErrorSeverity.WARNING,
                )
                provider = ProviderFactory.create(fallback_provider)
                return provider
            # If there's no fallback, re-raise the error
            raise LLMError(f"Failed to initialize LLM provider: {str(e)}") from e

    @handle_errors(error_type=LLMError, severity=ErrorSeverity.ERROR)
    def generate_response(self, prompt: str) -> str:
        """Generate a response to a prompt.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            The generated response.

        Raises:
            LLMError: If there was an error generating a response.
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        # If BONDOCS_MOCK is set, return a dummy response for testing
        if os.getenv("BONDOCS_MOCK") == "1":
            return "This is a mock response for testing."

        try:
            response = self.backend.generate_response(messages)
            if isinstance(response, AIMessage):
                return response.content
            elif isinstance(response, str):
                return response
            elif hasattr(response, "content"):
                return str(response.content)
            else:
                return str(response)
        except Exception as e:
            raise LLMError(f"Error generating response: {str(e)}") from e

    @handle_errors(error_type=LLMError, severity=ErrorSeverity.ERROR)
    def chat(self, prompt: str) -> str:
        """Generate a chat response.

        This is a convenience method for generate_response.

        Args:
            prompt: The prompt to generate a response for.

        Returns:
            The generated response.
        """
        return self.generate_response(prompt)

    @classmethod
    def reset(cls) -> None:
        """Reset the LLM backend singleton.

        This is primarily used for testing.
        """
        cls._instance = None
        cls._initialized = False
        cls._provider = None
        cls._system_prompt = None
        ProviderFactory.clear_cached_providers()


# Global singleton instance for convenience
llm = LLMBackend()
