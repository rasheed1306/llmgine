"""LLM Provider interfaces and implementations.

This module defines the core LLM provider protocol and manager interfaces,
as well as concrete implementations.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Protocol

from llmgine.llm import (
    ModelFormattedDictTool,
    ToolChoiceOrDictType,
)
from llmgine.llm.providers.response import LLMResponse
from llmgine.llm.tools import ToolCall


class LLMProvider(Protocol):
    """Protocol defining the interface for an LLM provider."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ModelFormattedDictTool]] = None,
        tool_choice: ToolChoiceOrDictType = "auto",
        parallel_tool_calls: Optional[bool] = None,
        temperature: Optional[float] = None,
        max_completion_tokens: int = 5068,
        response_format: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt to send to the LLM
            context: Optional conversation context/history
            system_prompt: Optional system prompt/instructions
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens for the response
            model: Optional model name/identifier
            tools: Optional list of tools to provide to the LLM
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The response from the LLM
        """
        ...


class LLMManager(ABC):
    """Interface for managing LLM providers and models."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[ModelFormattedDictTool]] = None,
        tool_choice: ToolChoiceOrDictType = "auto",
        temperature: Optional[float] = None,
        max_completion_tokens: int = 5068,
        response_format: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from an LLM provider.

        Args:
            prompt: The user prompt to send to the LLM
            provider_id: Optional provider identifier, uses default if not specified
            context: Optional conversation context/history
            system_prompt: Optional system prompt/instructions
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens for the response
            model: Optional model name/identifier
            tools: Optional list of tools to provide to the LLM
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The response from the LLM
        """
        ...

    @abstractmethod
    def register_provider(self, provider_id: str, provider: LLMProvider) -> None:
        """Register an LLM provider.

        Args:
            provider_id: The identifier for the provider
            provider: The LLM provider implementation
        """
        ...

    @abstractmethod
    def get_provider(self, provider_id: Optional[str] = None) -> LLMProvider:
        """Get an LLM provider.

        Args:
            provider_id: The provider identifier, uses default if not specified

        Returns:
            LLMProvider: The requested LLM provider

        Raises:
            ValueError: If the provider is not found
        """
        ...

    @abstractmethod
    def set_default_provider(self, provider_id: str) -> None:
        """Set the default LLM provider.

        Args:
            provider_id: The provider identifier to set as default

        Raises:
            ValueError: If the provider is not found
        """
        ...


class DefaultLLMManager(LLMManager):
    """Default implementation of the LLM manager interface."""

    def __init__(self, default_provider_id: Optional[str] = None):
        """Initialize the default LLM manager.

        Args:
            default_provider_id: The default provider ID to use if not specified
        """
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider_id = default_provider_id

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[str] = None,
        tools: Optional[List[ModelFormattedDictTool]] = None,
        tool_choice: ToolChoiceOrDictType = "auto",
        temperature: Optional[float] = None,
        max_completion_tokens: int = 5068,
        response_format: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from an LLM provider.

        Args:
            prompt: The user prompt to send to the LLM
            provider_id: Optional provider identifier, uses default if not specified
            context: Optional conversation context/history
            system_prompt: Optional system prompt/instructions
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens for the response
            model: Optional model name/identifier
            tools: Optional list of tools to provide to the LLM
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The response from the LLM

        Raises:
            ValueError: If the provider is not found
        """
        provider = self.get_provider(provider_id)

        return await provider.generate(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            response_format=response_format,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def register_provider(self, provider_id: str, provider: LLMProvider) -> None:
        """Register an LLM provider.

        Args:
            provider_id: The identifier for the provider
            provider: The LLM provider implementation
        """
        self.providers[provider_id] = provider

        # Set as default if it's the first provider or none is set
        if self.default_provider_id is None:
            self.default_provider_id = provider_id

    def get_provider(self, provider_id: Optional[str] = None) -> LLMProvider:
        """Get an LLM provider.

        Args:
            provider_id: The provider identifier, uses default if not specified

        Returns:
            LLMProvider: The requested LLM provider

        Raises:
            ValueError: If the provider is not found
        """
        # Use default provider if none specified
        if provider_id is None:
            if self.default_provider_id is None:
                raise ValueError("No default provider is set")
            provider_id = self.default_provider_id

        # Get the provider
        if provider_id not in self.providers:
            raise ValueError(f"Provider '{provider_id}' not found")

        return self.providers[provider_id]

    def set_default_provider(self, provider_id: str) -> None:
        """Set the default LLM provider.

        Args:
            provider_id: The provider identifier to set as default

        Raises:
            ValueError: If the provider is not found
        """
        if provider_id not in self.providers:
            raise ValueError(f"Provider '{provider_id}' not found")

        self.default_provider_id = provider_id


# Helper function to create a tool call
def create_tool_call(name: str, arguments: Dict[str, Any]) -> ToolCall:
    """Create a standardized tool call object.

    Args:
        name: The name of the tool to call
        arguments: The arguments to pass to the tool

    Returns:
        A ToolCall object
    """
    return ToolCall(id=str(uuid.uuid4()), name=name, arguments=str(arguments))


# Import specific provider implementations
from llmgine.llm.providers.anthropic import AnthropicProvider
from llmgine.llm.providers.openai import OpenAIProvider
from llmgine.llm.providers.openrouter import OpenRouterProvider
from llmgine.llm.providers.providers import Providers

__all__ = [
    "AnthropicProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "Providers",
]
