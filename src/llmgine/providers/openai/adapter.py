"""OpenAI adapter for unified LLM interface."""

from typing import Any, Dict, List, Union

from llmgine.providers.base import ProviderAdapter
from llmgine.unified.models import (
    ContentBlock,
    UnifiedRequest,
    UnifiedResponse,
    UnifiedStreamChunk,
)


class OpenAIAdapter(ProviderAdapter):
    """Adapter for converting between unified and OpenAI formats."""

    def _convert_content_to_openai(
        self, content: Union[str, List[ContentBlock]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """Convert unified content to OpenAI format."""
        if isinstance(content, str):
            return content

        openai_content: List[Dict[str, Any]] = []
        for block in content:
            if block.type == "text":
                openai_content.append({"type": "text", "text": block.text})
            elif block.type == "image":
                if block.image_url:
                    openai_content.append({
                        "type": "image_url",
                        "image_url": {"url": block.image_url},
                    })
                elif block.image_base64:
                    url = f"data:{block.mime_type or 'image/jpeg'};base64,{block.image_base64}"
                    openai_content.append({
                        "type": "image_url",
                        "image_url": {"url": url},
                    })

        return openai_content

    def to_provider_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert UnifiedRequest to OpenAI API format."""
        openai_request = {
            "model": unified.model,
            "messages": [],
            "stream": unified.stream,
        }

        if unified.temperature is not None:
            openai_request["temperature"] = unified.temperature

        if unified.max_tokens is not None:
            # Handle o4-mini models that use max_completion_tokens instead of max_tokens
            if "o4-mini" in unified.model:
                openai_request["max_completion_tokens"] = unified.max_tokens
            else:
                openai_request["max_tokens"] = unified.max_tokens

        for message in unified.messages:
            openai_message = {
                "role": message.role,
                "content": self._convert_content_to_openai(message.content),
            }
            openai_request["messages"].append(openai_message)

        return openai_request

    def from_provider_response(self, response: Dict[str, Any]) -> UnifiedResponse:
        """Convert OpenAI response to unified format."""
        return UnifiedResponse.from_openai(response)

    def to_provider_stream_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert unified request to OpenAI streaming format."""
        request = self.to_provider_request(unified)
        request["stream"] = True
        return request

    def from_provider_stream_chunk(self, chunk: Dict[str, Any]) -> UnifiedStreamChunk:
        """Convert OpenAI streaming chunk to unified format.
        
        Handles:
        - Content chunks
        - Tool call chunks
        - Final chunks with usage
        """
        choices = chunk.get("choices", [])
        if not choices:
            return UnifiedStreamChunk(
                content="",
                finish_reason=None,
                raw_chunk=chunk,
            )
            
        choice = choices[0]
        delta = choice.get("delta", {})
        
        # Extract content from delta
        content = delta.get("content", "")
        
        # Handle tool calls in streaming
        if "tool_calls" in delta and not content:
            # Format tool call delta as content
            tool_parts = []
            for tc in delta.get("tool_calls", []):
                if "function" in tc:
                    func = tc["function"]
                    if "name" in func:
                        tool_parts.append(f"[Tool: {func['name']}]")
                    if "arguments" in func:
                        tool_parts.append(func["arguments"])
            content = "".join(tool_parts)

        return UnifiedStreamChunk(
            content=content,
            finish_reason=choice.get("finish_reason"),
            raw_chunk=chunk,
        )
