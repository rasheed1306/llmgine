"""Gemini client for direct API access."""

import json
import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx


class GeminiClient:
    """Direct client for Gemini API with full feature access."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: float = 60.0,
    ):
        """Initialize the Gemini client.

        Args:
            api_key: Gemini API key (defaults to env var GEMINI_API_KEY)
            base_url: Base URL for Gemini API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable."
            )
        self.base_url = base_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "GeminiClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Gemini API requests."""
        return {
            "Content-Type": "application/json",
        }

    async def generate_content(
        self,
        model: str,
        contents: list,
        system_instruction: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[list] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate content using Gemini.

        Args:
            model: Model identifier
            contents: List of content objects with role and parts
            system_instruction: System instruction with parts
            generation_config: Generation configuration
            safety_settings: Safety settings
            stream: Whether to stream the response
            **kwargs: Additional parameters supported by Gemini

        Returns:
            Gemini API response
        """
        data = {
            "contents": contents,
            **kwargs,
        }

        if system_instruction is not None:
            data["systemInstruction"] = system_instruction

        if generation_config is not None:
            data["generationConfig"] = generation_config

        if safety_settings is not None:
            data["safetySettings"] = safety_settings

        endpoint = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        if stream:
            endpoint = (
                f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}"
            )

        headers = self._get_headers()

        response = await self._client.post(endpoint, json=data, headers=headers)

        if response.status_code != 200:
            error_text = response.text
            raise RuntimeError(f"Gemini API error ({response.status_code}): {error_text}")

        return response.json()

    async def generate_content_stream(
        self,
        model: str,
        contents: list,
        system_instruction: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        safety_settings: Optional[list] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate streaming content using Gemini.

        Args:
            model: Model identifier
            contents: List of content objects with role and parts
            system_instruction: System instruction with parts
            generation_config: Generation configuration
            safety_settings: Safety settings
            **kwargs: Additional parameters supported by Gemini

        Yields:
            Gemini API streaming chunks
        """
        data = {
            "contents": contents,
            **kwargs,
        }

        if system_instruction is not None:
            data["systemInstruction"] = system_instruction

        if generation_config is not None:
            data["generationConfig"] = generation_config

        if safety_settings is not None:
            data["safetySettings"] = safety_settings

        endpoint = (
            f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}"
        )
        headers = self._get_headers()

        async with self._client.stream(
            "POST", endpoint, json=data, headers=headers
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(
                    f"Gemini API error ({response.status_code}): {error_text.decode()}"
                )

            async for line in response.aiter_lines():
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
