# Story 2.2: Base Response Models Redesign

## Status
Draft

## Story
**As a** LLMgine developer,
**I want** to redesign the base response models to support provider-specific data preservation,
**so that** we can maintain backward compatibility while enabling rich provider-specific features

## Acceptance Criteria
1. New base response models support generic provider-specific data fields
2. Backward compatibility maintained with existing unified interface
3. Type safety preserved through proper Pydantic model inheritance
4. Clear separation between unified fields and provider-specific extensions
5. Support for both streaming and non-streaming response patterns
6. Extensible design allowing easy addition of new providers
7. Zero runtime overhead for applications not using provider-specific data
8. Migration path clearly defined for existing code

## Tasks / Subtasks
- [ ] Analyze current response model architecture (AC: 1, 2)
  - [ ] Document existing LLMResponse and related models
  - [ ] Identify all consumers of response models
  - [ ] Map current field usage across the codebase
- [ ] Design new base response architecture (AC: 1, 3, 4, 6)
  - [ ] Create base response model with extension points
  - [ ] Design provider-specific data containers
  - [ ] Define inheritance hierarchy for provider models
  - [ ] Plan for streaming response handling
- [ ] Implement base response models (AC: 3, 4, 5, 7)
  - [ ] Create BaseProviderResponse with common fields
  - [ ] Implement ProviderSpecificData container
  - [ ] Add support for streaming response metadata
  - [ ] Ensure zero-overhead for standard usage
- [ ] Create compatibility layer (AC: 2, 8)
  - [ ] Implement adapter for existing LLMResponse
  - [ ] Add deprecation warnings where appropriate
  - [ ] Create migration utilities
- [ ] Update type definitions (AC: 3, 6)
  - [ ] Define generic types for provider responses
  - [ ] Update protocol definitions
  - [ ] Ensure mypy compliance in strict mode

## Dev Notes

### Testing
- Test file location: `tests/llm/models/base_response/`
- Test standards: Follow existing pytest-asyncio patterns
- Testing frameworks: pytest, pytest-asyncio, pytest-mock
- Specific requirements:
  - Test backward compatibility thoroughly
  - Verify type safety with mypy tests
  - Test serialization/deserialization
  - Validate zero overhead claims with benchmarks
  - Test with all existing provider implementations

### Relevant Source Tree
Key files that need analysis and potential modification:
- `src/llmgine/llm/responses.py` - Current response models
- `src/llmgine/llm/models/base.py` - Base model definitions
- `src/llmgine/llm/providers/` - All provider implementations
- `src/llmgine/messages/llm.py` - LLM-related messages

### Architecture Notes
- The redesign must maintain the current message-passing architecture
- Provider-specific data should be accessible but not required
- Consider using Pydantic's discriminated unions for provider types
- Streaming responses need special consideration for metadata accumulation

### Implementation Details
1. **Base Response Structure**:
   ```python
   class BaseProviderResponse(BaseModel):
       # Common fields across all providers
       content: str
       model: str
       usage: Optional[Usage]
       
       # Extension point for provider data
       provider_data: Optional[ProviderSpecificData] = None
       
       # Backward compatibility method
       def to_legacy_response(self) -> LLMResponse:
           """Convert to legacy LLMResponse format"""
   ```

2. **Provider-Specific Container**:
   ```python
   class ProviderSpecificData(BaseModel, extra="allow"):
       provider: str
       raw_response: Optional[Dict[str, Any]] = None
       
       class Config:
           # Allow arbitrary fields for extensibility
           extra = "allow"
   ```

3. **Migration Strategy**:
   - Phase 1: Add new models alongside existing ones
   - Phase 2: Update providers to use new models internally
   - Phase 3: Deprecate old models with migration timeline
   - Phase 4: Remove deprecated models in major version

4. **Performance Considerations**:
   - Use lazy loading for provider-specific data
   - Implement __slots__ for frequently used models
   - Consider caching for repeated conversions

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-01-25 | 1.0 | Initial story creation | System |

## Dev Agent Record
### Agent Model Used
(To be populated by dev agent)

### Debug Log References
(To be populated by dev agent)

### Completion Notes List
(To be populated by dev agent)

### File List
(To be populated by dev agent)

## QA Results
(To be populated by QA agent)