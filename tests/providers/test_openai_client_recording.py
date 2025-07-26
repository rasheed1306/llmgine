"""Tests for OpenAI client with response recording."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from llmgine.llm.response_recorder import AsyncResponseRecorder, ResponseRecorderConfig
from llmgine.providers.openai.client import OpenAIClient


@pytest.mark.asyncio
class TestOpenAIClientRecording:
    """Test OpenAI client with response recording integration."""

    @pytest_asyncio.fixture
    async def mock_recorder(self):
        """Create a mock response recorder."""
        config = ResponseRecorderConfig()
        recorder = AsyncResponseRecorder(config)
        recorder.record_response = AsyncMock()
        return recorder

    @pytest_asyncio.fixture
    async def client_with_recorder(self, mock_recorder):
        """Create OpenAI client with mock recorder."""
        client = OpenAIClient(
            api_key="test-key", response_recorder=mock_recorder, session_id="test-session"
        )
        yield client
        await client.close()

    @patch("httpx.AsyncClient.post")
    async def test_chat_completion_records_response(
        self, mock_post, client_with_recorder, mock_recorder
    ):
        """Test that chat completion records responses."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
        }
        mock_post.return_value = mock_response

        # Make API call
        result = await client_with_recorder.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
            temperature=0.7,
            max_tokens=100,
        )

        # Verify response
        assert result["choices"][0]["message"]["content"] == "Hello! How can I help you?"

        # Verify recording was called
        mock_recorder.record_response.assert_called_once()
        call_args = mock_recorder.record_response.call_args[1]

        assert call_args["provider"] == "openai"
        assert call_args["raw_response"] == mock_response.json.return_value
        assert call_args["session_id"] == "test-session"
        assert call_args["request_metadata"]["model"] == "gpt-4"
        assert call_args["request_metadata"]["temperature"] == 0.7
        assert call_args["request_metadata"]["max_tokens"] == 100
        assert call_args["request_metadata"]["messages_count"] == 1
        assert "response_id" in call_args
        assert "processing_time_ms" in call_args

    @patch("httpx.AsyncClient.post")
    async def test_chat_completion_without_recorder(self, mock_post):
        """Test that client works without recorder."""
        # Create client without recorder
        client = OpenAIClient(api_key="test-key")

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
        }
        mock_post.return_value = mock_response

        # Make API call - should work without recorder
        result = await client.chat_completion(
            model="gpt-4", messages=[{"role": "user", "content": "Hello!"}]
        )

        assert result["choices"][0]["message"]["content"] == "Hello!"

        await client.close()

    @patch("httpx.AsyncClient.stream")
    async def test_streaming_records_chunks(
        self, mock_stream, client_with_recorder, mock_recorder
    ):
        """Test that streaming records all chunks."""
        # Mock streaming response
        mock_response = AsyncMock()
        mock_response.status_code = 200

        # Simulate streaming chunks
        async def mock_aiter_lines():
            chunks = [
                'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}',
                'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" there!"},"finish_reason":null}]}',
                'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}',
                "data: [DONE]",
            ]
            for chunk in chunks:
                yield chunk

        mock_response.aiter_lines = mock_aiter_lines
        mock_stream.return_value.__aenter__.return_value = mock_response

        # Collect streamed chunks
        chunks = []
        async for chunk in client_with_recorder.chat_completion_stream(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
            temperature=0.5,
        ):
            chunks.append(chunk)

        # Verify we got all chunks
        assert len(chunks) == 3

        # Verify recording was called
        mock_recorder.record_response.assert_called_once()
        call_args = mock_recorder.record_response.call_args[1]

        assert call_args["provider"] == "openai"
        assert call_args["raw_response"]["chunk_count"] == 3
        assert len(call_args["raw_response"]["stream_chunks"]) == 3
        assert call_args["request_metadata"]["stream"] is True
        assert call_args["request_metadata"]["model"] == "gpt-4"
        assert call_args["request_metadata"]["temperature"] == 0.5
