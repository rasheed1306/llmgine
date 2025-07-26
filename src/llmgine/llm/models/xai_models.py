import os
import uuid
from typing import Any, Dict, List, Optional

from llmgine.llm import ToolChoiceOrDictType
from llmgine.llm.providers import Providers
from llmgine.llm.providers.openrouter import OpenRouterProvider
from llmgine.llm.providers.response import LLMResponse


class Grok3Mini:
    def __init__(self, provider: Providers) -> None:
        self.id: str = str(uuid.uuid4())
        self.generate: Optional[Any] = None
        self._setProvider(provider)

    def _setProvider(self, provider: Providers) -> None:
        """Get the provider and set the generate method."""
        if provider == Providers.OPENROUTER:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.model = "x-ai/grok-3-mini-beta"
            self.provider = OpenRouterProvider(self.api_key, self.model)
            self.generate = self._generate_from_openrouter
        else:
            raise ValueError(
                f"Provider {provider} not supported for {self.__class__.__name__}"
            )

    def _generate_from_openrouter(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        tool_choice: ToolChoiceOrDictType = "auto",
        temperature: float = 0.7,
        max_completion_tokens: int = 5068,
    ) -> LLMResponse:
        return self.provider.generate(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
        )
