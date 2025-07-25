"""Unified LLM client implementation using provider modules."""

import os
from typing import Any, AsyncIterator, Optional

from llmgine.providers.anthropic import AnthropicAdapter, AnthropicClient
from llmgine.providers.gemini import GeminiAdapter, GeminiClient
from llmgine.providers.openai import OpenAIAdapter, OpenAIClient
from llmgine.providers.utils import detect_provider
from llmgine.unified.models import UnifiedRequest, UnifiedResponse, UnifiedStreamChunk


class UnifiedLLMClient:
    """Unified client for OpenAI, Anthropic, and Gemini APIs."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """Initialize the unified client.

        Args:
            openai_api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            anthropic_api_key: Anthropic API key (defaults to env var ANTHROPIC_API_KEY)
            gemini_api_key: Gemini API key (defaults to env var GEMINI_API_KEY)
            timeout: Request timeout in seconds
        """
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.timeout = timeout
        
        # Initialize providers and adapters
        self._openai_client: Optional[OpenAIClient] = None
        self._anthropic_client: Optional[AnthropicClient] = None
        self._gemini_client: Optional[GeminiClient] = None
        
        self._openai_adapter = OpenAIAdapter()
        self._anthropic_adapter = AnthropicAdapter()
        self._gemini_adapter = GeminiAdapter()

    async def __aenter__(self) -> "UnifiedLLMClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close all HTTP clients."""
        if self._openai_client:
            await self._openai_client.close()
        if self._anthropic_client:
            await self._anthropic_client.close()
        if self._gemini_client:
            await self._gemini_client.close()
    
    def _get_openai_client(self) -> OpenAIClient:
        """Get or create OpenAI client."""
        if not self._openai_client:
            self._openai_client = OpenAIClient(
                api_key=self.openai_api_key,
                timeout=self.timeout
            )
        return self._openai_client
    
    def _get_anthropic_client(self) -> AnthropicClient:
        """Get or create Anthropic client."""
        if not self._anthropic_client:
            self._anthropic_client = AnthropicClient(
                api_key=self.anthropic_api_key,
                timeout=self.timeout
            )
        return self._anthropic_client
    
    def _get_gemini_client(self) -> GeminiClient:
        """Get or create Gemini client."""
        if not self._gemini_client:
            self._gemini_client = GeminiClient(
                api_key=self.gemini_api_key,
                timeout=self.timeout
            )
        return self._gemini_client

    async def generate(self, request: UnifiedRequest) -> UnifiedResponse:
        """Generate a response from the LLM.

        Args:
            request: Unified request object

        Returns:
            Unified response object
        """
        # Detect provider
        provider = detect_provider(request.model)

        if provider == "openai":
            client = self._get_openai_client()
            adapter = self._openai_adapter
            
            # Convert to provider format
            openai_request = adapter.to_provider_request(request)
            
            # Make request
            response = await client.chat_completion(**openai_request)
            
            # Convert to unified format
            return adapter.from_provider_response(response)
            
        elif provider == "anthropic":
            client = self._get_anthropic_client()
            adapter = self._anthropic_adapter
            
            # Convert to provider format
            anthropic_request = adapter.to_provider_request(request)
            
            # Make request
            response = await client.messages(**anthropic_request)
            
            # Convert to unified format
            return adapter.from_provider_response(response)
            
        elif provider == "gemini":
            client = self._get_gemini_client()
            adapter = self._gemini_adapter
            
            # Convert to provider format
            gemini_request = adapter.to_provider_request(request)
            
            # Make request with model name
            response = await client.generate_content(
                model=request.model,
                **gemini_request
            )
            
            # Convert to unified format
            return adapter.from_provider_response(response)
            
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate_stream(
        self, request: UnifiedRequest
    ) -> AsyncIterator[UnifiedStreamChunk]:
        """Generate a streaming response from the LLM.

        Args:
            request: Unified request object (with stream=True)

        Yields:
            Unified stream chunks
        """
        if not request.stream:
            raise ValueError("Request must have stream=True for streaming")

        # Detect provider
        provider = detect_provider(request.model)

        if provider == "openai":
            client = self._get_openai_client()
            adapter = self._openai_adapter
            
            # Convert to provider format
            openai_request = adapter.to_provider_stream_request(request)
            
            # Make streaming request
            async for chunk in client.chat_completion_stream(**openai_request):
                unified_chunk = adapter.from_provider_stream_chunk(chunk)
                if unified_chunk.content or unified_chunk.finish_reason:
                    yield unified_chunk
                    
        elif provider == "anthropic":
            client = self._get_anthropic_client()
            adapter = self._anthropic_adapter
            
            # Convert to provider format
            anthropic_request = adapter.to_provider_stream_request(request)
            
            # Make streaming request
            async for chunk in client.messages_stream(**anthropic_request):
                unified_chunk = adapter.from_provider_stream_chunk(chunk)
                if unified_chunk.content or unified_chunk.finish_reason:
                    yield unified_chunk
                    
        elif provider == "gemini":
            client = self._get_gemini_client()
            adapter = self._gemini_adapter
            
            # Convert to provider format
            gemini_request = adapter.to_provider_stream_request(request)
            
            # Make streaming request with model name
            async for chunk in client.generate_content_stream(
                model=request.model,
                **gemini_request
            ):
                unified_chunk = adapter.from_provider_stream_chunk(chunk)
                if unified_chunk.content or unified_chunk.finish_reason:
                    yield unified_chunk
                    
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # Compatibility methods for backward compatibility
    def _get_api_key(self, provider: str) -> str:
        """Get API key for provider (for backward compatibility)."""
        if provider == "openai":
            if not self.openai_api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
                )
            return self.openai_api_key
        elif provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError(
                    "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
                )
            return self.anthropic_api_key
        elif provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError(
                    "Gemini API key not found. Set GEMINI_API_KEY environment variable."
                )
            return self.gemini_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")
