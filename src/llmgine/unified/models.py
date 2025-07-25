"""Base models for unified LLM interface."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """Unified content block for multimodal content."""

    type: Literal["text", "image", "file"] = Field(..., description="Type of content")
    text: Optional[str] = Field(None, description="Text content")
    image_url: Optional[str] = Field(None, description="URL to image")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    mime_type: Optional[str] = Field(None, description="MIME type for binary content")


class UnifiedMessage(BaseModel):
    """Unified message format across all providers."""

    role: Literal["system", "user", "assistant"] = Field(..., description="Message role")
    content: Union[str, List[ContentBlock]] = Field(..., description="Message content")


class UnifiedRequest(BaseModel):
    """Unified request format for all LLM providers."""

    model: str = Field(..., description="Model identifier")
    messages: List[UnifiedMessage] = Field(..., description="Conversation messages")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    system: Optional[str] = Field(None, description="System prompt (for Anthropic)")
    stream: bool = Field(False, description="Whether to stream the response")


class UnifiedResponse(BaseModel):
    """Unified response format from LLM providers."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    raw_response: Optional[Dict[str, Any]] = Field(
        None, description="Original provider response"
    )

    @classmethod
    def from_openai(cls, response: Dict[str, Any]) -> "UnifiedResponse":
        """Create UnifiedResponse from OpenAI response."""
        choice = response["choices"][0]
        return cls(
            content=choice["message"]["content"],
            model=response["model"],
            usage=response.get("usage"),
            finish_reason=choice.get("finish_reason"),
            raw_response=response,
        )

    @classmethod
    def from_anthropic(cls, response: Dict[str, Any]) -> "UnifiedResponse":
        """Create UnifiedResponse from Anthropic response."""
        content = response["content"][0]["text"] if response["content"] else ""
        return cls(
            content=content,
            model=response["model"],
            usage={
                "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    response.get("usage", {}).get("input_tokens", 0)
                    + response.get("usage", {}).get("output_tokens", 0)
                ),
            }
            if "usage" in response
            else None,
            finish_reason=response.get("stop_reason"),
            raw_response=response,
        )

    @classmethod
    def from_gemini(cls, response: Dict[str, Any]) -> "UnifiedResponse":
        """Create UnifiedResponse from Gemini response."""
        candidate = response.get("candidates", [{}])[0]
        content_parts = candidate.get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in content_parts)

        usage_metadata = response.get("usageMetadata", {})
        usage = (
            {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0),
            }
            if usage_metadata
            else None
        )

        return cls(
            content=content,
            model=response.get("modelVersion", "unknown"),
            usage=usage,
            finish_reason=candidate.get("finishReason"),
            raw_response=response,
        )


class UnifiedStreamChunk(BaseModel):
    """Unified streaming chunk for incremental responses."""

    content: str = Field(..., description="Incremental content")
    finish_reason: Optional[str] = Field(
        None, description="Reason for completion if finished"
    )
    raw_chunk: Optional[Dict[str, Any]] = Field(
        None, description="Original provider chunk"
    )
