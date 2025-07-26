import uuid
from typing import Any, Dict, List, Literal, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from llmgine.bus.bus import MessageBus
from llmgine.llm import ModelFormattedDictTool, SessionID, ToolChoiceOrDictType
from llmgine.llm.providers import LLMProvider
from llmgine.llm.providers.events import LLMCallEvent, LLMResponseEvent
from llmgine.llm.providers.providers import Providers
from llmgine.llm.providers.response import LLMResponse, ResponseTokens
from llmgine.llm.tools.toolCall import ToolCall

OpenRouterProviders = Literal[
    "OpenAI",
    "Anthropic",
    "Google",
    "Google AI Studio",
    "Amazon Bedrock",
    "Groq",
    "SambaNova",
    "Cohere",
    "Mistral",
    "Together",
    "Together 2",
    "Fireworks",
    "DeepInfra",
    "Lepton",
    "Novita",
    "Avian",
    "Lambda",
    "Azure",
    "Modal",
    "AnyScale",
    "Replicate",
    "Perplexity",
    "Recursal",
    "OctoAI",
    "DeepSeek",
    "Infermatic",
    "AI21",
    "Featherless",
    "Inflection",
    "xAI",
    "Cloudflare",
    "SF Compute",
    "Minimax",
    "Nineteen",
    "Liquid",
    "Stealth",
    "NCompass",
    "InferenceNet",
    "Friendli",
    "AionLabs",
    "Alibaba",
    "Nebius",
    "Chutes",
    "Kluster",
    "Crusoe",
    "Targon",
    "Ubicloud",
    "Parasail",
    "Phala",
    "Cent-ML",
    "Venice",
    "OpenInference",
    "Atoma",
    "01.AI",
    "HuggingFace",
    "Mancer",
    "Mancer 2",
    "Hyperbolic",
    "Hyperbolic 2",
    "Lynn 2",
    "Lynn",
    "Reflection",
]


class OpenRouterResponse(LLMResponse):
    def __init__(self, response: ChatCompletion) -> None:
        self.response = response

    @property
    def raw(self) -> ChatCompletion:
        return self.response

    @property
    def content(self) -> str:
        # TODO: Implement content
        return ""

    @property
    def tool_calls(self) -> List[ToolCall]:
        if not self.response.choices[0].message.tool_calls:
            return []
        return [
            ToolCall(tool_call.id, tool_call.function.name, tool_call.function.arguments)
            for tool_call in self.response.choices[0].message.tool_calls
        ]

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def finish_reason(self) -> str:
        return self.response.choices[0].finish_reason

    @property
    def tokens(self) -> ResponseTokens:
        # TODO: Implement tokens
        return ResponseTokens()

    @property
    def reasoning(self) -> str:
        # TODO: Implement reasoning
        return ""


class OpenRouterProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        provider: Optional[OpenRouterProviders] = None,
        model_component_id: Optional[str] = None,
    ) -> None:
        self.model = model
        self.model_component_id = model_component_id or ""
        self.provider = provider
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
        self.bus = MessageBus()

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ModelFormattedDictTool]] = None,
        tool_choice: ToolChoiceOrDictType = "auto",
        parallel_tool_calls: Optional[bool] = None,
        temperature: Optional[float] = 0.7,
        max_completion_tokens: int = 5068,
        response_format: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        reasoning: bool = False,
        reasoning_max_tokens: Optional[int] = None,
        reasoning_include_reasoning: Optional[bool] = False,
        retry_count: int = 5,
        **kwargs: Any,
    ) -> LLMResponse:
        call_id = str(uuid.uuid4())

        # Default payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
        }

        # Provider specific
        if self.provider:
            payload["extra_body"] = {
                "provider": {
                    "order": [self.provider],
                    "allow_fallbacks": False,
                    "data_collection": "deny",
                }
            }

        # Temperature
        if temperature:
            payload["temperature"] = temperature

        # Tools
        if tools:
            payload["tools"] = tools

            if tool_choice:
                payload["tool_choice"] = tool_choice

        # Response format
        if response_format:
            payload["response_format"] = response_format

        # Reasoning
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort

        # Reasoning
        if reasoning:
            payload["extra_body"]["reasoning"] = {}
            if reasoning_max_tokens:
                payload["extra_body"]["reasoning"]["max_tokens"] = reasoning_max_tokens
            if reasoning_effort:
                payload["extra_body"]["reasoning"]["effort"] = reasoning_effort
            if not reasoning_include_reasoning:
                payload["extra_body"]["reasoning"]["exclude"] = True

        # Update payload with additional kwargs
        payload.update(**kwargs)  # type: ignore

        # Call event
        call_event = LLMCallEvent(
            call_id=call_id,
            model_id=self.model_component_id,
            provider=Providers.OPENROUTER,
            payload=payload,
        )
        await self.bus.publish(call_event)
        for _ in range(retry_count):
            try:
                response: ChatCompletion = await self.client.chat.completions.create(
                    **payload
                )  # type: ignore
                assert isinstance(response, ChatCompletion), (
                    "Response is not a ChatCompletion"
                )
                await self.bus.publish(
                    LLMResponseEvent(
                        call_id=call_id,
                        raw_response=response,
                    )
                )
                break
            except Exception as e:
                await self.bus.publish(
                    LLMResponseEvent(
                        call_id=call_id,
                        error=e,
                    )
                )
        # Return wrapped response
        return OpenRouterResponse(response)

    def stream(self) -> None:
        # TODO: Implement streaming
        raise NotImplementedError("Streaming is not supported for OpenRouter")


async def main():
    import os

    from llmgine.bootstrap import ApplicationBootstrap, ApplicationConfig
    from llmgine.llm.tools import ToolManager

    def get_weather(city: str) -> str:
        """
        Get the weather in a city.

        Args:
            city: The city to get the weather for.

        Returns:
            str: The weather in the city.
        """
        return f"The weather in {city} is sunny with a chance to rain meatballs."

    app = ApplicationBootstrap(ApplicationConfig(enable_console_handler=False))
    await app.bootstrap()
    tool_manager = ToolManager(session_id=SessionID("test"), engine_id="test")
    await tool_manager.register_tool(get_weather)
    provider = OpenRouterProvider(
        api_key=os.getenv("OPENROUTER_API_KEY") or "",
        model="deepseek/deepseek-chat-v3-0324",
        provider="Fireworks",
    )
    tools = await tool_manager.get_tools()
    response = await provider.generate(
        messages=[{"role": "user", "content": "Whats the weather in Tokyo?"}],
        tools=tools,
    )
    print(response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
