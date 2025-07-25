# Provider Architecture

## Overview

LLMgine uses a modular provider architecture that separates provider-specific implementations from the unified interface. This design enables easy addition of new providers while maintaining a consistent API across all LLM backends.

## Architecture Components

### 1. Unified Models (`src/llmgine/unified/models.py`)

Defines the common data structures used across all providers:

- `UnifiedMessage` - Standard message format
- `UnifiedMessageRole` - Role enumeration (system, user, assistant, tool)
- `UnifiedRequest` - Common request parameters
- `UnifiedResponse` - Provider-agnostic response format
- `UnifiedStreamResponse` - Streaming response format

### 2. Provider Interface (`src/llmgine/providers/base.py`)

Abstract base class that all providers must implement:

```python
class BaseProvider(ABC):
    @abstractmethod
    async def complete(self, request: UnifiedRequest) -> UnifiedResponse:
        """Synchronous completion"""
        
    @abstractmethod
    async def stream(self, request: UnifiedRequest) -> AsyncIterator[UnifiedStreamResponse]:
        """Streaming completion"""
```

### 3. Provider Implementations

Each provider lives in its own module under `src/llmgine/providers/`:

```
providers/
├── openai/
│   ├── __init__.py
│   ├── client.py      # OpenAI-specific client
│   ├── models.py      # OpenAI-specific models
│   └── provider.py    # OpenAI provider implementation
├── anthropic/
│   ├── __init__.py
│   ├── client.py      # Anthropic-specific client
│   ├── models.py      # Anthropic-specific models
│   └── provider.py    # Anthropic provider implementation
└── gemini/
    ├── __init__.py
    ├── client.py      # Gemini-specific client
    ├── models.py      # Gemini-specific models
    └── provider.py    # Gemini provider implementation
```

### 4. Orchestrator Layer (`src/llmgine/orchestrator/`)

Manages provider selection and routing:

- Selects appropriate provider based on model name
- Handles provider initialization
- Routes requests to correct provider
- Manages provider lifecycle

## Data Flow

1. **Request Creation**: User creates a `UnifiedRequest` with messages and parameters
2. **Provider Selection**: Orchestrator determines provider from model name
3. **Translation**: Provider translates unified request to provider-specific format
4. **API Call**: Provider makes API call using its native client
5. **Response Translation**: Provider converts native response to `UnifiedResponse`
6. **Return**: Unified response returned to user

## Adding a New Provider

To add a new provider:

1. Create a new module under `src/llmgine/providers/<provider_name>/`
2. Implement the `BaseProvider` interface
3. Define provider-specific models if needed
4. Create translation logic between unified and native formats
5. Register the provider in the orchestrator

Example structure:
```python
# providers/newprovider/provider.py
from llmgine.providers.base import BaseProvider
from llmgine.unified.models import UnifiedRequest, UnifiedResponse

class NewProvider(BaseProvider):
    async def complete(self, request: UnifiedRequest) -> UnifiedResponse:
        # Translate to provider format
        native_request = self._to_native_request(request)
        
        # Make API call
        native_response = await self.client.complete(native_request)
        
        # Translate response
        return self._to_unified_response(native_response)
```

## Benefits

1. **Modularity**: Each provider is self-contained
2. **Consistency**: Unified interface across all providers
3. **Extensibility**: Easy to add new providers
4. **Maintainability**: Provider-specific code is isolated
5. **Type Safety**: Strong typing throughout

## Migration from Legacy Architecture

The legacy architecture used a single `UnifiedLLMClient` with provider-specific logic mixed together. The new architecture:

- Separates concerns between providers
- Removes tight coupling
- Enables parallel development of providers
- Simplifies testing of individual providers

See the [migration guide](../migration/observability-migration-guide.md) for details on upgrading from the legacy system.