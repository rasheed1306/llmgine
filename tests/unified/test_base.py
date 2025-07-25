"""Tests for unified base models."""

import pytest

from llmgine.unified.models import (
    ContentBlock,
    UnifiedMessage,
    UnifiedRequest,
    UnifiedResponse,
    UnifiedStreamChunk,
)


class TestContentBlock:
    """Test ContentBlock model."""
    
    def test_text_content(self):
        """Test text content block."""
        block = ContentBlock(type="text", text="Hello world")
        assert block.type == "text"
        assert block.text == "Hello world"
        assert block.image_url is None
        assert block.image_base64 is None
    
    def test_image_url_content(self):
        """Test image URL content block."""
        block = ContentBlock(
            type="image",
            image_url="https://example.com/image.png",
            mime_type="image/png"
        )
        assert block.type == "image"
        assert block.image_url == "https://example.com/image.png"
        assert block.mime_type == "image/png"
    
    def test_image_base64_content(self):
        """Test base64 image content block."""
        block = ContentBlock(
            type="image",
            image_base64="iVBORw0KGgoAAAANS...",
            mime_type="image/png"
        )
        assert block.type == "image"
        assert block.image_base64 == "iVBORw0KGgoAAAANS..."
        assert block.mime_type == "image/png"


class TestUnifiedMessage:
    """Test UnifiedMessage model."""
    
    def test_simple_text_message(self):
        """Test message with simple text content."""
        msg = UnifiedMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_multimodal_message(self):
        """Test message with multiple content blocks."""
        blocks = [
            ContentBlock(type="text", text="Check out this image:"),
            ContentBlock(type="image", image_url="https://example.com/pic.jpg"),
        ]
        msg = UnifiedMessage(role="user", content=blocks)
        assert msg.role == "user"
        assert len(msg.content) == 2
        assert msg.content[0].text == "Check out this image:"
        assert msg.content[1].image_url == "https://example.com/pic.jpg"
    
    def test_role_validation(self):
        """Test role validation."""
        with pytest.raises(ValueError):
            UnifiedMessage(role="invalid", content="test")


class TestUnifiedRequest:
    """Test UnifiedRequest model."""
    
    def test_minimal_request(self):
        """Test request with minimal fields."""
        req = UnifiedRequest(
            model="gpt-4o-mini",
            messages=[UnifiedMessage(role="user", content="Hello")]
        )
        assert req.model == "gpt-4o-mini"
        assert len(req.messages) == 1
        assert req.stream is False
        assert req.temperature is None
        assert req.max_tokens is None
    
    def test_full_request(self):
        """Test request with all fields."""
        req = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="system", content="Be helpful"),
                UnifiedMessage(role="user", content="Hello"),
            ],
            max_tokens=1000,
            temperature=0.7,
            system="System prompt for Anthropic",
            stream=True
        )
        assert req.model == "claude-3-5-sonnet-20241022"
        assert len(req.messages) == 2
        assert req.max_tokens == 1000
        assert req.temperature == 0.7
        assert req.system == "System prompt for Anthropic"
        assert req.stream is True


class TestUnifiedResponse:
    """Test UnifiedResponse model."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        resp = UnifiedResponse(
            content="Hello from AI",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop"
        )
        assert resp.content == "Hello from AI"
        assert resp.model == "gpt-4o-mini"
        assert resp.usage["total_tokens"] == 15
        assert resp.finish_reason == "stop"
    
    def test_from_openai(self):
        """Test creating response from OpenAI format."""
        openai_resp = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        resp = UnifiedResponse.from_openai(openai_resp)
        assert resp.content == "Hello!"
        assert resp.model == "gpt-4o-mini"
        assert resp.usage["total_tokens"] == 15
        assert resp.finish_reason == "stop"
    
    def test_from_anthropic(self):
        """Test creating response from Anthropic format."""
        anthropic_resp = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello from Claude!"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }
        
        resp = UnifiedResponse.from_anthropic(anthropic_resp)
        assert resp.content == "Hello from Claude!"
        assert resp.model == "claude-3-5-sonnet-20241022"
        assert resp.usage["prompt_tokens"] == 10
        assert resp.usage["completion_tokens"] == 5
        assert resp.usage["total_tokens"] == 15
        assert resp.finish_reason == "end_turn"
    
    def test_from_gemini(self):
        """Test creating response from Gemini format."""
        gemini_resp = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Hello from Gemini!"}],
                    "role": "model"
                },
                "finishReason": "STOP",
                "index": 0
            }],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 5,
                "totalTokenCount": 15
            },
            "modelVersion": "gemini-2.0-flash"
        }
        
        resp = UnifiedResponse.from_gemini(gemini_resp)
        assert resp.content == "Hello from Gemini!"
        assert resp.model == "gemini-2.0-flash"
        assert resp.usage["prompt_tokens"] == 10
        assert resp.usage["completion_tokens"] == 5
        assert resp.usage["total_tokens"] == 15
        assert resp.finish_reason == "STOP"


class TestUnifiedStreamChunk:
    """Test UnifiedStreamChunk model."""
    
    def test_stream_chunk(self):
        """Test stream chunk creation."""
        chunk = UnifiedStreamChunk(
            content="Hello",
            finish_reason=None,
            raw_chunk={"data": "raw"}
        )
        assert chunk.content == "Hello"
        assert chunk.finish_reason is None
        assert chunk.raw_chunk["data"] == "raw"
    
    def test_final_chunk(self):
        """Test final stream chunk."""
        chunk = UnifiedStreamChunk(
            content="",
            finish_reason="stop",
            raw_chunk=None
        )
        assert chunk.content == ""
        assert chunk.finish_reason == "stop"
