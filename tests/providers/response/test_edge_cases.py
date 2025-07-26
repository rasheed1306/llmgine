"""Test edge cases and provider-specific features in response models."""

import json
from pathlib import Path

from llmgine.providers.response import (
    AnthropicMetadata,
    OpenAIMetadata,
    StreamChunk,
    StreamingResponse,
    Usage,
    create_anthropic_response,
    create_gemini_response,
    create_openai_response,
)

# Load stored responses for testing
RESPONSES_DIR = Path(__file__).parent / "stored_responses"


class TestOpenAISpecificFeatures:
    """Test OpenAI-specific features."""
    
    def test_openai_o1_reasoning_response(self):
        """Test OpenAI o1 model with reasoning tokens."""
        # Simulated o1 response with reasoning
        raw_response = {
            "id": "chatcmpl-o1-test",
            "model": "o1-preview",
            "choices": [{
                "message": {
                    "content": "The answer is 42",
                    "reasoning_content": "Let me think step by step. First, I need to consider...",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "reasoning_tokens": 100,
                "total_tokens": 160
            },
            "system_fingerprint": "fp_o1_test"
        }
        
        response = create_openai_response(
            content="The answer is 42",
            model="o1-preview",
            raw_response=raw_response,
            usage=raw_response["usage"],
            finish_reason="stop",
        )
        
        # Verify reasoning content
        assert response.metadata.reasoning_content == "Let me think step by step. First, I need to consider..."
        
        # Verify reasoning tokens are captured
        assert hasattr(response.usage, "reasoning_tokens")
        assert response.usage.reasoning_tokens == 100
        assert response.usage.total_tokens == 160
    
    def test_openai_empty_content_with_tools(self):
        """Test OpenAI response with empty content but tool calls."""
        raw_response = {
            "id": "chatcmpl-tool-only",
            "model": "gpt-4",
            "choices": [{
                "message": {
                    "content": None,  # Can be None when only tool calls
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "calculate",
                            "arguments": "{\"x\": 5, \"y\": 3}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35}
        }
        
        response = create_openai_response(
            content="",  # Empty string for None content
            model="gpt-4",
            raw_response=raw_response,
            usage=raw_response["usage"],
            finish_reason="tool_calls",
            tool_calls=raw_response["choices"][0]["message"]["tool_calls"],
        )
        
        assert response.content == ""
        assert response.has_tool_calls is True
        assert len(response.tool_calls) == 1
        assert response.finish_reason == "tool_calls"


class TestAnthropicSpecificFeatures:
    """Test Anthropic-specific features."""
    
    def test_anthropic_cache_tokens(self):
        """Test Anthropic response with cache tokens."""
        raw_response = {
            "id": "msg_cache_test",
            "type": "message",
            "model": "claude-3-sonnet-20241022",
            "content": [{"type": "text", "text": "Cached response"}],
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 50,
                "cache_creation_input_tokens": 800,
                "cache_read_input_tokens": 200
            },
            "stop_reason": "end_turn"
        }
        
        response = create_anthropic_response(
            content="Cached response",
            model=raw_response["model"],
            raw_response=raw_response,
            usage=raw_response["usage"],
            finish_reason="end_turn",
        )
        
        # Verify cache tokens are captured
        assert hasattr(response.usage, "cache_creation_input_tokens")
        assert response.usage.cache_creation_input_tokens == 800
        assert hasattr(response.usage, "cache_read_input_tokens")
        assert response.usage.cache_read_input_tokens == 200
    
    def test_anthropic_stop_sequence(self):
        """Test Anthropic response with stop sequence."""
        raw_response = {
            "id": "msg_stop_seq",
            "type": "message",
            "model": "claude-3-haiku-20240307",
            "content": [{"type": "text", "text": "Response until stop"}],
            "stop_sequence": "\\n\\nHuman:",
            "stop_reason": "stop_sequence",
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        
        response = create_anthropic_response(
            content="Response until stop",
            model=raw_response["model"],
            raw_response=raw_response,
            usage=raw_response["usage"],
            finish_reason="stop_sequence",
        )
        
        assert response.metadata.stop_sequence == "\\n\\nHuman:"
        assert response.finish_reason == "stop_sequence"


class TestGeminiSpecificFeatures:
    """Test Gemini-specific features."""
    
    def test_gemini_safety_ratings(self):
        """Test Gemini response with safety ratings."""
        response_data = json.load(open(RESPONSES_DIR / "gemini_basic.json"))
        
        content = ""
        if response_data.get("candidates"):
            parts = response_data["candidates"][0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in parts)
        
        response = create_gemini_response(
            content=content,
            model="gemini-1.5-flash",
            raw_response=response_data,
            usage=response_data.get("usageMetadata"),
            finish_reason=response_data["candidates"][0].get("finishReason"),
        )
        
        # Verify safety ratings
        assert response.metadata.safety_ratings is not None
        assert len(response.metadata.safety_ratings) > 0
        
        # Check rating structure
        for rating in response.metadata.safety_ratings:
            assert "category" in rating
            assert "probability" in rating
            assert rating["probability"] in ["NEGLIGIBLE", "LOW", "MEDIUM", "HIGH"]
    
    def test_gemini_blocked_response(self):
        """Test Gemini response when content is blocked."""
        raw_response = {
            "candidates": [{
                "content": {"parts": [], "role": "model"},
                "finishReason": "SAFETY",
                "safetyRatings": [
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "probability": "HIGH"}
                ]
            }],
            "promptFeedback": {
                "blockReason": "SAFETY",
                "safetyRatings": [
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "probability": "HIGH"}
                ]
            }
        }
        
        response = create_gemini_response(
            content="",  # Empty due to blocking
            model="gemini-1.5-flash",
            raw_response=raw_response,
            finish_reason="SAFETY",
        )
        
        assert response.content == ""
        assert response.finish_reason == "SAFETY"
        assert response.metadata.prompt_feedback["blockReason"] == "SAFETY"


class TestStreamingEdgeCases:
    """Test edge cases in streaming responses."""
    
    def test_empty_stream_chunks(self):
        """Test handling empty chunks in stream."""
        stream = StreamingResponse[OpenAIMetadata]()
        
        # Add some empty chunks
        stream.add_chunk(StreamChunk(delta=""))
        stream.add_chunk(StreamChunk(delta=""))
        stream.add_chunk(StreamChunk(delta="Hello"))
        stream.add_chunk(StreamChunk(delta=""))
        stream.add_chunk(StreamChunk(delta=" world", finish_reason="stop"))
        
        assert stream.content == "Hello world"
        assert stream.finish_reason == "stop"
    
    def test_stream_with_tool_calls(self):
        """Test streaming response with tool calls."""
        stream = StreamingResponse[OpenAIMetadata]()
        
        # Simulate chunks building up tool calls
        stream.add_chunk(StreamChunk(delta="I'll help you with that."))
        
        # Final chunk with tool calls
        final_chunk = StreamChunk(
            delta="",
            finish_reason="tool_calls",
            tool_calls=[{
                "id": "call_stream_123",
                "type": "function",
                "function": {"name": "search", "arguments": '{"query": "test"}'}
            }]
        )
        stream.add_chunk(final_chunk)
        
        assert stream.content == "I'll help you with that."
        assert stream.finish_reason == "tool_calls"
        assert stream.tool_calls is not None
        assert len(stream.tool_calls) == 1
    
    def test_stream_usage_accumulation(self):
        """Test that usage is only taken from final chunk."""
        stream = StreamingResponse[AnthropicMetadata]()
        
        # Add chunks with partial usage (should be ignored)
        stream.add_chunk(StreamChunk(
            delta="Part 1",
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        ))
        
        stream.add_chunk(StreamChunk(delta=" Part 2"))
        
        # Final chunk with complete usage
        stream.add_chunk(StreamChunk(
            delta=" Part 3",
            finish_reason="end_turn",
            usage=Usage(prompt_tokens=10, completion_tokens=8, total_tokens=18)
        ))
        
        # Only final usage should be kept
        assert stream.usage.completion_tokens == 8
        assert stream.usage.total_tokens == 18


class TestErrorCases:
    """Test error handling in response models."""
    
    def test_malformed_openai_response(self):
        """Test handling malformed OpenAI response."""
        # Missing choices
        raw_response = {
            "id": "test",
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        
        # Should handle gracefully
        response = create_openai_response(
            content="Fallback content",
            model=raw_response["model"],
            raw_response=raw_response,
            usage=raw_response["usage"],
        )
        
        assert response.content == "Fallback content"
        assert response.metadata.reasoning_content is None  # No choices to extract from
    
    def test_missing_usage_data(self):
        """Test handling missing usage data."""
        response = create_anthropic_response(
            content="No usage data",
            model="claude-3-haiku-20240307",
            raw_response={"id": "test"},
            usage=None,  # No usage data
            finish_reason="end_turn",
        )
        
        assert response.usage is None
        assert response.total_tokens is None  # Property handles None usage
