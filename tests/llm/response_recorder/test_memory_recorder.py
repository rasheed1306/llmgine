"""Tests for memory-based response recorder."""

import asyncio
from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from llmgine.llm.response_recorder import (
    MemoryResponseRecorder,
    ResponseRecorderConfig,
)


@pytest.mark.asyncio
class TestMemoryResponseRecorder:
    """Test MemoryResponseRecorder functionality."""

    @pytest_asyncio.fixture
    async def recorder(self):
        """Create a test recorder."""
        config = ResponseRecorderConfig(
            buffer_size=10,
            max_memory_mb=1,
        )
        recorder = MemoryResponseRecorder(config)
        yield recorder
        await recorder.stop()

    async def test_record_response(self, recorder):
        """Test recording a basic response."""
        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={"model": "gpt-4"},
            session_id="test-session",
            response_id="response-1",
            processing_time_ms=100.0,
        )

        responses = await recorder.get_recorded_responses()
        assert len(responses) == 1
        assert responses[0].provider == "openai"
        assert responses[0].response_id == "response-1"
        assert responses[0].processing_time_ms == 100.0

    async def test_provider_filtering(self, recorder):
        """Test that disabled providers are not recorded."""
        # Record for enabled provider
        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={},
            session_id="test-session",
            response_id="response-1",
        )

        # Try to record for non-configured provider
        await recorder.record_response(
            provider="unknown-provider",
            raw_response={"test": "data"},
            request_metadata={},
            session_id="test-session",
            response_id="response-2",
        )

        responses = await recorder.get_recorded_responses()
        assert len(responses) == 1
        assert responses[0].response_id == "response-1"

    async def test_buffer_limit(self, recorder):
        """Test that buffer respects size limit."""
        # Record more responses than buffer size
        for i in range(15):
            await recorder.record_response(
                provider="openai",
                raw_response={"index": i},
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )

        responses = await recorder.get_recorded_responses()
        assert len(responses) == 10  # Buffer size is 10
        # Should have kept the most recent responses (5-14)
        assert responses[0].response_id == "response-14"  # Most recent first
        assert responses[9].response_id == "response-5"

    async def test_get_recorded_responses_with_filters(self, recorder):
        """Test filtering recorded responses."""
        # Record responses for different sessions and providers
        await recorder.record_response(
            provider="openai",
            raw_response={"test": 1},
            request_metadata={},
            session_id="session-1",
            response_id="response-1",
        )
        await recorder.record_response(
            provider="anthropic",
            raw_response={"test": 2},
            request_metadata={},
            session_id="session-1",
            response_id="response-2",
        )
        await recorder.record_response(
            provider="openai",
            raw_response={"test": 3},
            request_metadata={},
            session_id="session-2",
            response_id="response-3",
        )

        # Test session filter
        session_responses = await recorder.get_recorded_responses(session_id="session-1")
        assert len(session_responses) == 2
        assert all(r.session_id == "session-1" for r in session_responses)

        # Test provider filter
        openai_responses = await recorder.get_recorded_responses(provider="openai")
        assert len(openai_responses) == 2
        assert all(r.provider == "openai" for r in openai_responses)

        # Test combined filters
        filtered_responses = await recorder.get_recorded_responses(
            session_id="session-1", provider="anthropic"
        )
        assert len(filtered_responses) == 1
        assert filtered_responses[0].response_id == "response-2"

    async def test_clear_old_responses(self, recorder):
        """Test clearing old responses by timestamp."""
        now = datetime.now()

        # Record some responses
        for i in range(5):
            await recorder.record_response(
                provider="openai",
                raw_response={"index": i},
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )

        # Clear responses older than now (should clear nothing)
        cleared = await recorder.clear_old_responses(now - timedelta(minutes=1))
        assert cleared == 0
        assert len(await recorder.get_recorded_responses()) == 5

        # Clear all responses
        cleared = await recorder.clear_old_responses(now + timedelta(minutes=1))
        assert cleared == 5
        assert len(await recorder.get_recorded_responses()) == 0

    async def test_memory_usage_tracking(self, recorder):
        """Test memory usage statistics."""
        initial_stats = await recorder.get_memory_usage()
        assert initial_stats["buffer_size"] == 0
        assert initial_stats["memory_usage_bytes"] == 0
        assert initial_stats["buffer_utilization"] == 0

        # Record some responses
        for i in range(5):
            await recorder.record_response(
                provider="openai",
                raw_response={"data": "x" * 100},  # Some data
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )

        stats = await recorder.get_memory_usage()
        assert stats["buffer_size"] == 5
        assert stats["memory_usage_bytes"] > 0
        assert stats["buffer_utilization"] == 0.5  # 5/10

    async def test_memory_limit_enforcement(self, recorder):
        """Test that memory limits are enforced."""
        # Create very large responses to test memory limit
        large_data = {"data": "x" * 10000}  # Large payload

        recorded_count = 0
        for i in range(100):  # Try to record many large responses
            await recorder.record_response(
                provider="openai",
                raw_response=large_data,
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )
            recorded_count += 1

        # Check that we stayed within memory limits
        stats = await recorder.get_memory_usage()
        assert stats["memory_usage_mb"] <= stats["max_memory_mb"]

    async def test_concurrent_recording(self, recorder):
        """Test concurrent response recording."""

        async def record_many(start_idx: int, count: int):
            for i in range(count):
                await recorder.record_response(
                    provider="openai",
                    raw_response={"index": start_idx + i},
                    request_metadata={},
                    session_id="test-session",
                    response_id=f"response-{start_idx}-{i}",
                )

        # Record concurrently from multiple tasks
        await asyncio.gather(
            record_many(0, 3),
            record_many(100, 3),
            record_many(200, 3),
        )

        responses = await recorder.get_recorded_responses()
        assert len(responses) == 9  # 3 tasks * 3 responses each

    async def test_disabled_recorder(self):
        """Test that disabled recorder doesn't record anything."""
        config = ResponseRecorderConfig(enabled=False)
        recorder = MemoryResponseRecorder(config)

        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={},
            session_id="test-session",
            response_id="response-1",
        )

        responses = await recorder.get_recorded_responses()
        assert len(responses) == 0

        await recorder.stop()
