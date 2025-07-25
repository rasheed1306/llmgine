# Story 2.6: OpenRouter Provider Response Implementation

## Status
Draft

## Story
**As a** LLMgine developer,
**I want** comprehensive response handling for OpenRouter that preserves all API-specific data,
**so that** users can access OpenRouter-specific features like model routing metadata, cost tracking, and provider fallback information

## Acceptance Criteria
1. Deep research of OpenRouter API documentation completed and documented
2. Response Recording Framework used to analyze actual API responses
3. All OpenRouter response fields mapped and preserved (100% coverage)
4. Support for all OpenRouter-specific features (routing, costs, providers)
5. Proper handling of streaming responses with OpenRouter's format
6. Type-safe models for all response variations
7. Comprehensive test coverage with real and mock responses
8. Documentation includes all discovered fields and their purposes

## Tasks / Subtasks
- [ ] Research OpenRouter API comprehensively (AC: 1, 4)
  - [ ] Study official OpenRouter API documentation
  - [ ] Document unified API response format
  - [ ] Research model routing metadata
  - [ ] Identify cost tracking fields
  - [ ] Document provider selection information
  - [ ] Study rate limiting and quota systems
- [ ] Analyze actual API responses (AC: 2, 3)
  - [ ] Use Response Recording Framework to capture responses
  - [ ] Test with multiple model providers via OpenRouter
  - [ ] Capture responses showing provider fallbacks
  - [ ] Test with different routing preferences
  - [ ] Document undocumented fields found in responses
  - [ ] Create comprehensive field mapping document
- [ ] Design OpenRouter-specific models (AC: 3, 4, 6)
  - [ ] Create OpenRouterResponse model with all fields
  - [ ] Model routing metadata structure
  - [ ] Design cost tracking models
  - [ ] Model provider selection data
  - [ ] Handle unified response format
- [ ] Implement response handling (AC: 3, 4, 5, 6)
  - [ ] Create OpenRouterResponseHandler class
  - [ ] Implement streaming response parser
  - [ ] Handle routing metadata extraction
  - [ ] Process cost information correctly
  - [ ] Preserve all metadata and headers
- [ ] Test with real API (AC: 7)
  - [ ] Test various model providers
  - [ ] Test provider fallback scenarios
  - [ ] Verify streaming response handling
  - [ ] Test error response parsing
  - [ ] Test cost calculation accuracy
- [ ] Create documentation (AC: 8)
  - [ ] Document all fields and their meanings
  - [ ] Provide usage examples
  - [ ] Document OpenRouter-specific features
  - [ ] Create migration guide from unified model

## Dev Notes

### Testing
- Test file location: `tests/llm/providers/openrouter/responses/`
- Test standards: Follow existing pytest-asyncio patterns
- Testing frameworks: pytest, pytest-asyncio, pytest-mock, vcr.py
- Specific requirements:
  - Use vcr.py to record real API responses
  - Test multiple provider routes
  - Test fallback behavior
  - Verify cost tracking accuracy
  - Test rate limit handling

### Relevant Source Tree
- `src/llmgine/llm/providers/openrouter.py` - Current OpenRouter implementation (if exists)
- `src/llmgine/llm/models/openrouter.py` - OpenRouter model wrapper (if exists)
- `tests/fixtures/openrouter/` - Test fixtures
- `docs/providers/openrouter.md` - Provider documentation

### Architecture Notes
- Must integrate with Response Recording Framework from Story 2.1
- Should extend base models from Story 2.2
- Handle OpenRouter's unified API format
- Consider multi-provider routing complexity

### Implementation Details
1. **Comprehensive Field Research**:
   - Study fields like: `id`, `model`, `object`, `created`
   - Document routing metadata: `provider`, `model_used`, `fallback_used`
   - Map cost fields: `usage`, `cost`, `pricing`
   - Research headers: `X-OpenRouter-*` headers
   - Understand provider selection logic

2. **OpenRouter Response Model**:
   ```python
   class OpenRouterResponse(BaseProviderResponse):
       # Standard OpenAI-compatible fields
       id: str
       object: str
       created: int
       model: str
       choices: List[OpenRouterChoice]
       usage: OpenRouterUsage
       
       # OpenRouter-specific
       provider: str
       model_used: str
       fallback_used: Optional[bool]
       routing_metadata: Optional[OpenRouterRoutingMetadata]
       cost_info: Optional[OpenRouterCostInfo]
   ```

3. **Routing and Cost Models**:
   ```python
   class OpenRouterRoutingMetadata(BaseModel):
       requested_model: str
       selected_provider: str
       fallback_providers: Optional[List[str]]
       routing_reason: Optional[str]
       latency_ms: Optional[int]
       
   class OpenRouterCostInfo(BaseModel):
       prompt_cost: float
       completion_cost: float
       total_cost: float
       currency: str = "USD"
       pricing_model: Optional[str]
   ```

4. **Usage Tracking**:
   ```python
   class OpenRouterUsage(BaseModel):
       prompt_tokens: int
       completion_tokens: int
       total_tokens: int
       
       # OpenRouter-specific
       cached_tokens: Optional[int]
       provider_tokens: Optional[Dict[str, int]]
   ```

5. **API Response Analysis Tasks**:
   - Record responses from different providers
   - Test with provider preferences
   - Capture fallback scenarios
   - Test with various models
   - Record streaming responses
   - Analyze cost calculation methods

6. **Required Research Areas**:
   - Provider selection algorithm
   - Fallback behavior and triggers
   - Cost calculation methodology
   - Rate limiting per provider
   - Model availability tracking
   - Provider-specific features exposed

7. **Header Analysis**:
   ```python
   class OpenRouterHeaders(BaseModel):
       x_openrouter_provider: Optional[str]
       x_openrouter_model: Optional[str]
       x_openrouter_cost: Optional[str]
       x_openrouter_cache_hit: Optional[bool]
       x_ratelimit_remaining: Optional[int]
       x_ratelimit_reset: Optional[int]
   ```

8. **Provider-Specific Considerations**:
   - OpenRouter may pass through provider-specific fields
   - Need to handle varying response formats
   - Consider caching behavior
   - Track provider availability

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