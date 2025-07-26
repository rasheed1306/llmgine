"""OpenAI provider implementation."""

import uuid
from typing import Any, Dict, List, Literal, Optional

from anthropic import AsyncAnthropic
from openai.types.chat import ChatCompletion

from llmgine.bootstrap import ApplicationConfig
from llmgine.bus.bus import MessageBus
from llmgine.llm import ModelFormattedDictTool, ToolChoiceOrDictType
from llmgine.llm.providers import LLMProvider
from llmgine.llm.providers.events import LLMCallEvent, LLMResponseEvent
from llmgine.llm.providers.providers import Providers
from llmgine.llm.providers.response import LLMResponse, ResponseTokens
from llmgine.llm.tools.toolCall import ToolCall


class AnthropicResponse(LLMResponse):
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


class AnthropicProvider(LLMProvider):
    def __init__(
        self, api_key: str, model: str, model_component_id: Optional[str] = None
    ) -> None:
        self.model = model
        self.model_component_id = model_component_id or ""
        self.client = AsyncAnthropic(api_key=api_key)
        self.bus = MessageBus()

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
        thinking_enabled: bool = False,
        thinking_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        call_id = str(uuid.uuid4())

        # construct the payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_completion_tokens,
        }

        # System prompt extract
        if messages[0]["role"] == "system":
            payload["system"] = messages[0]["content"]
            payload["messages"] = messages[1:]

        if temperature:
            payload["temperature"] = temperature

        if tools:
            payload["tools"] = tools

            if tool_choice:
                payload["tool_choice"] = tool_choice

            if parallel_tool_calls is not None:
                payload["parallel_tool_calls"] = parallel_tool_calls

        if response_format:
            payload["response_format"] = response_format

        if thinking_enabled:
            payload["thinking"] = {
                "type": "enabled",
                "budget": thinking_budget,
            }

        payload.update(**kwargs)
        call_event = LLMCallEvent(
            call_id=call_id,
            model_id=self.model_component_id,
            provider=Providers.ANTHROPIC,
            payload=payload,
        )
        await self.bus.publish(call_event)
        try:
            response: ChatCompletion = await self.client.messages.create(**payload)  # type: ignore
            assert isinstance(response, ChatCompletion), (
                "Response is not a ChatCompletion"
            )
        except Exception as e:
            await self.bus.publish(
                LLMResponseEvent(
                    call_id=call_id,
                    error=e,
                )
            )
            raise e
        await self.bus.publish(
            LLMResponseEvent(
                call_id=call_id,
                raw_response=response,
            )
        )

        return AnthropicResponse(response)

    def stream(self) -> None:
        # TODO: Implement streaming
        raise NotImplementedError("Streaming is not supported for OpenAI")


async def main():
    import os

    import dotenv

    from llmgine.bootstrap import ApplicationBootstrap

    dotenv.load_dotenv(override=True)
    app = ApplicationBootstrap(ApplicationConfig(enable_console_handler=False))
    await app.bootstrap()
    provider = AnthropicProvider(
        api_key=os.getenv("ANTHROPIC_API_KEY") or "", model="claude-3-5-sonnet-20240620"
    )
    response = await provider.generate(
        messages=[
            {"role": "system", "content": "Respond in pirate language"},
            {"role": "user", "content": "Hello, how are you?"},
        ]
    )
    print(response.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
