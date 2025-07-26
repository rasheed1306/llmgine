"""Events for response recording system."""

from dataclasses import dataclass, field
from typing import Optional

from llmgine.messages.events import Event


@dataclass
class ResponseRecorded(Event):
    """Event emitted when a response is successfully recorded."""

    provider: str = field(default="")
    response_id: str = field(default="")
    processing_time_ms: Optional[float] = field(default=None)


@dataclass
class ResponseRecordingFailed(Event):
    """Event emitted when response recording fails."""

    provider: str = field(default="")
    response_id: str = field(default="")
    error: str = field(default="")


@dataclass
class ResponseRecorderMemoryWarning(Event):
    """Event emitted when recorder memory usage is high."""

    memory_usage_mb: float = field(default=0.0)
    max_memory_mb: float = field(default=0.0)
    buffer_utilization: float = field(default=0.0)


@dataclass
class ResponseRecorderFlushed(Event):
    """Event emitted when recorder flushes buffered responses."""

    responses_flushed: int = field(default=0)
    flush_duration_ms: float = field(default=0.0)
