"""Provider implementations and response models.

This package contains:
- Modern response models with provider-specific metadata
- Type-safe provider response implementations
- Streaming response support
- Provider implementations (OpenAI, Anthropic, Gemini)
"""

from llmgine.providers.base import ProviderAdapter
from llmgine.providers.response import (
    AnthropicMetadata,
    AnthropicResponse,
    GeminiMetadata,
    GeminiResponse,
    OpenAIMetadata,
    OpenAIResponse,
    ProviderMetadata,
    ProviderResponse,
    StreamChunk,
    StreamingResponse,
    ToolCall,
    Usage,
    create_anthropic_response,
    create_gemini_response,
    create_openai_response,
)

__all__ = [
    # Base classes
    "ProviderAdapter",
    "ProviderMetadata",
    "ProviderResponse",
    # Response types
    "AnthropicMetadata",
    "AnthropicResponse",
    "GeminiMetadata",
    "GeminiResponse",
    "OpenAIMetadata",
    "OpenAIResponse",
    # Common models
    "StreamChunk",
    "StreamingResponse",
    "ToolCall",
    "Usage",
    # Factory functions
    "create_anthropic_response",
    "create_gemini_response",
    "create_openai_response",
]
