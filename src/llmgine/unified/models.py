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
        """Create UnifiedResponse from OpenAI response.
        
        Handles various response types including:
        - Standard text responses
        - Tool calling responses
        - Responses with logprobs
        - Error responses
        """
        # Handle error responses
        if "error" in response:
            error_msg = response["error"].get("message", "Unknown error")
            return cls(
                content=f"Error: {error_msg}",
                model=response.get("model", "unknown"),
                usage=None,
                finish_reason="error",
                raw_response=response,
            )
        
        # Handle standard responses
        choice = response["choices"][0]
        message = choice.get("message", {})
        
        # Extract content - can be null for tool calls
        content = message.get("content")
        
        # Check for tool calls
        tool_calls = message.get("tool_calls")
        if tool_calls and content is None:
            # Format tool calls as content for unified response
            tool_info = []
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_info.append(
                    f"Tool call: {func.get('name')}({func.get('arguments')})"
                )
            content = "\n".join(tool_info)
        
        # Handle usage information with all nested fields
        usage = response.get("usage")
        if usage:
            # Preserve all usage fields including nested ones
            usage = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                # Preserve model-specific fields
                "prompt_tokens_details": usage.get("prompt_tokens_details"),
                "completion_tokens_details": usage.get("completion_tokens_details"),
            }
        
        return cls(
            content=content or "",
            model=response["model"],
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            raw_response=response,
        )

    @classmethod
    def from_anthropic(cls, response: Dict[str, Any]) -> "UnifiedResponse":
        """Create UnifiedResponse from Anthropic response.
        
        Handles various response types including:
        - Standard text responses
        - Tool calling responses with multiple content blocks
        - Error responses
        - Stop sequences
        """
        # Handle error responses
        if response.get("type") == "error" or "error" in response:
            error_info = response.get("error", {})
            error_msg = error_info.get("message", "Unknown error")
            return cls(
                content=f"Error: {error_msg}",
                model=response.get("model", "unknown"),
                usage=None,
                finish_reason="error",
                raw_response=response,
            )
        
        # Extract content from content blocks
        content_parts = []
        tool_calls = []
        thinking_parts = []
        
        for block in response.get("content", []):
            if block["type"] == "text":
                content_parts.append(block["text"])
            elif block["type"] == "tool_use":
                # Format tool use for unified response
                tool_info = f"Tool call: {block['name']}({block.get('input', {})})"
                tool_calls.append(tool_info)
            elif block["type"] == "thinking":
                # Include thinking content for Claude 4 models
                thinking_parts.append(block.get("thinking", ""))
        
        # Combine all content parts
        # Note: thinking content is typically not shown to end users
        # but we include it here for completeness
        content = "\n".join(content_parts)
        if thinking_parts:
            # Optionally include thinking with a marker
            content = "[THINKING]\n" + "\n".join(thinking_parts) + "\n[/THINKING]\n" + content
        if tool_calls:
            if content:
                content += "\n"
            content += "\n".join(tool_calls)
        
        # Extract usage information
        usage = None
        if "usage" in response:
            usage_data = response["usage"]
            usage = {
                "prompt_tokens": usage_data.get("input_tokens", 0),
                "completion_tokens": usage_data.get("output_tokens", 0),
                "total_tokens": (
                    usage_data.get("input_tokens", 0)
                    + usage_data.get("output_tokens", 0)
                ),
                # Preserve Anthropic-specific fields
                "cache_creation_input_tokens": usage_data.get("cache_creation_input_tokens"),
                "cache_read_input_tokens": usage_data.get("cache_read_input_tokens"),
                "service_tier": usage_data.get("service_tier"),
            }
        
        return cls(
            content=content,
            model=response.get("model", "unknown"),
            usage=usage,
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
