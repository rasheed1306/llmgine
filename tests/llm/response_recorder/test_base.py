"""Tests for base response recorder functionality."""

from datetime import datetime

from llmgine.llm.response_recorder import RecordedResponse, ResponseRecorderConfig


class TestResponseRecorderConfig:
    """Test ResponseRecorderConfig validation and defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ResponseRecorderConfig()
        assert config.enabled is True
        assert config.max_memory_mb == 100
        assert config.buffer_size == 1000
        assert config.providers == ["openai", "anthropic", "gemini"]
        assert config.flush_interval_seconds == 5.0
        assert config.storage_backend == "memory"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ResponseRecorderConfig(
            enabled=False,
            max_memory_mb=200,
            buffer_size=2000,
            providers=["openai"],
            flush_interval_seconds=10.0,
            storage_backend="file",
        )
        assert config.enabled is False
        assert config.max_memory_mb == 200
        assert config.buffer_size == 2000
        assert config.providers == ["openai"]
        assert config.flush_interval_seconds == 10.0
        assert config.storage_backend == "file"


class TestRecordedResponse:
    """Test RecordedResponse data structure."""

    def test_recorded_response_creation(self):
        """Test creating a recorded response."""
        response = RecordedResponse(
            provider="openai",
            raw_response={"choices": [{"message": {"content": "Hello"}}]},
            request_metadata={"model": "gpt-4", "temperature": 0.7},
            session_id="test-session",
            response_id="test-response",
            processing_time_ms=123.45,
        )

        assert response.provider == "openai"
        assert response.raw_response == {"choices": [{"message": {"content": "Hello"}}]}
        assert response.request_metadata == {"model": "gpt-4", "temperature": 0.7}
        assert response.session_id == "test-session"
        assert response.response_id == "test-response"
        assert response.processing_time_ms == 123.45
        assert isinstance(response.timestamp, datetime)
        assert response.error is None

    def test_recorded_response_with_error(self):
        """Test creating a recorded response with error."""
        response = RecordedResponse(
            provider="anthropic",
            raw_response=None,
            request_metadata={"model": "claude-3"},
            session_id="test-session",
            response_id="test-response",
            error="API rate limit exceeded",
        )

        assert response.provider == "anthropic"
        assert response.raw_response is None
        assert response.error == "API rate limit exceeded"
