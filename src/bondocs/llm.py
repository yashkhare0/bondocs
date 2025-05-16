"""LLM integration module for Bondocs.

Provides a unified interface to different LLM backends including
Ollama, OpenAI, Anthropic, and Azure.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Union

import httpx
from dotenv import load_dotenv

# Type ignore comments for libraries without stubs
from langchain.schema import AIMessage, HumanMessage, SystemMessage  # type: ignore

from .config import env, get
from .prompt import load_system_prompt

# Load environment variables
load_dotenv()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_response(
        self, messages: list[Union[SystemMessage, HumanMessage]]
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
        self, messages: list[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(messages)

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
            ValueError: If the OpenAI API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_openai import ChatOpenAI  # type: ignore

        api_key = env("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider"
            )

        self.model = model
        self.client = ChatOpenAI(
            model_name=model,
            temperature=0.2,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    def generate_response(
        self, messages: list[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(messages)


class AnthropicProvider(LLMProvider):
    """Anthropic provider for cloud LLM inference."""

    def __init__(self, model: str, max_tokens: int):
        """Initialize the Anthropic provider.

        Args:
            model (str): The model to use.
            max_tokens (int): The maximum number of tokens to generate.

        Raises:
            ValueError: If the Anthropic API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_anthropic import ChatAnthropic  # type: ignore

        api_key = env("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"  # noqa: E501
            )

        self.model = model
        self.client = ChatAnthropic(
            model=model,
            temperature=0.2,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
        )

    def generate_response(
        self, messages: list[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(messages)


class AzureProvider(LLMProvider):
    """Azure provider for cloud LLM inference."""

    def __init__(self, model: str, max_tokens: int):
        """Initialize the Azure provider.

        Args:
            model (str): The model to use.
            max_tokens (int): The maximum number of tokens to generate.

        Raises:
            ValueError: If the Azure API key is not set.
        """
        # Import here to avoid startup overhead if not used
        from langchain_openai import AzureChatOpenAI  # type: ignore

        api_key = env("AZURE_AI_API_KEY")
        if not api_key:
            raise ValueError(
                "AZURE_AI_API_KEY environment variable is required for Azure provider"
            )

        self.model = model
        self.client = AzureChatOpenAI(
            deployment_name=model,
            temperature=0.2,
            max_tokens=max_tokens,
            api_key=api_key,
            api_version="2024-02-15-preview",
        )

    def generate_response(
        self, messages: list[Union[SystemMessage, HumanMessage]]
    ) -> Any:
        """Generate a response from the LLM based on the input messages."""
        return self.client(messages)


class ProviderFactory:
    """Factory for creating LLM providers."""

    _PROVIDERS = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "azure": AzureProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_name: Name of the provider to create.

        Returns:
            An instance of the requested provider.

        Raises:
            ValueError: If the provider is not supported.
        """
        provider_class = cls._PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider_name}")

        model = get("model", "mistral-small3.1:latest")
        max_tokens = get("max_tokens", 1024)

        if provider_name == "ollama":
            return provider_class(model)
        return provider_class(model, max_tokens)


class LLMBackend:
    """Large Language Model backend integration.

    Handles detection and initialization of the appropriate language model
    provider based on configuration, with automatic fallback from Ollama
    to other providers if needed.
    """

    def __init__(self):
        """Initialize the LLM backend.

        Detects and initializes the appropriate language model based on
        the current configuration.
        """
        self.backend = self._initialize_provider()
        self.system_prompt = load_system_prompt()

    def _initialize_provider(self) -> LLMProvider:
        """Initialize the appropriate provider based on configuration and availability.

        Returns:
            An initialized provider instance based on configuration

        Raises:
            ValueError: If no suitable provider can be initialized
        """
        primary_provider = get("provider", "ollama").lower()
        fallback_provider = get("fallback_provider", "openai").lower()

        # Try primary provider first
        if primary_provider == "ollama" and not OllamaProvider.is_available():
            print(
                f"[yellow]Warning: Ollama not available. "
                f"Falling back to {fallback_provider}.[/]"
            )
            return ProviderFactory.create(fallback_provider)

        try:
            return ProviderFactory.create(primary_provider)
        except ValueError as e:
            if primary_provider != fallback_provider:
                print(
                    f"[yellow]Warning: {str(e)}. "
                    f"Falling back to {fallback_provider}.[/]"
                )
                return ProviderFactory.create(fallback_provider)
            raise

    def chat(self, prompt: str) -> str:
        """Send a prompt to the LLM and get a response.

        Args:
            prompt: The text prompt to send to the LLM.

        Returns:
            The text response from the LLM.
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]
        resp = self.backend.generate_response(messages)
        # some backends return list
        if isinstance(resp, list):
            resp = resp[0]
        if isinstance(resp, AIMessage):
            return resp.content
        return resp
