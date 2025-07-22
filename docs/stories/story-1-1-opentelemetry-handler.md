# Story 1.1: Implement Standalone Observability Module

## Story
As a platform engineer,
I want a separate observability module that doesn't depend on the message bus,
so that I can monitor all events without creating circular dependencies or performance overhead.

## Context
The current observability system uses the message bus to publish events to handlers, which creates several problems:
1. Circular dependencies - observability events could trigger more observability events
2. Performance overhead - every log operation creates additional events
3. Complexity - mixing application events with observability events

This story refactors observability into a standalone module that the message bus calls directly.

## Acceptance Criteria
1. Create standalone `ObservabilityManager` that intercepts events without using the message bus
2. Refactor existing handlers to work with the new observability module
3. Implement `OpenTelemetryHandler` for OTel integration
4. Add OpenTelemetry dependencies as optional extra in pyproject.toml
5. Update message bus to call observability module directly (not via events)
6. Ensure no observability events are published back to the message bus
7. Document the new observability architecture

## Integration Verification
- IV1: Message bus continues to function without observability-triggered events
- IV2: All events are still captured by observability handlers
- IV3: No circular dependencies between bus and observability
- IV4: Performance improves due to reduced event overhead

## Technical Details

### New Architecture Design
```python
# src/llmgine/observability/manager.py
class ObservabilityManager:
    """Standalone observability manager - no message bus dependency"""
    def __init__(self):
        self._handlers: List[ObservabilityHandler] = []
    
    def register_handler(self, handler: ObservabilityHandler):
        self._handlers.append(handler)
    
    def observe_event(self, event: Event):
        """Called directly by message bus - no event publishing"""
        for handler in self._handlers:
            handler.handle(event)

# src/llmgine/bus/bus.py (updated)
class MessageBus:
    def __init__(self, observability: Optional[ObservabilityManager] = None):
        self._observability = observability
    
    async def publish(self, event: Event):
        # Direct call to observability - no event publishing
        if self._observability:
            self._observability.observe_event(event)
        
        # Continue with normal event publishing
        await self._publish_to_handlers(event)
```

### Implementation Files
- Create: `src/llmgine/observability/manager.py` - New ObservabilityManager
- Create: `src/llmgine/observability/otel_handler.py` - OpenTelemetry handler
- Update: `src/llmgine/observability/handlers.py` - Refactor existing handlers
- Update: `src/llmgine/bus/bus.py` - Integrate ObservabilityManager
- Update: `src/llmgine/bootstrap.py` - Configure observability separately

### Key Dependencies
```toml
[project.optional-dependencies]
opentelemetry = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0", 
    "opentelemetry-exporter-otlp>=1.20.0",
    "opentelemetry-semantic-conventions>=0.41b0"
]
```

### Event Mapping Strategy (for OpenTelemetry)
- `SessionStartEvent` → Start new trace
- `CommandStartedEvent` → Start new span
- `CommandResultEvent` → End span with status
- `ToolExecuteStartedEvent` → Start child span
- `ToolExecuteResultEvent` → End child span with result
- `LLMResponseStreamStartedEvent` → Start span with streaming attribute
- `LLMResponseStreamChunkEvent` → Add events to span
- `ErrorEvent` → Record exception on span

## Testing Requirements
1. Unit tests for ObservabilityManager
2. Tests ensuring no observability events in message bus
3. Integration test with all handler types
4. Performance comparison before/after refactoring
5. Test handler registration and lifecycle