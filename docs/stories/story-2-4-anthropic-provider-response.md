# Story 2.4: Anthropic Provider Response Implementation

## Status
Draft

## Story
**As a** LLMgine developer,
**I want** comprehensive response handling for Anthropic that preserves all API-specific data,
**so that** users can access Anthropic-specific features like stop sequences, model metadata, and detailed usage information

## Acceptance Criteria
1. Deep research of Anthropic API documentation completed and documented
2. Response Recording Framework used to analyze actual API responses
3. All Anthropic response fields mapped and preserved (100% coverage)
4. Support for all Anthropic-specific features and metadata
5. Proper handling of streaming responses with SSE format
6. Type-safe models for all response variations
7. Comprehensive test coverage with real and mock responses
8. Documentation includes all discovered fields and their purposes

## Tasks / Subtasks
- [ ] Research Anthropic API comprehensively (AC: 1, 4)
  - [ ] Study official Anthropic API documentation
  - [ ] Document Messages API response format
  - [ ] Research legacy Completions API if still supported
  - [ ] Identify all optional and conditional fields
  - [ ] Document rate limit and quota information
  - [ ] Study error response formats
- [ ] Analyze actual API responses (AC: 2, 3)
  - [ ] Use Response Recording Framework to capture responses
  - [ ] Test with multiple Claude models (Claude 3, Claude 2, etc.)
  - [ ] Capture responses with different parameters
  - [ ] Test system prompts and their effects
  - [ ] Document undocumented fields found in responses
  - [ ] Create comprehensive field mapping document
- [ ] Design Anthropic-specific models (AC: 3, 4, 6)
  - [ ] Create AnthropicResponse model with all fields
  - [ ] Model message structure and roles
  - [ ] Design stop sequence handling
  - [ ] Model streaming response format
  - [ ] Handle model-specific metadata
- [ ] Implement response handling (AC: 3, 4, 5, 6)
  - [ ] Create AnthropicResponseHandler class
  - [ ] Implement SSE streaming parser
  - [ ] Handle message role validation
  - [ ] Process usage metrics correctly
  - [ ] Preserve all metadata and headers
- [ ] Test with real API (AC: 7)
  - [ ] Test all Claude model variants
  - [ ] Test with various message formats
  - [ ] Verify streaming response handling
  - [ ] Test error response parsing
  - [ ] Test rate limit handling
- [ ] Create documentation (AC: 8)
  - [ ] Document all fields and their meanings
  - [ ] Provide usage examples
  - [ ] Document Anthropic-specific features
  - [ ] Create migration guide from unified model

## Dev Notes

### Testing
- Test file location: `tests/llm/providers/anthropic/responses/`
- Test standards: Follow existing pytest-asyncio patterns
- Testing frameworks: pytest, pytest-asyncio, pytest-mock, vcr.py
- Specific requirements:
  - Use vcr.py to record real API responses
  - Test all Claude model variants
  - Test streaming SSE parsing thoroughly
  - Verify message format handling
  - Test system prompt effects on responses

### Relevant Source Tree
- `src/llmgine/llm/providers/anthropic.py` - Current Anthropic implementation
- `src/llmgine/llm/models/anthropic.py` - Anthropic model wrapper
- `tests/fixtures/anthropic/` - Existing test fixtures
- `docs/providers/anthropic.md` - Provider documentation

### Architecture Notes
- Must integrate with Response Recording Framework from Story 2.1
- Should extend base models from Story 2.2
- Handle Anthropic's SSE streaming format properly
- Consider Anthropic's unique message role system

### Implementation Details
1. **Comprehensive Field Research**:
   - Study fields like: `id`, `type`, `role`, `content`
   - Document stop reasons: `stop_reason`, `stop_sequence`
   - Map usage fields: `input_tokens`, `output_tokens`
   - Research metadata: `model`, `created_at`
   - Understand message structure and content blocks

2. **Anthropic Response Model**:
   ```python
   class AnthropicResponse(BaseProviderResponse):
       # Core fields
       id: str
       type: Literal["message"]
       role: Literal["assistant"]
       content: List[AnthropicContentBlock]
       model: str
       
       # Anthropic-specific
       stop_reason: Optional[str]
       stop_sequence: Optional[str]
       usage: AnthropicUsage
       
       # Metadata
       created_at: Optional[str]
       system_fingerprint: Optional[str]
   ```

3. **Content Block Structure**:
   ```python
   class AnthropicContentBlock(BaseModel):
       type: Literal["text"]
       text: str
       
   class AnthropicUsage(BaseModel):
       input_tokens: int
       output_tokens: int
       # Additional usage metrics if available
   ```

4. **API Response Analysis Tasks**:
   - Record responses with different max_tokens
   - Test with various temperature settings
   - Capture responses with system prompts
   - Test stop sequence behavior
   - Record streaming event types
   - Analyze error response formats

5. **Required Research Areas**:
   - Beta features and experimental fields
   - Streaming event types and formats
   - Error response structure
   - Rate limit header formats
   - Model-specific capabilities
   - Content moderation metadata

6. **Streaming Considerations**:
   ```python
   class AnthropicStreamEvent(BaseModel):
       type: str  # message_start, content_block_delta, etc.
       message: Optional[AnthropicResponse]
       delta: Optional[Dict[str, Any]]
       usage: Optional[AnthropicUsage]
   ```

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