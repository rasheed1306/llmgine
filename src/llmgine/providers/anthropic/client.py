"""Anthropic client for direct API access."""

import json
import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx


class AnthropicClient:
    """Direct client for Anthropic API with full feature access."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.anthropic.com/v1",
        timeout: float = 60.0,
    ):
        """Initialize the Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to env var ANTHROPIC_API_KEY)
            base_url: Base URL for Anthropic API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
            )
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "AnthropicClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Anthropic API requests."""
        if not self.api_key:
            raise ValueError("API key is required")
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def messages(
        self,
        model: str,
        messages: list,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        thinking: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a message completion.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters supported by Anthropic

        Returns:
            Anthropic API response
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }

        if system is not None:
            data["system"] = system

        if temperature is not None:
            data["temperature"] = temperature

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        if thinking is not None:
            data["thinking"] = thinking

        endpoint = f"{self.base_url}/messages"
        headers = self._get_headers()

        response = await self._client.post(endpoint, json=data, headers=headers)

        if response.status_code != 200:
            error_text = response.text
            raise RuntimeError(
                f"Anthropic API error ({response.status_code}): {error_text}"
            )

        result: Dict[str, Any] = response.json()
        return result

    async def messages_stream(
        self,
        model: str,
        messages: list,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Create a streaming message completion.

        Args:
            model: Model identifier
            messages: List of messages
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters supported by Anthropic

        Yields:
            Anthropic API streaming chunks
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }

        if system is not None:
            data["system"] = system

        if temperature is not None:
            data["temperature"] = temperature

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        if thinking is not None:
            data["thinking"] = thinking

        endpoint = f"{self.base_url}/messages"
        headers = self._get_headers()

        async with self._client.stream(
            "POST", endpoint, json=data, headers=headers
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(
                    f"Anthropic API error ({response.status_code}): {error_text.decode()}"
                )

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
