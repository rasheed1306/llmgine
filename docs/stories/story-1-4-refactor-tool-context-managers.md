# Story 1.4: Refactor Tool and Context Managers

## Status
Backlog

## Story
As a developer using `llmgine`,
I want tool and context managers that work seamlessly with the unified LLM interface,
so that I have a consistent experience across all components.

## Context
After implementing the unified LLM interface in Story 1.3, the tool and context managers need to be updated to work with the standardized contracts. This ensures consistency across the entire llmgine ecosystem and makes it easier to build provider-agnostic applications.

## Acceptance Criteria
1. Update ToolManager to work with standardized tool schemas
2. Ensure Context Store uses unified message formats
3. Create adapters for provider-specific tool formats
4. Test integration between unified interface and tool/context systems
5. Update all tool registration APIs to use standardized formats
6. Ensure tool execution results follow unified response patterns
7. Create migration guide for existing tool implementations

## Integration Verification
- IV1: Existing tools continue to work without modification
- IV2: New tools can be registered once and work with all providers
- IV3: Context store correctly handles messages from all providers
- IV4: No performance degradation in tool execution

## Technical Details

### Standardized Tool Format
```python
@dataclass
class Tool:
    """Unified tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    required: List[str] = field(default_factory=list)
    
    # Provider-specific metadata
    provider_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ToolCall:
    """Standardized tool call from LLM"""
    id: str
    name: str
    arguments: Dict[str, Any]
    
@dataclass
class ToolResult:
    """Standardized tool execution result"""
    tool_call_id: str
    content: str
    error: Optional[str] = None
```

### Updated ToolManager Interface
```python
class ToolManager:
    """Enhanced tool manager with unified interface support"""
    
    def register_tool(
        self, 
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tool:
        """Register function as tool with auto-schema generation"""
        ...
    
    async def execute_tool_call(
        self, 
        tool_call: ToolCall
    ) -> ToolResult:
        """Execute tool with standardized input/output"""
        ...
    
    def get_tools_for_provider(
        self, 
        provider: str
    ) -> List[Any]:
        """Get tools in provider-specific format"""
        ...
```

### Context Store Updates
```python
class ContextStore:
    """Updated context store with unified message support"""
    
    async def add_message(
        self, 
        session_id: str, 
        message: Message
    ) -> None:
        """Add unified message format"""
        ...
    
    async def add_llm_exchange(
        self,
        session_id: str,
        request: LLMRequest,
        response: LLMResponse
    ) -> None:
        """Add complete LLM exchange"""
        ...
```

## Tasks / Subtasks
- [ ] Update Tool data structures (AC: 1, 5)
  - [ ] Create unified Tool, ToolCall, ToolResult classes
  - [ ] Update existing tool schemas
  - [ ] Write migration utilities
  - [ ] Add comprehensive tests
- [ ] Refactor ToolManager (AC: 1, 2, 6)
  - [ ] Update registration methods
  - [ ] Implement unified execution
  - [ ] Add provider transformation layer
  - [ ] Update event publishing
- [ ] Create provider adapters (AC: 3)
  - [ ] OpenAI tool format adapter
  - [ ] Anthropic tool format adapter
  - [ ] Gemini function calling adapter
  - [ ] Test all adapters
- [ ] Update Context Store (AC: 2)
  - [ ] Add unified message support
  - [ ] Create LLM exchange tracking
  - [ ] Update storage format
  - [ ] Migrate existing data
- [ ] Integration testing (AC: 4)
  - [ ] Test tool execution with all providers
  - [ ] Test context persistence
  - [ ] Performance benchmarks
  - [ ] End-to-end scenarios
- [ ] Documentation (AC: 7)
  - [ ] Migration guide for tools
  - [ ] Updated examples
  - [ ] API documentation
  - [ ] Best practices guide

## Dev Notes
- This story depends on Story 1.3 (Unified LLM Interface) being completed first
- Backward compatibility is crucial - existing tools must continue working
- Consider using adapter pattern for provider-specific transformations
- Performance testing is important - tool execution is often in hot path
- Follow existing patterns in llmgine for consistency

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