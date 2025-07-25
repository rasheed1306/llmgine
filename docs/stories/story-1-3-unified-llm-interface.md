# Story 1.3: Unified LLM Interface

## Status
Draft

## Story
As a developer using `llmgine`,
I want a unified LLM interface that standardizes interactions across all providers,
so that I can switch between providers without changing my application code.

## Context
Currently, each LLM provider (OpenAI, Anthropic, Gemini) has its own request/response format and API patterns. This creates several problems:
1. Switching providers requires significant code changes
2. Tool format differs between providers
3. No standardized way to handle provider-specific features
4. Difficult to write provider-agnostic code

This story creates a unified interface that all providers implement, with standardized contracts and adapter patterns for provider-specific features.

## Acceptance Criteria
1. Create a standardized `LLMRequest` and enhanced `LLMResponse` contract in `src/llmgine/messages/`
2. Define common fields that all providers must support (messages, model, temperature, max_tokens, tools)
3. Create provider-agnostic interfaces for model operations
4. Update all provider implementations (OpenAI, Anthropic, Gemini) to implement the unified interface
5. Maintain backward compatibility through adapter patterns
6. Create comprehensive transformation utilities for provider-specific features
7. Update all example programs to demonstrate the unified approach
8. Comprehensive test coverage for all providers using the unified interface

## Integration Verification
- IV1: All existing provider calls continue to work with current interfaces
- IV2: Provider-specific features remain accessible through extensions
- IV3: No performance degradation in request processing
- IV4: Seamless switching between providers using unified interface

## Technical Details

### Unified Contract Design
```python
# src/llmgine/messages/llm_messages.py
@dataclass
class LLMRequest(Command):
    """Standardized LLM request across all providers"""
    messages: List[Message]
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[Tool]] = None
    stream: bool = False
    
    # Provider-specific extensions
    provider_options: Optional[Dict[str, Any]] = None

@dataclass  
class LLMResponse(Event):
    """Enhanced standardized response"""
    content: str
    model: str
    usage: Optional[Usage] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    
    # Provider-specific data
    provider_data: Optional[Dict[str, Any]] = None
```

### Provider Interface
```python
# src/llmgine/llm/providers/base.py
class LLMProvider(Protocol):
    """Unified interface all providers must implement"""
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Non-streaming completion"""
        ...
    
    async def stream_complete(
        self, 
        request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Streaming completion"""
        ...
    
    def get_supported_models(self) -> List[str]:
        """List supported models"""
        ...
    
    def transform_tools(self, tools: List[Tool]) -> Any:
        """Transform tools to provider format"""
        ...
```

### Implementation Strategy
1. Create base provider class with common functionality
2. Implement adapters for each provider that handle format conversion
3. Use factory pattern for provider instantiation
4. Maintain existing provider classes with deprecation warnings
5. Create migration guide for users

## Tasks / Subtasks
- [ ] Design and implement unified contracts (AC: 1, 2)
  - [ ] Create LLMRequest with all common fields
  - [ ] Enhance LLMResponse for all provider responses
  - [ ] Define Tool and Message standardized formats
  - [ ] Write comprehensive tests for contracts
- [ ] Create provider interface and base class (AC: 3)
  - [ ] Define LLMProvider protocol
  - [ ] Implement BaseLLMProvider with common logic
  - [ ] Create provider factory
  - [ ] Write interface tests
- [ ] Update OpenAI provider (AC: 4, 5)
  - [ ] Implement unified interface
  - [ ] Create request/response adapters
  - [ ] Add backward compatibility layer
  - [ ] Update tests
- [ ] Update Anthropic provider (AC: 4, 5)
  - [ ] Implement unified interface
  - [ ] Handle tool format conversion
  - [ ] Add backward compatibility layer
  - [ ] Update tests
- [ ] Update Gemini provider (AC: 4, 5)
  - [ ] Implement unified interface
  - [ ] Handle content format differences
  - [ ] Add backward compatibility layer
  - [ ] Update tests
- [ ] Create transformation utilities (AC: 6)
  - [ ] Tool format converters for each provider
  - [ ] Message format adapters
  - [ ] Provider option handlers
  - [ ] Comprehensive test coverage
- [ ] Update example programs (AC: 7)
  - [ ] Update single_pass_engine example
  - [ ] Update tool_chat_engine example
  - [ ] Create provider switching demo
  - [ ] Update documentation
- [ ] Comprehensive testing (AC: 8)
  - [ ] Integration tests across all providers
  - [ ] Performance benchmarks
  - [ ] Backward compatibility tests
  - [ ] Migration path tests

## Dev Notes
- Maintain backward compatibility is critical - existing code must continue working
- Use deprecation warnings to guide users to new interface
- Performance must not degrade - benchmark before/after
- Provider-specific features should be accessible but clearly marked
- Follow existing code patterns for consistency
- Consider feature flags for gradual rollout

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-25 | 1.0 | Initial story creation | Bob (SM) |

## Dev Agent Record

### Agent Model Used
- Model: [To be populated]

### Debug Log References
- Session: [To be populated]

### Completion Notes List
- [To be populated]

### File List
- [To be populated]

## QA Results
- [To be populated]