"""Tests for unified LLM client.

Note: These tests require valid API keys to be set as environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY
"""

import os
from unittest.mock import patch

import pytest

from llmgine.unified.models import UnifiedMessage, UnifiedRequest
from llmgine.orchestrator.client import UnifiedLLMClient


class TestUnifiedLLMClient:
    """Test UnifiedLLMClient functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return UnifiedLLMClient(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            gemini_api_key="test-gemini-key",
        )
    
    def test_initialization(self):
        """Test client initialization."""
        client = UnifiedLLMClient(
            openai_api_key="custom-openai",
            anthropic_api_key="custom-anthropic",
            gemini_api_key="custom-gemini",
            timeout=30.0,
        )
        
        assert client.openai_api_key == "custom-openai"
        assert client.anthropic_api_key == "custom-anthropic"
        assert client.gemini_api_key == "custom-gemini"
        assert client.timeout == 30.0
    
    def test_initialization_from_env(self):
        """Test client initialization from environment variables."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "env-openai",
            "ANTHROPIC_API_KEY": "env-anthropic",
            "GEMINI_API_KEY": "env-gemini",
        }):
            client = UnifiedLLMClient()
            
            assert client.openai_api_key == "env-openai"
            assert client.anthropic_api_key == "env-anthropic"
            assert client.gemini_api_key == "env-gemini"
    
    def test_get_api_key_missing(self, client):
        """Test error when API key is missing."""
        client.openai_api_key = None
        
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            client._get_api_key("openai")
    
    def test_get_endpoint_openai(self, client):
        """Test OpenAI endpoint generation."""
        request = UnifiedRequest(model="gpt-4o-mini", messages=[])
        
        endpoint = client._get_endpoint("openai", request)
        assert endpoint == "https://api.openai.com/v1/chat/completions"
        
        request.stream = True
        endpoint = client._get_endpoint("openai", request)
        assert endpoint == "https://api.openai.com/v1/chat/completions"
    
    def test_get_endpoint_anthropic(self, client):
        """Test Anthropic endpoint generation."""
        request = UnifiedRequest(model="claude-3-5-sonnet-20241022", messages=[])
        
        endpoint = client._get_endpoint("anthropic", request)
        assert endpoint == "https://api.anthropic.com/v1/messages"
    
    def test_get_endpoint_gemini(self, client):
        """Test Gemini endpoint generation."""
        request = UnifiedRequest(model="gemini-2.0-flash", messages=[])
        
        endpoint = client._get_endpoint("gemini", request)
        assert endpoint == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        request.stream = True
        endpoint = client._get_endpoint("gemini", request)
        assert endpoint == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent"
    
    def test_prepare_request_openai(self, client):
        """Test request preparation for OpenAI."""
        request = UnifiedRequest(
            model="gpt-4o-mini",
            messages=[UnifiedMessage(role="user", content="Hello")],
            temperature=0.7,
        )
        
        endpoint, data, headers = client._prepare_request("openai", request)
        
        assert endpoint == "https://api.openai.com/v1/chat/completions"
        assert data["model"] == "gpt-4o-mini"
        assert data["temperature"] == 0.7
        assert headers["Authorization"] == "Bearer test-openai-key"
        assert headers["Content-Type"] == "application/json"
    
    def test_prepare_request_anthropic(self, client):
        """Test request preparation for Anthropic."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="system", content="Be helpful"),
                UnifiedMessage(role="user", content="Hello"),
            ],
        )
        
        endpoint, data, headers = client._prepare_request("anthropic", request)
        
        assert endpoint == "https://api.anthropic.com/v1/messages"
        assert data["model"] == "claude-3-5-sonnet-20241022"
        assert data["system"] == "Be helpful"
        assert headers["x-api-key"] == "test-anthropic-key"
        assert headers["anthropic-version"] == "2023-06-01"
    
    def test_prepare_request_gemini(self, client):
        """Test request preparation for Gemini."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[UnifiedMessage(role="user", content="Hello")],
        )
        
        endpoint, data, headers = client._prepare_request("gemini", request)
        
        assert "key=test-gemini-key" in endpoint
        assert len(data["contents"]) == 1
        assert headers["Content-Type"] == "application/json"
    
    def test_parse_stream_line_openai(self, client):
        """Test parsing OpenAI stream lines."""
        # Regular chunk
        line = 'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}'
        chunk = client._parse_stream_line("openai", line)
        assert chunk.content == "Hello"
        assert chunk.finish_reason is None
        
        # Final chunk
        line = 'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}'
        chunk = client._parse_stream_line("openai", line)
        assert chunk.content == ""
        assert chunk.finish_reason == "stop"
        
        # Done marker
        line = "data: [DONE]"
        chunk = client._parse_stream_line("openai", line)
        assert chunk is None
    
    def test_parse_stream_line_anthropic(self, client):
        """Test parsing Anthropic stream lines."""
        # Content chunk
        line = 'data: {"type":"content_block_delta","delta":{"text":"Hello"}}'
        chunk = client._parse_stream_line("anthropic", line)
        assert chunk.content == "Hello"
        assert chunk.finish_reason is None
        
        # Stop chunk
        line = 'data: {"type":"message_stop"}'
        chunk = client._parse_stream_line("anthropic", line)
        assert chunk.content == ""
        assert chunk.finish_reason == "stop"
    
    def test_parse_stream_line_gemini(self, client):
        """Test parsing Gemini stream lines."""
        # Regular chunk
        line = '{"candidates":[{"content":{"parts":[{"text":"Hello"}]},"finishReason":null}]}'
        chunk = client._parse_stream_line("gemini", line)
        assert chunk.content == "Hello"
        assert chunk.finish_reason is None
        
        # Final chunk
        line = '{"candidates":[{"content":{"parts":[]},"finishReason":"STOP"}]}'
        chunk = client._parse_stream_line("gemini", line)
        assert chunk.content == ""
        assert chunk.finish_reason == "STOP"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager functionality."""
        async with UnifiedLLMClient() as client:
            assert client._client is not None
        
        # Client should be closed after context
        assert client._client.is_closed


# Integration tests that require real API keys
@pytest.mark.skipif(
    not all([
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("ANTHROPIC_API_KEY"),
        os.environ.get("GEMINI_API_KEY"),
    ]),
    reason="Live API keys not available"
)
class TestLiveAPIs:
    """Test with live API calls."""
    
    @pytest.fixture
    async def client(self):
        """Create a real client with API keys from environment."""
        async with UnifiedLLMClient() as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_openai_generation(self, client):
        """Test OpenAI generation."""
        request = UnifiedRequest(
            model="gpt-4o-mini",
            messages=[
                UnifiedMessage(role="user", content="Say 'test successful' and nothing else")
            ],
            max_tokens=10,
            temperature=0,
        )
        
        response = await client.generate(request)
        
        assert response.content.lower() == "test successful"
        assert response.model == "gpt-4o-mini"
        assert response.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_anthropic_generation(self, client):
        """Test Anthropic generation."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="user", content="Say 'test successful' and nothing else")
            ],
            max_tokens=10,
            temperature=0,
        )
        
        response = await client.generate(request)
        
        assert "test successful" in response.content.lower()
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.finish_reason in ["end_turn", "stop_sequence", "max_tokens"]
    
    @pytest.mark.asyncio
    async def test_gemini_generation(self, client):
        """Test Gemini generation."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(role="user", content="Say 'test successful' and nothing else")
            ],
            max_tokens=10,
            temperature=0,
        )
        
        response = await client.generate(request)
        
        assert "test successful" in response.content.lower()
        assert response.model == "gemini-2.0-flash"
        assert response.finish_reason in ["STOP", "MAX_TOKENS"]
    
    @pytest.mark.asyncio
    async def test_streaming_openai(self, client):
        """Test OpenAI streaming."""
        request = UnifiedRequest(
            model="gpt-4o-mini",
            messages=[
                UnifiedMessage(role="user", content="Count from 1 to 3")
            ],
            stream=True,
            temperature=0,
        )
        
        chunks = []
        async for chunk in client.generate_stream(request):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        content = "".join(chunk.content for chunk in chunks)
        assert "1" in content and "2" in content and "3" in content
    
    @pytest.mark.asyncio
    async def test_provider_switching(self, client):
        """Test switching between providers with same code."""
        models = [
            "gpt-4o-mini",
            "claude-3-5-sonnet-20241022",
            "gemini-2.0-flash",
        ]
        
        for model in models:
            request = UnifiedRequest(
                model=model,
                messages=[
                    UnifiedMessage(role="user", content="Say 'hello' and nothing else")
                ],
                max_tokens=10,
                temperature=0,
            )
            
            response = await client.generate(request)
            
            assert "hello" in response.content.lower()
            assert response.model == model
