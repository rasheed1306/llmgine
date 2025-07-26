"""Base response recorder interface and data structures."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ResponseRecorderConfig(BaseModel):
    """Configuration for response recording."""

    enabled: bool = True
    max_memory_mb: int = 100
    buffer_size: int = 1000
    providers: List[str] = ["openai", "anthropic", "gemini"]
    flush_interval_seconds: float = 5.0
    storage_backend: str = "memory"  # Options: memory, file, database

    @field_validator("max_memory_mb")
    @classmethod
    def validate_max_memory(cls, v: int) -> int:
        """Ensure memory limit is reasonable."""
        if v < 1:
            raise ValueError("max_memory_mb must be at least 1 MB")
        if v > 10000:
            raise ValueError("max_memory_mb should not exceed 10 GB (10000 MB)")
        return v

    @field_validator("buffer_size")
    @classmethod
    def validate_buffer_size(cls, v: int) -> int:
        """Ensure buffer size is reasonable."""
        if v < 1:
            raise ValueError("buffer_size must be at least 1")
        if v > 1000000:
            raise ValueError("buffer_size should not exceed 1,000,000 entries")
        return v

    @field_validator("flush_interval_seconds")
    @classmethod
    def validate_flush_interval(cls, v: float) -> float:
        """Ensure flush interval is reasonable."""
        if v < 0.1:
            raise ValueError("flush_interval_seconds must be at least 0.1 seconds")
        if v > 3600:
            raise ValueError(
                "flush_interval_seconds should not exceed 1 hour (3600 seconds)"
            )
        return v


class RecordedResponse(BaseModel):
    """Data structure for a recorded response."""

    provider: str
    raw_response: Any
    request_metadata: Dict[str, Any]
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    response_id: str
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None


class ResponseRecorder(ABC):
    """Abstract base class for response recording."""

    def __init__(self, config: ResponseRecorderConfig):
        """Initialize the recorder with configuration."""
        self.config = config

    @abstractmethod
    async def record_response(
        self,
        provider: str,
        raw_response: Any,
        request_metadata: Dict[str, Any],
        session_id: str,
        response_id: str,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Record a provider response asynchronously.

        Args:
            provider: Name of the provider (openai, anthropic, gemini)
            raw_response: The complete raw response from the provider
            request_metadata: Metadata about the request (model, parameters, etc.)
            session_id: ID of the current session
            response_id: Unique identifier for this response
            processing_time_ms: Time taken to process the request in milliseconds
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered responses to storage."""
        pass

    @abstractmethod
    async def get_recorded_responses(
        self,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> List[RecordedResponse]:
        """Retrieve recorded responses with optional filtering.

        Args:
            session_id: Filter by session ID
            provider: Filter by provider name
            limit: Maximum number of responses to return

        Returns:
            List of recorded responses matching the criteria
        """
        pass

    @abstractmethod
    async def clear_old_responses(self, older_than: datetime) -> int:
        """Clear responses older than the specified datetime.

        Args:
            older_than: Clear responses with timestamp before this

        Returns:
            Number of responses cleared
        """
        pass

    @abstractmethod
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics.

        Returns:
            Dictionary with memory usage information
        """
        pass

    async def is_enabled_for_provider(self, provider: str) -> bool:
        """Check if recording is enabled for a specific provider.

        Args:
            provider: Provider name to check

        Returns:
            True if recording is enabled for this provider
        """
        return self.config.enabled and provider in self.config.providers
