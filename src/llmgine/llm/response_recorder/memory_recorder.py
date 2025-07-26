"""Memory-based implementation of ResponseRecorder."""

import asyncio
import contextlib
import sys
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import RecordedResponse, ResponseRecorder, ResponseRecorderConfig


class MemoryResponseRecorder(ResponseRecorder):
    """In-memory implementation of ResponseRecorder with bounded buffer."""

    def __init__(self, config: ResponseRecorderConfig):
        """Initialize the memory recorder."""
        super().__init__(config)
        self._buffer: deque[RecordedResponse] = deque(maxlen=config.buffer_size)
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._memory_usage_bytes = 0
        self._max_memory_bytes = config.max_memory_mb * 1024 * 1024

    async def record_response(
        self,
        provider: str,
        raw_response: Any,
        request_metadata: Dict[str, Any],
        session_id: str,
        response_id: str,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Record a response in memory buffer."""
        if not await self.is_enabled_for_provider(provider):
            return

        recorded_response = RecordedResponse(
            provider=provider,
            raw_response=raw_response,
            request_metadata=request_metadata,
            session_id=session_id,
            response_id=response_id,
            processing_time_ms=processing_time_ms,
        )

        # Estimate memory usage
        response_size = self._estimate_response_size(recorded_response)

        async with self._lock:
            # Check memory limit
            if self._memory_usage_bytes + response_size > self._max_memory_bytes:
                # Remove oldest responses until we have space
                while (
                    self._buffer
                    and self._memory_usage_bytes + response_size > self._max_memory_bytes
                ):
                    old_response = self._buffer.popleft()
                    old_size = self._estimate_response_size(old_response)
                    self._memory_usage_bytes -= old_size

            # Add new response
            self._buffer.append(recorded_response)
            self._memory_usage_bytes += response_size

    async def flush(self) -> None:
        """Flush buffered responses (no-op for memory recorder)."""
        # Memory recorder doesn't need to flush to external storage
        pass

    async def get_recorded_responses(
        self,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> List[RecordedResponse]:
        """Get recorded responses from memory buffer."""
        async with self._lock:
            responses = list(self._buffer)

        # Apply filters
        if session_id:
            responses = [r for r in responses if r.session_id == session_id]
        if provider:
            responses = [r for r in responses if r.provider == provider]

        # Sort by timestamp (newest first) and limit
        responses.sort(key=lambda r: r.timestamp, reverse=True)
        return responses[:limit]

    async def clear_old_responses(self, older_than: datetime) -> int:
        """Clear responses older than specified datetime."""
        cleared_count = 0

        async with self._lock:
            new_buffer: deque[RecordedResponse] = deque(maxlen=self.config.buffer_size)
            new_memory_usage = 0

            for response in self._buffer:
                if response.timestamp >= older_than:
                    new_buffer.append(response)
                    new_memory_usage += self._estimate_response_size(response)
                else:
                    cleared_count += 1

            self._buffer = new_buffer
            self._memory_usage_bytes = new_memory_usage

        return cleared_count

    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        async with self._lock:
            return {
                "buffer_size": len(self._buffer),
                "memory_usage_bytes": self._memory_usage_bytes,
                "memory_usage_mb": self._memory_usage_bytes / (1024 * 1024),
                "max_memory_mb": self.config.max_memory_mb,
                "buffer_capacity": self.config.buffer_size,
                "buffer_utilization": len(self._buffer) / self.config.buffer_size
                if self.config.buffer_size > 0
                else 0,
            }

    async def start(self) -> None:
        """Start the recorder (for compatibility with async context managers)."""
        pass

    async def stop(self) -> None:
        """Stop the recorder and clean up resources."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._flush_task

    def _estimate_response_size(self, response: RecordedResponse) -> int:
        """Estimate memory size of a recorded response.

        Args:
            response: The recorded response to measure

        Returns:
            Estimated size in bytes
        """
        return sys.getsizeof(response.model_dump())
