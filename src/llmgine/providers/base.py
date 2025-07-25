"""Base classes for provider implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from llmgine.unified.models import UnifiedRequest, UnifiedResponse, UnifiedStreamChunk


class ProviderAdapter(ABC):
    """Abstract base class for provider adapters."""
    
    @abstractmethod
    def to_provider_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert unified request to provider-specific format."""
        pass
    
    @abstractmethod
    def from_provider_response(self, response: Dict[str, Any]) -> UnifiedResponse:
        """Convert provider response to unified format."""
        pass
    
    @abstractmethod
    def to_provider_stream_request(self, unified: UnifiedRequest) -> Dict[str, Any]:
        """Convert unified request to provider-specific streaming format."""
        pass
    
    @abstractmethod
    def from_provider_stream_chunk(self, chunk: Dict[str, Any]) -> UnifiedStreamChunk:
        """Convert provider streaming chunk to unified format."""
        pass
