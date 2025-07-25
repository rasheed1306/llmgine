"""OpenAI client for direct API access."""

import json
import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx


class OpenAIClient:
    """Direct client for OpenAI API with full feature access."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ):
        """Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
            base_url: Base URL for OpenAI API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self) -> "OpenAIClient":
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OpenAI API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def chat_completion(
        self,
        model: str,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a chat completion.
        
        Args:
            model: Model identifier
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters supported by OpenAI
            
        Returns:
            OpenAI API response
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        endpoint = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        
        response = await self._client.post(endpoint, json=data, headers=headers)
        
        if response.status_code != 200:
            error_text = response.text
            raise RuntimeError(
                f"OpenAI API error ({response.status_code}): {error_text}"
            )
        
        return response.json()
    
    async def chat_completion_stream(
        self,
        model: str,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming chat completion.
        
        Args:
            model: Model identifier
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters supported by OpenAI
            
        Yields:
            OpenAI API streaming chunks
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        endpoint = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        
        async with self._client.stream(
            "POST", endpoint, json=data, headers=headers
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(
                    f"OpenAI API error ({response.status_code}): {error_text.decode()}"
                )
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
