"""LLM integration module for Bondocs.

Provides a unified interface to different LLM backends including
Ollama, OpenAI, Anthropic, and Azure.
"""

import os

import httpx
from dotenv import load_dotenv
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from .config import env, get
from .prompt import load_system_prompt

# Load environment variables
load_dotenv()


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
        self.backend = self._detect()
        self.system_prompt = load_system_prompt()

    def _detect(self):
        provider = get("provider", "ollama").lower()
        model = get("model", "mistral-small3.1:latest")

        if provider == "ollama":
            try:
                # Check if Ollama is running
                httpx.get("http://localhost:11434", timeout=0.2)
                return ChatOllama(
                    model=model,
                    temperature=0.2,
                    base_url=os.getenv("API_URL", "http://localhost:11434"),
                )
            except Exception as e:
                # Get fallback provider from configuration
                fallback_provider = get("fallback_provider", "openai").lower()
                print(
                    f"[yellow]Warning: Ollama not available ({str(e)}). "
                    f"Falling back to {fallback_provider}.[/]"
                )
                provider = fallback_provider

        if provider == "openai":
            api_key = env("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required "
                    "for OpenAI provider"
                )
            return ChatOpenAI(
                model_name=model,
                temperature=0.2,
                max_tokens=get("max_tokens", 1024),
                api_key=api_key,
            )

        if provider == "anthropic":
            api_key = env("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required "
                    "for Anthropic provider"
                )
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model,
                temperature=0.2,
                max_tokens=get("max_tokens", 1024),
                anthropic_api_key=api_key,
            )

        if provider == "azure":
            api_key = env("AZURE_AI_API_KEY")
            if not api_key:
                raise ValueError(
                    "AZURE_AI_API_KEY environment variable is required for Azure provider"  # noqa: E501
                )
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                deployment_name=model,
                temperature=0.2,
                max_tokens=get("max_tokens", 1024),
                api_key=api_key,
                api_version="2024-02-15-preview",
            )

        raise ValueError(f"Unsupported provider: {provider}")

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
        resp = self.backend(messages)
        # some backends return list
        if isinstance(resp, list):
            resp = resp[0]
        if isinstance(resp, AIMessage):
            return resp.content
        return resp
