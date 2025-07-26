"""Live API tests for provider response models.

These tests actually call the provider APIs and test response parsing.
They require valid API keys to be set in environment variables.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import pytest

from llmgine.providers.response import (
    AnthropicResponse,
    GeminiResponse,
    OpenAIResponse,
    create_anthropic_response,
    create_gemini_response,
    create_openai_response,
)

# Directory to store API responses
RESPONSES_DIR = Path(__file__).parent / "stored_responses"
RESPONSES_DIR.mkdir(exist_ok=True)


class APIClient:
    """Simple HTTP client for making API calls."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def post(self, url: str, headers: Dict[str, str], json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request and return JSON response."""
        response = await self.client.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()


async def call_openai_api(api_key: str, store: bool = True) -> Dict[str, Any]:
    """Call OpenAI API and optionally store the response."""
    client = APIClient()
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json_data={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Say 'Hello from OpenAI' and nothing else."}
                ],
                "max_tokens": 20,
                "temperature": 0,
            }
        )
        
        if store:
            with open(RESPONSES_DIR / "openai_basic.json", "w") as f:
                json.dump(response, f, indent=2)
        
        return response
    finally:
        await client.close()


async def call_openai_with_tools(api_key: str, store: bool = True) -> Dict[str, Any]:
    """Call OpenAI API with function calling."""
    client = APIClient()
    try:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json_data={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "What's the weather in San Francisco?"}
                ],
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather in a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "City name"},
                            },
                            "required": ["location"],
                        },
                    },
                }],
                "tool_choice": "auto",
                "temperature": 0,
            }
        )
        
        if store:
            with open(RESPONSES_DIR / "openai_tools.json", "w") as f:
                json.dump(response, f, indent=2)
        
        return response
    finally:
        await client.close()


async def call_anthropic_api(api_key: str, store: bool = True) -> Dict[str, Any]:
    """Call Anthropic API and optionally store the response."""
    client = APIClient()
    try:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json_data={
                "model": "claude-3-haiku-20240307",
                "messages": [
                    {"role": "user", "content": "Say 'Hello from Anthropic' and nothing else."}
                ],
                "max_tokens": 20,
                "temperature": 0,
            }
        )
        
        if store:
            with open(RESPONSES_DIR / "anthropic_basic.json", "w") as f:
                json.dump(response, f, indent=2)
        
        return response
    finally:
        await client.close()


async def call_gemini_api(api_key: str, store: bool = True) -> Dict[str, Any]:
    """Call Gemini API and optionally store the response."""
    client = APIClient()
    try:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json_data={
                "contents": [{
                    "parts": [{
                        "text": "Say 'Hello from Gemini' and nothing else."
                    }]
                }],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 20,
                }
            }
        )
        
        if store:
            with open(RESPONSES_DIR / "gemini_basic.json", "w") as f:
                json.dump(response, f, indent=2)
        
        return response
    finally:
        await client.close()


def load_stored_response(filename: str) -> Optional[Dict[str, Any]]:
    """Load a stored response from file."""
    filepath = RESPONSES_DIR / filename
    if filepath.exists():
        with open(filepath, "r") as f:
            return json.load(f)
    return None


class TestOpenAIResponses:
    """Test OpenAI response parsing with real API data."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    async def test_openai_basic_response(self):
        """Test parsing basic OpenAI response."""
        # Try to load stored response first
        response_data = load_stored_response("openai_basic.json")
        
        if not response_data:
            # Call API if no stored response
            api_key = os.getenv("OPENAI_API_KEY")
            response_data = await call_openai_api(api_key)
        
        # Extract data from response
        choice = response_data["choices"][0]
        content = choice["message"]["content"]
        
        # Create response object
        response = create_openai_response(
            content=content,
            model=response_data["model"],
            raw_response=response_data,
            usage=response_data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )
        
        # Verify response
        assert isinstance(response, OpenAIResponse)
        assert response.content == content
        assert response.metadata.model == response_data["model"]
        assert response.metadata.id == response_data["id"]
        assert response.metadata.created == response_data["created"]
        assert response.metadata.system_fingerprint == response_data.get("system_fingerprint")
        
        # Verify usage
        assert response.usage is not None
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens
        
        # Verify raw response is stored
        assert response.raw == response_data
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    async def test_openai_tool_response(self):
        """Test parsing OpenAI response with tool calls."""
        # Try to load stored response first
        response_data = load_stored_response("openai_tools.json")
        
        if not response_data:
            # Call API if no stored response
            api_key = os.getenv("OPENAI_API_KEY")
            response_data = await call_openai_with_tools(api_key)
        
        # Extract data
        choice = response_data["choices"][0]
        message = choice["message"]
        
        # Create response object
        response = create_openai_response(
            content=message.get("content", ""),
            model=response_data["model"],
            raw_response=response_data,
            usage=response_data.get("usage"),
            finish_reason=choice.get("finish_reason"),
            tool_calls=message.get("tool_calls"),
        )
        
        # Verify response
        assert isinstance(response, OpenAIResponse)
        
        # Check if this is a tool call response
        if response.has_tool_calls:
            assert len(response.tool_calls) > 0
            tool_call = response.tool_calls[0]
            assert tool_call.id.startswith("call_")
            assert tool_call.type == "function"
            assert tool_call.function["name"] == "get_weather"
            assert "San Francisco" in tool_call.function["arguments"]


class TestAnthropicResponses:
    """Test Anthropic response parsing with real API data."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    async def test_anthropic_basic_response(self):
        """Test parsing basic Anthropic response."""
        # Try to load stored response first
        response_data = load_stored_response("anthropic_basic.json")
        
        if not response_data:
            # Call API if no stored response
            api_key = os.getenv("ANTHROPIC_API_KEY")
            response_data = await call_anthropic_api(api_key)
        
        # Extract content
        content = ""
        if response_data.get("content"):
            content_blocks = response_data["content"]
            if isinstance(content_blocks, list) and content_blocks:
                content = content_blocks[0].get("text", "")
        
        # Create response object
        response = create_anthropic_response(
            content=content,
            model=response_data["model"],
            raw_response=response_data,
            usage=response_data.get("usage"),
            finish_reason=response_data.get("stop_reason"),
        )
        
        # Verify response
        assert isinstance(response, AnthropicResponse)
        assert response.content == content
        assert response.metadata.model == response_data["model"]
        assert response.metadata.id == response_data["id"]
        assert response.metadata.type == response_data["type"]
        
        # Verify usage (Anthropic uses different field names)
        if response.usage:
            assert response.usage.prompt_tokens > 0
            assert response.usage.completion_tokens > 0
            assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens


class TestGeminiResponses:
    """Test Gemini response parsing with real API data."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    async def test_gemini_basic_response(self):
        """Test parsing basic Gemini response."""
        # Try to load stored response first
        response_data = load_stored_response("gemini_basic.json")
        
        if not response_data:
            # Call API if no stored response
            api_key = os.getenv("GEMINI_API_KEY")
            response_data = await call_gemini_api(api_key)
        
        # Extract content
        content = ""
        if response_data.get("candidates"):
            candidate = response_data["candidates"][0]
            content_parts = candidate.get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in content_parts)
        
        # Create response object
        response = create_gemini_response(
            content=content,
            model="gemini-1.5-flash",  # API doesn't return model in response
            raw_response=response_data,
            usage=response_data.get("usageMetadata"),
            finish_reason=response_data.get("candidates", [{}])[0].get("finishReason"),
        )
        
        # Verify response
        assert isinstance(response, GeminiResponse)
        assert response.content == content
        assert response.metadata.candidates_count == len(response_data.get("candidates", []))
        
        # Check safety ratings if present
        if response.metadata.safety_ratings:
            assert isinstance(response.metadata.safety_ratings, list)
            assert all("category" in rating for rating in response.metadata.safety_ratings)
        
        # Verify usage if present
        if response.usage:
            assert response.usage.total_tokens > 0


class TestStoredResponses:
    """Test with stored responses (no API calls needed)."""
    
    def test_parse_stored_openai_response(self):
        """Test parsing stored OpenAI response."""
        response_data = load_stored_response("openai_basic.json")
        if not response_data:
            pytest.skip("No stored OpenAI response found")
        
        choice = response_data["choices"][0]
        response = create_openai_response(
            content=choice["message"]["content"],
            model=response_data["model"],
            raw_response=response_data,
            usage=response_data.get("usage"),
            finish_reason=choice.get("finish_reason"),
        )
        
        assert isinstance(response, OpenAIResponse)
        assert response.metadata.provider == "openai"
        assert response.raw == response_data
    
    def test_parse_stored_anthropic_response(self):
        """Test parsing stored Anthropic response."""
        response_data = load_stored_response("anthropic_basic.json")
        if not response_data:
            pytest.skip("No stored Anthropic response found")
        
        content = ""
        if response_data.get("content"):
            content = response_data["content"][0].get("text", "")
        
        response = create_anthropic_response(
            content=content,
            model=response_data["model"],
            raw_response=response_data,
            usage=response_data.get("usage"),
            finish_reason=response_data.get("stop_reason"),
        )
        
        assert isinstance(response, AnthropicResponse)
        assert response.metadata.provider == "anthropic"
    
    def test_parse_stored_gemini_response(self):
        """Test parsing stored Gemini response."""
        response_data = load_stored_response("gemini_basic.json")
        if not response_data:
            pytest.skip("No stored Gemini response found")
        
        content = ""
        if response_data.get("candidates"):
            parts = response_data["candidates"][0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in parts)
        
        response = create_gemini_response(
            content=content,
            model="gemini-1.5-flash",
            raw_response=response_data,
            usage=response_data.get("usageMetadata"),
        )
        
        assert isinstance(response, GeminiResponse)
        assert response.metadata.provider == "gemini"


if __name__ == "__main__":
    # Run a quick test to store responses
    async def store_all_responses():
        """Store responses from all providers."""
        print("Storing API responses...")
        
        if api_key := os.getenv("OPENAI_API_KEY"):
            print("Calling OpenAI API...")
            await call_openai_api(api_key)
            await call_openai_with_tools(api_key)
        
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            print("Calling Anthropic API...")
            await call_anthropic_api(api_key)
        
        if api_key := os.getenv("GEMINI_API_KEY"):
            print("Calling Gemini API...")
            await call_gemini_api(api_key)
        
        print(f"Responses stored in: {RESPONSES_DIR}")
    
    asyncio.run(store_all_responses())
