"""Provider response models for LLMgine.

This module provides a clean, modern response architecture that:
1. Supports provider-specific data with type safety
2. Handles both streaming and non-streaming responses
3. Provides zero-overhead for standard usage
4. Enables rich provider-specific features
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class Usage(BaseModel):
    """Token usage information with provider-specific extensions."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")

    # Allow provider-specific fields like reasoning_tokens, cache_tokens, etc.
    model_config = ConfigDict(extra="allow")


class ToolCall(BaseModel):
    """Represents a tool/function call in the response."""
    
    id: str = Field(..., description="Unique identifier for this tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: Dict[str, Any] = Field(..., description="Function name and arguments")


class ProviderMetadata(BaseModel):
    """Base class for provider-specific metadata."""
    
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model identifier used")
    
    # Allow arbitrary provider-specific fields
    model_config = ConfigDict(extra="allow")


class OpenAIMetadata(ProviderMetadata):
    """OpenAI-specific response metadata."""
    
    provider: str = Field(default="openai", frozen=True)
    id: Optional[str] = Field(None, description="Response ID")
    created: Optional[int] = Field(None, description="Timestamp")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")
    
    # For reasoning models (o1, etc.)
    reasoning_content: Optional[str] = Field(None, description="Chain of thought reasoning")


class AnthropicMetadata(ProviderMetadata):
    """Anthropic-specific response metadata."""
    
    provider: str = Field(default="anthropic", frozen=True)
    id: Optional[str] = Field(None, description="Message ID")
    type: Optional[str] = Field(None, description="Response type")
    stop_sequence: Optional[str] = Field(None, description="Stop sequence used")


class GeminiMetadata(ProviderMetadata):
    """Gemini-specific response metadata."""
    
    provider: str = Field(default="gemini", frozen=True)
    candidates_count: Optional[int] = Field(None, description="Number of candidates")
    prompt_feedback: Optional[Dict[str, Any]] = Field(None, description="Prompt feedback")
    safety_ratings: Optional[List[Dict[str, Any]]] = Field(None, description="Safety ratings")


# Type variable for provider metadata
TMetadata = TypeVar("TMetadata", bound=ProviderMetadata)


class ProviderResponse(BaseModel, Generic[TMetadata]):
    """Modern provider response with type-safe metadata."""
    
    content: str = Field(..., description="Generated content")
    usage: Optional[Usage] = Field(None, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool/function calls")
    
    # Provider-specific metadata
    metadata: TMetadata = Field(..., description="Provider-specific metadata")
    
    # Original response for debugging/advanced usage
    raw: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0
    
    @property
    def total_tokens(self) -> Optional[int]:
        """Get total token count if available."""
        return self.usage.total_tokens if self.usage else None


# Concrete provider response types
OpenAIResponse = ProviderResponse[OpenAIMetadata]
AnthropicResponse = ProviderResponse[AnthropicMetadata]
GeminiResponse = ProviderResponse[GeminiMetadata]


class StreamChunk(BaseModel):
    """Represents a single chunk in a streaming response."""
    
    delta: str = Field(default="", description="Incremental content")
    finish_reason: Optional[str] = Field(None, description="Finish reason if this is the last chunk")
    
    # For accumulating metadata during streaming
    usage: Optional[Usage] = Field(None, description="Final usage (in last chunk)")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls (accumulated)")
    
    # Provider-specific data
    metadata: Optional[Dict[str, Any]] = Field(None, description="Provider-specific chunk metadata")
    
    @property
    def is_final(self) -> bool:
        """Check if this is the final chunk."""
        return self.finish_reason is not None


class StreamingResponse(BaseModel, Generic[TMetadata]):
    """Container for accumulating streaming response data."""
    
    chunks: List[StreamChunk] = Field(default_factory=list, description="All chunks received")
    content: str = Field(default="", description="Accumulated content")
    usage: Optional[Usage] = Field(None, description="Final usage statistics")
    finish_reason: Optional[str] = Field(None, description="Final finish reason")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Accumulated tool calls")
    metadata: Optional[TMetadata] = Field(None, description="Provider metadata")
    
    def add_chunk(self, chunk: StreamChunk) -> None:
        """Add a chunk and update accumulated data."""
        self.chunks.append(chunk)
        self.content += chunk.delta
        
        if chunk.usage:
            self.usage = chunk.usage
        
        if chunk.finish_reason:
            self.finish_reason = chunk.finish_reason
        
        if chunk.tool_calls:
            self.tool_calls = chunk.tool_calls
    
    def to_response(self) -> ProviderResponse[TMetadata]:
        """Convert accumulated streaming data to final response."""
        if not self.metadata:
            raise ValueError("Metadata must be set before converting to response")
        
        return ProviderResponse(
            content=self.content,
            usage=self.usage,
            finish_reason=self.finish_reason,
            tool_calls=self.tool_calls,
            metadata=self.metadata,
            raw=None,
        )


# Response factory functions
def create_openai_response(
    content: str,
    model: str,
    raw_response: Dict[str, Any],
    usage: Optional[Dict[str, Any]] = None,
    finish_reason: Optional[str] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
) -> OpenAIResponse:
    """Create OpenAI response from raw API data."""
    metadata = OpenAIMetadata(
        model=model,
        id=raw_response.get("id"),
        created=raw_response.get("created"),
        system_fingerprint=raw_response.get("system_fingerprint"),
        reasoning_content=None,
    )
    
    # Extract reasoning content if present
    if raw_response.get("choices"):
        message = raw_response["choices"][0].get("message", {})
        if "reasoning_content" in message:
            metadata.reasoning_content = message["reasoning_content"]
    
    # Parse usage
    usage_obj = None
    if usage:
        usage_obj = Usage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        # Add reasoning tokens if present
        if "reasoning_tokens" in usage:
            usage_obj.reasoning_tokens = usage["reasoning_tokens"]
    
    # Parse tool calls
    tool_call_objs = None
    if tool_calls:
        tool_call_objs = [
            ToolCall(
                id=tc["id"],
                type=tc.get("type", "function"),
                function={
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                },
            )
            for tc in tool_calls
        ]
    
    return OpenAIResponse(
        content=content,
        usage=usage_obj,
        finish_reason=finish_reason,
        tool_calls=tool_call_objs,
        metadata=metadata,
        raw=raw_response,
    )


def create_anthropic_response(
    content: str,
    model: str,
    raw_response: Dict[str, Any],
    usage: Optional[Dict[str, Any]] = None,
    finish_reason: Optional[str] = None,
) -> AnthropicResponse:
    """Create Anthropic response from raw API data."""
    metadata = AnthropicMetadata(
        model=model,
        id=raw_response.get("id"),
        type=raw_response.get("type"),
        stop_sequence=raw_response.get("stop_sequence"),
    )
    
    # Parse usage - Anthropic uses different field names
    usage_obj = None
    if usage:
        usage_obj = Usage(
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=(
                usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            ),
        )
        # Add cache tokens if present
        for field in ["cache_creation_input_tokens", "cache_read_input_tokens"]:
            if field in usage:
                setattr(usage_obj, field, usage[field])
    
    return AnthropicResponse(
        content=content,
        usage=usage_obj,
        finish_reason=finish_reason,
        tool_calls=None,
        metadata=metadata,
        raw=raw_response,
    )


def create_gemini_response(
    content: str,
    model: str,
    raw_response: Dict[str, Any],
    usage: Optional[Dict[str, Any]] = None,
    finish_reason: Optional[str] = None,
) -> GeminiResponse:
    """Create Gemini response from raw API data."""
    metadata = GeminiMetadata(
        model=model,
        candidates_count=len(raw_response.get("candidates", [])),
        prompt_feedback=raw_response.get("promptFeedback"),
        safety_ratings=None,
    )
    
    # Extract safety ratings if present
    if raw_response.get("candidates"):
        candidate = raw_response["candidates"][0]
        if "safetyRatings" in candidate:
            metadata.safety_ratings = candidate["safetyRatings"]
    
    # Parse usage - Gemini uses usageMetadata
    usage_obj = None
    if usage:
        usage_obj = Usage(
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
        )
    
    return GeminiResponse(
        content=content,
        usage=usage_obj,
        finish_reason=finish_reason,
        tool_calls=None,
        metadata=metadata,
        raw=raw_response,
    )
