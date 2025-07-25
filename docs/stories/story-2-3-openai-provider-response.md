# Story 2.3: OpenAI Provider Response Implementation

## Status
Draft

## Story
**As a** LLMgine developer,
**I want** comprehensive response handling for OpenAI that preserves all API-specific data,
**so that** users can access OpenAI-specific features like logprobs, function calls, and detailed usage metrics

## Acceptance Criteria
1. Deep research of OpenAI API documentation completed and documented
2. Response Recording Framework used to analyze actual API responses
3. All OpenAI response fields mapped and preserved (100% coverage)
4. Support for all OpenAI-specific features (logprobs, function calls, etc.)
5. Proper handling of streaming responses with incremental data
6. Type-safe models for all response variations
7. Comprehensive test coverage with real and mock responses
8. Documentation includes all discovered fields and their purposes

## Tasks / Subtasks
- [ ] Research OpenAI API comprehensively (AC: 1, 4)
  - [ ] Study official OpenAI API documentation
  - [ ] Document all response formats (chat, completion, embedding)
  - [ ] Identify all optional and conditional fields
  - [ ] Research beta features and experimental fields
  - [ ] Document rate limit headers and metadata
- [ ] Analyze actual API responses (AC: 2, 3)
  - [ ] Use Response Recording Framework to capture responses
  - [ ] Test with multiple models (GPT-4, GPT-3.5, etc.)
  - [ ] Capture responses with different parameters
  - [ ] Document undocumented fields found in responses
  - [ ] Create comprehensive field mapping document
- [ ] Design OpenAI-specific models (AC: 3, 4, 6)
  - [ ] Create OpenAIResponse model with all fields
  - [ ] Model function call responses
  - [ ] Model logprobs structure
  - [ ] Design streaming response models
  - [ ] Handle model-specific response variations
- [ ] Implement response handling (AC: 3, 4, 5, 6)
  - [ ] Create OpenAIResponseHandler class
  - [ ] Implement streaming response aggregation
  - [ ] Handle function call parsing
  - [ ] Process logprobs data correctly
  - [ ] Preserve all metadata and headers
- [ ] Test with real API (AC: 7)
  - [ ] Test all model variants
  - [ ] Test with various parameters
  - [ ] Verify streaming response handling
  - [ ] Test error response parsing
  - [ ] Benchmark performance impact
- [ ] Create documentation (AC: 8)
  - [ ] Document all fields and their meanings
  - [ ] Provide usage examples
  - [ ] Document version differences
  - [ ] Create migration guide from unified model

## Dev Notes

### Testing
- Test file location: `tests/llm/providers/openai/responses/`
- Test standards: Follow existing pytest-asyncio patterns
- Testing frameworks: pytest, pytest-asyncio, pytest-mock, vcr.py
- Specific requirements:
  - Use vcr.py to record real API responses
  - Test all model variants (gpt-4, gpt-3.5-turbo, etc.)
  - Test streaming and non-streaming modes
  - Verify all optional fields are captured
  - Test error responses and edge cases

### Relevant Source Tree
- `src/llmgine/llm/providers/openai.py` - Current OpenAI implementation
- `src/llmgine/llm/models/openai.py` - OpenAI model wrapper
- `tests/fixtures/openai/` - Existing test fixtures
- `docs/providers/openai.md` - Provider documentation

### Architecture Notes
- Must integrate with Response Recording Framework from Story 2.1
- Should extend base models from Story 2.2
- Preserve streaming architecture for real-time responses
- Consider token-level streaming for advanced use cases

### Implementation Details
1. **Comprehensive Field Research**:
   - Study fields like: `system_fingerprint`, `logprobs`, `finish_reason`
   - Document rate limit headers: `x-ratelimit-*`
   - Map all usage fields: `prompt_tokens`, `completion_tokens`, `total_tokens`
   - Research function calling: `function_call`, `tool_calls`

2. **OpenAI Response Model**:
   ```python
   class OpenAIResponse(BaseProviderResponse):
       # Standard fields
       id: str
       object: str
       created: int
       model: str
       
       # Choice-specific fields
       choices: List[OpenAIChoice]
       
       # OpenAI-specific
       system_fingerprint: Optional[str]
       usage: OpenAIUsage
       
       # Rate limit metadata
       rate_limit_headers: Optional[Dict[str, str]]
   ```

3. **Advanced Features**:
   ```python
   class OpenAIChoice(BaseModel):
       index: int
       message: OpenAIMessage
       logprobs: Optional[OpenAILogprobs]
       finish_reason: str
       
   class OpenAILogprobs(BaseModel):
       tokens: List[str]
       token_logprobs: List[float]
       top_logprobs: List[Dict[str, float]]
       text_offset: List[int]
   ```

4. **API Response Analysis Tasks**:
   - Record responses with different temperature settings
   - Capture responses with max_tokens variations
   - Test with and without logprobs
   - Record function calling responses
   - Capture streaming chunks

5. **Required Research Areas**:
   - Beta features in API headers
   - Undocumented response fields
   - Model-specific response differences
   - Error response formats
   - Streaming chunk formats

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