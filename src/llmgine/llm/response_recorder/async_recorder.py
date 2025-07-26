"""Async response recorder with observability integration."""

import asyncio
from typing import Any, Dict, Optional

from llmgine.bus import MessageBus
from llmgine.llm import SessionID
from llmgine.messages.response_recorder_events import (
    ResponseRecorded,
    ResponseRecorderMemoryWarning,
    ResponseRecordingFailed,
)

from .base import ResponseRecorderConfig
from .memory_recorder import MemoryResponseRecorder


class AsyncResponseRecorder(MemoryResponseRecorder):
    """Async response recorder with message bus integration."""

    def __init__(self, config: ResponseRecorderConfig, bus: Optional[MessageBus] = None):
        """Initialize with optional message bus for events."""
        super().__init__(config)
        self.bus = bus
        self._recording_tasks: set[asyncio.Task[None]] = set()

    async def record_response(
        self,
        provider: str,
        raw_response: Any,
        request_metadata: Dict[str, Any],
        session_id: str,
        response_id: str,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Record response asynchronously without blocking."""
        if not await self.is_enabled_for_provider(provider):
            return

        # Create task for async recording
        task = asyncio.create_task(
            self._record_with_observability(
                provider=provider,
                raw_response=raw_response,
                request_metadata=request_metadata,
                session_id=session_id,
                response_id=response_id,
                processing_time_ms=processing_time_ms,
            )
        )

        # Track task and clean up when done
        self._recording_tasks.add(task)
        task.add_done_callback(self._recording_tasks.discard)

    async def _record_with_observability(
        self,
        provider: str,
        raw_response: Any,
        request_metadata: Dict[str, Any],
        session_id: str,
        response_id: str,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Record response with error handling and events."""
        try:
            # Perform the actual recording
            await super().record_response(
                provider=provider,
                raw_response=raw_response,
                request_metadata=request_metadata,
                session_id=session_id,
                response_id=response_id,
                processing_time_ms=processing_time_ms,
            )

            # Emit success event if bus is available
            if self.bus:
                event = ResponseRecorded(
                    provider=provider,
                    response_id=response_id,
                    processing_time_ms=processing_time_ms,
                    session_id=SessionID(session_id),
                )
                await self.bus.publish(event)

            # Check memory usage and emit warning if needed
            memory_stats = await self.get_memory_usage()
            if memory_stats["buffer_utilization"] > 0.8 and self.bus:
                warning_event = ResponseRecorderMemoryWarning(
                    memory_usage_mb=memory_stats["memory_usage_mb"],
                    max_memory_mb=memory_stats["max_memory_mb"],
                    buffer_utilization=memory_stats["buffer_utilization"],
                    session_id=SessionID(session_id),
                )
                await self.bus.publish(warning_event)

        except Exception as e:
            # Emit failure event if bus is available
            if self.bus:
                error_event = ResponseRecordingFailed(
                    provider=provider,
                    response_id=response_id,
                    error=str(e),
                    session_id=SessionID(session_id),
                )
                await self.bus.publish(error_event)

            # Log but don't raise - recording failures shouldn't affect main flow
            if self.config.enabled:
                # In production, this would use proper logging
                pass

    async def stop(self) -> None:
        """Stop recorder and wait for pending recordings."""
        # Cancel any pending recording tasks
        for task in self._recording_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self._recording_tasks:
            await asyncio.gather(*self._recording_tasks, return_exceptions=True)

        await super().stop()

    async def __aenter__(self) -> "AsyncResponseRecorder":
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.stop()
