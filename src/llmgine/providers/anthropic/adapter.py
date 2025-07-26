"""Anthropic adapter for unified LLM interface."""

from typing import Any, Dict, List, Union

from llmgine.providers.base import ProviderAdapter
from llmgine.unified.models import (
    ContentBlock,
    UnifiedRequest,
    UnifiedResponse,
    UnifiedStreamChunk,
)


class AnthropicAdapter(ProviderAdapter):
    """Adapter for converting between unified and Anthropic formats."""

    def _convert_content_to_anthropic(
        self, content: Union[str, List[ContentBlock]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """Convert unified content to Anthropic format."""
        if isinstance(content, str):
            return content

        anthropic_content: List[Dict[str, Any]] = []
        for block in content:
            if block.type == "text":
                anthropic_content.append({"type": "text", "text": block.text})
            elif block.type == "image":
                if block.image_base64:
                    anthropic_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": block.mime_type or "image/jpeg",
                            "data": block.image_base64,
                        },
                    })
                elif block.image_url:
                    # Anthropic doesn't support URLs directly, would need to download
                    raise ValueError(
                        "Anthropic requires base64 encoded images, not URLs. "
                        "Please convert image URLs to base64 before sending."
                    )

        return anthropic_content

    def to_provider_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert UnifiedRequest to Anthropic API format."""
        anthropic_request = {
            "model": unified.model,
            "messages": [],
            "stream": unified.stream,
        }

        if unified.temperature is not None:
            anthropic_request["temperature"] = unified.temperature

        if unified.max_tokens is not None:
            anthropic_request["max_tokens"] = unified.max_tokens

        # Handle system prompt separately
        system_messages: List[str] = []
        for message in unified.messages:
            if message.role == "system":
                content_str = (
                    message.content
                    if isinstance(message.content, str)
                    else (message.content[0].text if message.content else "")
                )
                if content_str:
                    system_messages.append(content_str)
            else:
                anthropic_message = {
                    "role": message.role,
                    "content": self._convert_content_to_anthropic(message.content),
                }
                anthropic_request["messages"].append(anthropic_message)  # type: ignore[attr-defined]

        # Add system prompt if any
        if system_messages:
            anthropic_request["system"] = "\n".join(system_messages)
        elif unified.system:
            anthropic_request["system"] = unified.system

        return anthropic_request

    def from_provider_response(self, response: Dict[str, Any]) -> UnifiedResponse:
        """Convert Anthropic response to unified format."""
        return UnifiedResponse.from_anthropic(response)

    def to_provider_stream_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert unified request to Anthropic streaming format."""
        request = self.to_provider_request(unified)
        request["stream"] = True
        return request

    def from_provider_stream_chunk(self, chunk: Dict[str, Any]) -> UnifiedStreamChunk:
        """Convert Anthropic streaming chunk to unified format."""
        chunk_type = chunk.get("type", "")

        if chunk_type == "content_block_delta":
            # Extract text from delta
            delta = chunk.get("delta", {})
            content = delta.get("text", "") if delta.get("type") == "text_delta" else ""
            return UnifiedStreamChunk(
                content=content,
                finish_reason=None,
                raw_chunk=chunk,
            )
        elif chunk_type == "message_delta":
            # Check for stop reason in delta
            delta = chunk.get("delta", {})
            finish_reason = delta.get("stop_reason")
            return UnifiedStreamChunk(
                content="",
                finish_reason=finish_reason,
                raw_chunk=chunk,
            )
        elif chunk_type == "message_stop":
            return UnifiedStreamChunk(
                content="",
                finish_reason="stop",
                raw_chunk=chunk,
            )
        else:
            # Other chunk types (message_start, content_block_start, etc.)
            return UnifiedStreamChunk(
                content="",
                finish_reason=None,
                raw_chunk=chunk,
            )
