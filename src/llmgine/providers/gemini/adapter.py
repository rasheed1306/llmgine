"""Gemini adapter for unified LLM interface."""

import json
from typing import Any, Dict, List, Union

from llmgine.providers.base import ProviderAdapter
from llmgine.unified.models import (
    ContentBlock,
    UnifiedRequest,
    UnifiedResponse,
    UnifiedStreamChunk,
)


class GeminiAdapter(ProviderAdapter):
    """Adapter for converting between unified and Gemini formats."""

    def _convert_content_to_gemini_parts(
        self, content: Union[str, List[ContentBlock]]
    ) -> List[Dict[str, Any]]:
        """Convert unified content to Gemini parts format."""
        if isinstance(content, str):
            return [{"text": content}]

        parts = []
        for block in content:
            if block.type == "text":
                parts.append({"text": block.text})
            elif block.type == "image":
                if block.image_base64:
                    parts.append({
                        "inline_data": {
                            "mime_type": block.mime_type or "image/jpeg",
                            "data": block.image_base64,
                        }
                    })
                elif block.image_url:
                    # For Gemini, we need to handle different URL types
                    # GCS URLs are supported directly, others need to be downloaded
                    if block.image_url.startswith("gs://"):
                        parts.append({"file_data": {"file_uri": block.image_url}})
                    else:
                        # Would need to download and convert to base64
                        raise ValueError(
                            "Gemini only supports Google Cloud Storage URLs (gs://) directly. "
                            "Please convert other URLs to base64 before sending."
                        )

        return parts

    def to_provider_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert UnifiedRequest to Gemini API format."""
        gemini_request: Dict[str, Any] = {
            "contents": [],
            "generationConfig": {},
        }

        if unified.temperature is not None:
            gemini_request["generationConfig"]["temperature"] = unified.temperature

        if unified.max_tokens is not None:
            gemini_request["generationConfig"]["maxOutputTokens"] = unified.max_tokens

        # Handle system instructions
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
                # Map role names
                role = "model" if message.role == "assistant" else message.role
                gemini_content = {
                    "role": role,
                    "parts": self._convert_content_to_gemini_parts(message.content),
                }
                gemini_request["contents"].append(gemini_content)

        # Add system instruction if any
        if system_messages:
            gemini_request["systemInstruction"] = {
                "parts": [{"text": "\n".join(system_messages)}]
            }
        elif unified.system:
            gemini_request["systemInstruction"] = {"parts": [{"text": unified.system}]}

        return gemini_request

    def from_provider_response(self, response: Dict[str, Any]) -> UnifiedResponse:
        """Convert Gemini response to unified format."""
        return UnifiedResponse.from_gemini(response)

    def to_provider_stream_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert unified request to Gemini streaming format."""
        # Gemini uses the same format for streaming
        return self.to_provider_request(unified)

    def from_provider_stream_chunk(self, chunk: Dict[str, Any]) -> UnifiedStreamChunk:
        """Convert Gemini streaming chunk to unified format."""
        try:
            # Parse JSON from the line
            chunk_data = json.loads(chunk) if isinstance(chunk, str) else chunk

            candidate = chunk_data.get("candidates", [{}])[0]
            content_parts = candidate.get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in content_parts)
            finish_reason = candidate.get("finishReason")

            return UnifiedStreamChunk(
                content=content,
                finish_reason=finish_reason,
                raw_chunk=chunk_data,
            )
        except Exception:
            return UnifiedStreamChunk(
                content="",
                finish_reason=None,
                raw_chunk=chunk,
            )
