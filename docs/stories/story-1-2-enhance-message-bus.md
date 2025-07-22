# Story 1.2: Enhance Message Bus Robustness

## Story
As a platform engineer,
I want a production-grade message bus with error recovery and performance guarantees,
so that I can build reliable applications that scale under load.

## Context
The current message bus implementation is functional but lacks production-grade robustness features. For a framework promising production readiness, the bus needs error recovery, backpressure handling, performance guarantees, and comprehensive monitoring.

## Acceptance Criteria
1. Implement error recovery mechanisms for handler failures
2. Add backpressure handling to prevent queue overflow
3. Create dead letter queue for unprocessable events
4. Add circuit breaker pattern for failing handlers
5. Implement event prioritization and queue management
6. Add comprehensive logging and metrics for bus operations
7. Create performance benchmarks targeting 10k events/sec

## Integration Verification
- IV1: Existing handler registration and execution continues to work
- IV2: No performance degradation for normal workloads
- IV3: Graceful degradation under extreme load
- IV4: All existing tests continue to pass

## Technical Details

### Error Recovery Architecture
```python
# src/llmgine/bus/resilience.py
class ResilientMessageBus(MessageBus):
    def __init__(self, max_retries: int = 3, retry_delay: float = 0.1):
        super().__init__()
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._dead_letter_queue: asyncio.Queue = asyncio.Queue()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    async def execute_with_retry(self, command: Command):
        """Execute command with exponential backoff retry"""
        for attempt in range(self._max_retries):
            try:
                return await self.execute(command)
            except Exception as e:
                if attempt == self._max_retries - 1:
                    await self._dead_letter_queue.put((command, e))
                    raise
                await asyncio.sleep(self._retry_delay * (2 ** attempt))
```

### Backpressure Handling
```python
class BoundedEventQueue:
    def __init__(self, max_size: int = 10000, high_water_mark: float = 0.8):
        self._queue = asyncio.Queue(maxsize=max_size)
        self._high_water_mark = int(max_size * high_water_mark)
        self._backpressure_active = False
    
    async def put(self, event: Event, priority: int = 0):
        if self._queue.qsize() > self._high_water_mark:
            self._backpressure_active = True
            # Apply backpressure strategies
```

### Performance Requirements
- **Throughput**: 10,000+ events/second sustained
- **Latency**: <10ms p99 for event publishing
- **Memory**: Bounded memory usage under load
- **CPU**: Linear scaling with event rate

### Monitoring Metrics
```python
# Key metrics to expose:
- events_published_total (counter)
- events_processed_total (counter)
- events_failed_total (counter)
- event_processing_duration_seconds (histogram)
- queue_size (gauge)
- backpressure_active (gauge)
- circuit_breaker_state (gauge per handler)
- dead_letter_queue_size (gauge)
```

### Implementation Files
- Create: `src/llmgine/bus/resilience.py` - Error recovery mechanisms
- Create: `src/llmgine/bus/backpressure.py` - Backpressure handling
- Create: `src/llmgine/bus/metrics.py` - Performance monitoring
- Update: `src/llmgine/bus/bus.py` - Integrate resilience features
- Create: `benchmarks/bus_performance.py` - Performance benchmarks

## Testing Requirements
1. Unit tests for all resilience mechanisms
2. Integration tests simulating failures
3. Performance benchmarks with various loads
4. Chaos testing with random failures
5. Memory leak tests under sustained load
6. Circuit breaker state transition tests