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
from typing import Any, TypeVar, Union, cast

import httpx
from langchain.schema import (  # type: ignore
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from .config import config
from .interfaces import LLMError, LLMInterface
from .prompt import load_system_prompt

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

    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        try:
            return self.client(cast(list[BaseMessage], list(messages)))
        except Exception as e:
            raise LLMError(f"Error generating response from Ollama: {str(e)}") from e

    @classmethod
    def is_available(cls) -> bool:
        """Check if Ollama is running and available."""
        try:
            httpx.get("http://localhost:11434", timeout=0.2)
            return True
        except Exception:
            return False


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

    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        try:
            return self.client(cast(list[BaseMessage], list(messages)))
        except Exception as e:
            raise LLMError(f"Error generating response from OpenAI: {str(e)}") from e


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

    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        try:
            return self.client(cast(list[BaseMessage], list(messages)))
        except Exception as e:
            raise LLMError(f"Error generating response from Anthropic: {str(e)}") from e


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

    def generate_response(
        self, messages: Sequence[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        try:
            return self.client(cast(list[BaseMessage], list(messages)))
        except Exception as e:
            raise LLMError(f"Error generating response from Azure: {str(e)}") from e


class ProviderFactory:
    """Factory for creating LLM providers."""

    _PROVIDERS = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "azure": AzureProvider,
    }

    @classmethod
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
                return provider  # Type is correct as provider is LLMProvider

        # Create a new provider instance
        try:
            if provider_name == "ollama":
                provider = provider_class(model)
            else:
                provider = provider_class(model, max_tokens)

            if reuse:
                # Store weakref to avoid memory leaks
                _provider_instances[instance_key] = weakref.ref(provider)

            return provider  # Type is correct as provider is LLMProvider
        except Exception as e:
            raise LLMError(
                f"Failed to create provider {provider_name}: {str(e)}"
            ) from e

    @classmethod
    def clear_cached_providers(cls) -> None:
        """Clear all cached provider instances."""
        global _provider_instances
        _provider_instances = {}


class LLMBackend(LLMInterface):
    """Large Language Model backend integration.

    Handles detection and initialization of the appropriate language model
    provider based on configuration, with automatic fallback from Ollama
    to other providers if needed.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Create a singleton instance of LLMBackend."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LLM backend.

        Detects and initializes the appropriate language model based on
        the current configuration.
        """
        # Skip initialization if already done (singleton pattern)
        if LLMBackend._initialized:
            return

        self._provider = None
        self._system_prompt = None
        LLMBackend._initialized = True

    @property
    def backend(self) -> LLMProvider:
        """Get the LLM provider instance, initializing it if needed.

        Returns:
            The LLM provider instance
        """
        if self._provider is None:
            self._provider = self._initialize_provider()
        return self._provider

    @property
    def system_prompt(self) -> str:
        """Get the system prompt, loading it if needed.

        Returns:
            The system prompt string
        """
        if self._system_prompt is None:
            self._system_prompt = load_system_prompt()
        return self._system_prompt

    def _initialize_provider(self) -> LLMProvider:
        """Initialize the appropriate provider based on configuration and availability.

        Returns:
            An initialized provider instance based on configuration

        Raises:
            LLMError: If no suitable provider can be initialized
        """
        primary_provider = config.get_value("provider", "ollama").lower()
        fallback_provider = config.get_value("fallback_provider", "openai").lower()

        # Try primary provider first
        if primary_provider == "ollama" and not OllamaProvider.is_available():
            print(
                f"[yellow]Warning: Ollama not available. "
                f"Falling back to {fallback_provider}.[/]"
            )
            return ProviderFactory.create(fallback_provider)

        try:
            return ProviderFactory.create(primary_provider)
        except LLMError as e:
            if primary_provider != fallback_provider:
                print(
                    f"[yellow]Warning: {str(e)}. "
                    f"Falling back to {fallback_provider}.[/]"
                )
                try:
                    return ProviderFactory.create(fallback_provider)
                except LLMError as e2:
                    raise LLMError(
                        f"Failed to initialize primary and fallback providers: {str(e2)}"  # noqa: E501
                    ) from e2
            raise

    def generate_response(self, prompt: str) -> str:
        """Generate a response to a prompt.

        Args:
            prompt: The prompt to generate a response for

        Returns:
            The generated response

        Raises:
            LLMError: If there was an error generating a response
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]
        try:
            resp = self.backend.generate_response(messages)
            # some backends return list
            if isinstance(resp, list) and resp:
                resp = resp[0]
            if isinstance(resp, AIMessage):
                return resp.content if resp.content is not None else ""
            if isinstance(resp, str):
                return resp
            # Last resort - convert whatever we got to a string
            try:
                return str(resp)
            except Exception:
                return ""  # Return empty string if conversion fails
        except Exception as e:
            raise LLMError(f"Error generating response: {str(e)}") from e

    # Legacy method for backward compatibility
    def chat(self, prompt: str) -> str:
        """Send a prompt to the LLM and get a response (legacy method).

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The generated response
        """
        try:
            return self.generate_response(prompt)
        except LLMError as e:
            # Keep backward compatibility by not raising exceptions
            print(f"[red]Error generating response: {str(e)}[/]")
            return ""

    @classmethod
    def reset(cls) -> None:
        """Reset the LLM backend.

        Clears the provider instance and initialized flag, forcing a new provider
        to be created on the next use. This is useful for testing or when
        configuration has changed.
        """
        if cls._instance is not None:
            cls._instance._provider = None
            cls._instance._system_prompt = None
        cls._initialized = False
        ProviderFactory.clear_cached_providers()


# Global singleton instance for convenience
llm = LLMBackend()
