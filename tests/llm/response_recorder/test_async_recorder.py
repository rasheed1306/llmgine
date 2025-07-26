"""Tests for async response recorder with observability."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from llmgine.bus import MessageBus
from llmgine.llm.response_recorder import (
    AsyncResponseRecorder,
    ResponseRecorderConfig,
)
from llmgine.messages.response_recorder_events import (
    ResponseRecorded,
    ResponseRecorderMemoryWarning,
    ResponseRecordingFailed,
)


@pytest.mark.asyncio
class TestAsyncResponseRecorder:
    """Test AsyncResponseRecorder with message bus integration."""

    @pytest_asyncio.fixture
    async def mock_bus(self):
        """Create a mock message bus."""
        bus = Mock(spec=MessageBus)
        bus.publish = AsyncMock()
        return bus

    @pytest_asyncio.fixture
    async def recorder(self, mock_bus):
        """Create a test recorder with mock bus."""
        config = ResponseRecorderConfig(
            buffer_size=10,
            max_memory_mb=1,
        )
        recorder = AsyncResponseRecorder(config, bus=mock_bus)
        yield recorder
        await recorder.stop()

    async def test_async_recording_non_blocking(self, recorder, mock_bus):
        """Test that recording doesn't block the caller."""
        # Record response and measure time
        start_time = asyncio.get_event_loop().time()

        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={"model": "gpt-4"},
            session_id="test-session",
            response_id="response-1",
            processing_time_ms=100.0,
        )

        elapsed = asyncio.get_event_loop().time() - start_time

        # Should return almost immediately (not waiting for recording)
        assert elapsed < 0.1  # Should be much faster than this

        # Wait a bit for async recording to complete
        await asyncio.sleep(0.1)

        # Verify event was published
        mock_bus.publish.assert_called()
        call_args = mock_bus.publish.call_args[0][0]
        assert isinstance(call_args, ResponseRecorded)
        assert call_args.provider == "openai"
        assert call_args.response_id == "response-1"

    async def test_memory_warning_event(self, mock_bus):
        """Test that memory warning events are emitted."""
        # Create recorder with small buffer to trigger warning
        config = ResponseRecorderConfig(
            buffer_size=5,
            max_memory_mb=1,
        )
        recorder = AsyncResponseRecorder(config, bus=mock_bus)

        # Fill buffer past 80% to trigger warning
        for i in range(5):
            await recorder.record_response(
                provider="openai",
                raw_response={"index": i},
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )

        # Wait for async recording
        await asyncio.sleep(0.1)

        # Check that warning event was published
        warning_calls = [
            call
            for call in mock_bus.publish.call_args_list
            if isinstance(call[0][0], ResponseRecorderMemoryWarning)
        ]
        assert len(warning_calls) >= 1
        warning_event = warning_calls[0][0][0]
        assert warning_event.buffer_utilization >= 0.8

        await recorder.stop()

    async def test_recording_failure_event(self, mock_bus):
        """Test that recording failures emit events."""
        config = ResponseRecorderConfig()
        recorder = AsyncResponseRecorder(config, bus=mock_bus)

        # Mock the parent record_response to raise an exception
        original_method = recorder.__class__.__bases__[0].record_response

        async def failing_record(*args, **kwargs):
            raise ValueError("Test recording failure")

        recorder.__class__.__bases__[0].record_response = failing_record

        try:
            await recorder.record_response(
                provider="openai",
                raw_response={"test": "data"},
                request_metadata={},
                session_id="test-session",
                response_id="response-1",
            )

            # Wait for async recording
            await asyncio.sleep(0.1)

            # Check that failure event was published
            failure_calls = [
                call
                for call in mock_bus.publish.call_args_list
                if isinstance(call[0][0], ResponseRecordingFailed)
            ]
            assert len(failure_calls) == 1
            failure_event = failure_calls[0][0][0]
            assert failure_event.provider == "openai"
            assert failure_event.response_id == "response-1"
            assert "Test recording failure" in failure_event.error

        finally:
            # Restore original method
            recorder.__class__.__bases__[0].record_response = original_method
            await recorder.stop()

    async def test_no_events_without_bus(self):
        """Test that recorder works without message bus."""
        config = ResponseRecorderConfig()
        recorder = AsyncResponseRecorder(config, bus=None)

        # Should not raise any errors
        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={},
            session_id="test-session",
            response_id="response-1",
        )

        # Wait for async recording
        await asyncio.sleep(0.1)

        # Verify response was recorded
        responses = await recorder.get_recorded_responses()
        assert len(responses) == 1

        await recorder.stop()

    async def test_concurrent_recording_tasks(self, recorder):
        """Test handling multiple concurrent recording tasks."""
        # Record many responses concurrently
        tasks = []
        for i in range(20):
            task = recorder.record_response(
                provider="openai",
                raw_response={"index": i},
                request_metadata={},
                session_id="test-session",
                response_id=f"response-{i}",
            )
            tasks.append(task)

        # All should complete quickly (non-blocking)
        await asyncio.gather(*tasks)

        # Wait for all async recordings to complete
        await asyncio.sleep(0.2)

        # Check that responses were recorded
        responses = await recorder.get_recorded_responses()
        assert len(responses) == 10  # Buffer size is 10, should have last 10

    async def test_stop_cancels_pending_tasks(self, recorder):
        """Test that stop() cancels pending recording tasks."""

        # Start a recording that will take time
        async def slow_record(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow recording

        # Monkey patch to make recording slow
        recorder._record_with_observability = slow_record

        # Start recording
        await recorder.record_response(
            provider="openai",
            raw_response={"test": "data"},
            request_metadata={},
            session_id="test-session",
            response_id="response-1",
        )

        # Should have pending task
        assert len(recorder._recording_tasks) > 0

        # Stop should cancel tasks
        await recorder.stop()

        # All tasks should be done (cancelled)
        for task in recorder._recording_tasks:
            assert task.done()

    async def test_recording_with_no_processing_time(self, recorder, mock_bus):
        """Test recording without processing time metric."""
        await recorder.record_response(
            provider="anthropic",
            raw_response={"result": "success"},
            request_metadata={"model": "claude-3"},
            session_id="test-session",
            response_id="response-1",
            processing_time_ms=None,
        )

        # Wait for async recording
        await asyncio.sleep(0.1)

        # Verify event was published without processing time
        mock_bus.publish.assert_called()
        call_args = mock_bus.publish.call_args[0][0]
        assert isinstance(call_args, ResponseRecorded)
        assert call_args.processing_time_ms is None
