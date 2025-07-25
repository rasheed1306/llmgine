# Story 2.7: Migration and Cleanup

## Status
Draft

## Story
**As a** LLMgine developer,
**I want** to migrate existing code to the new response management system and clean up deprecated code,
**so that** the codebase maintains consistency and all consumers benefit from the enhanced response handling

## Acceptance Criteria
1. All existing provider implementations migrated to new response system
2. Backward compatibility maintained through deprecation period
3. All tests updated and passing with new models
4. Documentation fully updated with migration guides
5. Deprecated code clearly marked with removal timeline
6. Performance benchmarks show no regression
7. All example code and demos updated
8. Zero breaking changes for existing API consumers

## Tasks / Subtasks
- [ ] Create migration plan (AC: 1, 2, 5)
  - [ ] Identify all code using old response models
  - [ ] Define deprecation timeline
  - [ ] Create compatibility layer design
  - [ ] Plan phased migration approach
- [ ] Implement compatibility layer (AC: 2, 8)
  - [ ] Create adapters for old to new models
  - [ ] Add deprecation warnings
  - [ ] Implement backward-compatible APIs
  - [ ] Test with existing codebases
- [ ] Migrate provider implementations (AC: 1, 3)
  - [ ] Update OpenAI provider to use new models
  - [ ] Update Anthropic provider to use new models
  - [ ] Update Gemini provider to use new models
  - [ ] Update OpenRouter provider (if exists)
  - [ ] Verify all providers work correctly
- [ ] Update test suite (AC: 3, 6)
  - [ ] Migrate unit tests to new models
  - [ ] Update integration tests
  - [ ] Add migration-specific tests
  - [ ] Run performance benchmarks
  - [ ] Ensure 95%+ coverage maintained
- [ ] Update documentation (AC: 4, 7)
  - [ ] Create migration guide
  - [ ] Update API documentation
  - [ ] Update provider documentation
  - [ ] Update all code examples
  - [ ] Update README and tutorials
- [ ] Update examples and demos (AC: 7)
  - [ ] Update single_pass_engine example
  - [ ] Update tool_chat_engine example
  - [ ] Update voice_processing_engine example
  - [ ] Update all programs/ examples
- [ ] Clean up deprecated code (AC: 5)
  - [ ] Mark deprecated functions/classes
  - [ ] Add removal timeline to docstrings
  - [ ] Create deprecation tracking document
  - [ ] Plan for future removal

## Dev Notes

### Testing
- Test file location: `tests/migration/`
- Test standards: Follow existing pytest-asyncio patterns
- Testing frameworks: pytest, pytest-asyncio, pytest-mock
- Specific requirements:
  - Test both old and new APIs work
  - Verify deprecation warnings appear
  - Test migration utilities
  - Benchmark performance
  - Test with real-world usage patterns

### Relevant Source Tree
All provider-related code needs review:
- `src/llmgine/llm/` - All LLM-related code
- `src/llmgine/engines/` - All engine implementations
- `programs/` - All example programs
- `tests/` - Entire test suite
- `docs/` - All documentation

### Architecture Notes
- Compatibility layer must not impact performance
- Deprecation warnings should be informative
- Migration should be incremental
- Consider semantic versioning implications

### Implementation Details
1. **Compatibility Layer Design**:
   ```python
   class LLMResponse:
       """Legacy response model - DEPRECATED
       
       Will be removed in version 2.0.0.
       Please migrate to provider-specific response models.
       """
       
       def __init__(self, *args, **kwargs):
           warnings.warn(
               "LLMResponse is deprecated. Use provider-specific models.",
               DeprecationWarning,
               stacklevel=2
           )
           # Compatibility implementation
   ```

2. **Migration Utilities**:
   ```python
   class ResponseMigrator:
       @staticmethod
       def to_legacy(response: BaseProviderResponse) -> LLMResponse:
           """Convert new response to legacy format"""
           
       @staticmethod
       def from_legacy(legacy: LLMResponse) -> BaseProviderResponse:
           """Convert legacy response to new format"""
   ```

3. **Phased Migration Plan**:
   - Phase 1: Add new models alongside old (current)
   - Phase 2: Update internal usage to new models
   - Phase 3: Deprecate old models with warnings
   - Phase 4: Remove old models in major version

4. **Documentation Updates**:
   - Migration guide with code examples
   - Before/after comparison
   - Benefits of migration
   - Timeline for deprecation
   - FAQ section

5. **Performance Validation**:
   ```python
   @pytest.mark.benchmark
   def test_response_performance():
       # Compare old vs new response handling
       # Ensure no significant regression
   ```

6. **Example Migration**:
   ```python
   # Old code
   response = await model.complete(prompt)
   print(response.content)
   
   # New code
   response = await model.complete(prompt)
   print(response.content)  # Still works
   print(response.provider_data.logprobs)  # New capability
   ```

7. **Deprecation Timeline**:
   - v1.x.x: New models available, old models deprecated
   - v1.x+3.x: Final warning period
   - v2.0.0: Old models removed

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