# Anthropic Response Handling Documentation

## Overview

This document describes the comprehensive response handling implementation for Anthropic's Claude models in the LLMgine framework. The implementation validates and processes all response types from Claude models:
- **claude-3-5-haiku-20241022** - Used for all normal operations (fast, efficient)
- **claude-sonnet-4-20250514** - Used for testing thinking mode syntax (supports extended reasoning)

## Response Structure

### Standard Message Response

```json
{
  "id": "msg_01ABC...",
  "type": "message",
  "role": "assistant",
  "model": "claude-3-5-sonnet-20241022",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "service_tier": "standard"
  }
}
```

### Content Block Types

#### Text Content
```json
{
  "type": "text",
  "text": "This is the response text"
}
```

#### Tool Use Content
```json
{
  "type": "tool_use",
  "id": "toolu_01ABC...",
  "name": "get_weather",
  "input": {
    "location": "Paris"
  }
}
```

#### Thinking Content (Claude 4 only)
```json
{
  "type": "thinking",
  "thinking": "I need to calculate 25 * 17. Let me work through this step by step..."
}
```

### Stop Reasons

- `end_turn` - Natural completion of response
- `stop_sequence` - Hit a stop sequence
- `max_tokens` - Reached token limit
- `tool_use` - Calling a tool

### Streaming Response Events

1. **message_start** - Initial message metadata
2. **content_block_start** - Beginning of content block
3. **content_block_delta** - Incremental content
4. **content_block_stop** - End of content block
5. **message_delta** - Updates to message (stop_reason, usage)
6. **message_stop** - End of message
7. **ping** - Keep-alive event

### Error Response Format

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "invalid_parameter: Extra inputs are not permitted"
  }
}
```

## Response Validator

The `AnthropicResponseValidator` class provides methods to:

### 1. Validate Message Response
```python
from llmgine.providers.anthropic import AnthropicResponseValidator

# Validate a standard response
response = {...}  # Anthropic API response
is_valid = AnthropicResponseValidator.validate_message_response(response)
```

### 2. Validate Streaming Chunks
```python
# Validate individual streaming chunks
chunk = {"type": "content_block_delta", ...}
is_valid = AnthropicResponseValidator.validate_streaming_chunk(chunk)
```

### 3. Aggregate Streaming Chunks
```python
# Convert streaming chunks to complete response
chunks = [...]  # List of streaming chunks
complete_response = AnthropicResponseValidator.aggregate_streaming_chunks(chunks)
```

### 4. Extract Tool Calls
```python
# Extract tool calls from response
tool_calls = AnthropicResponseValidator.extract_tool_calls(response)
# Returns: [{"id": "...", "name": "get_weather", "input": {...}}]
```

### 5. Extract Content Blocks
```python
# Extract text content
text_blocks = AnthropicResponseValidator.extract_content_blocks(response, "text")
# Returns: ["Hello!", "How can I help?"]

# Extract tool use blocks
tool_blocks = AnthropicResponseValidator.extract_content_blocks(response, "tool_use")
```

## Unified Response Integration

The `UnifiedResponse.from_anthropic()` method handles:

1. **Multi-block content** - Combines text and tool use blocks
2. **Error responses** - Converts to unified error format
3. **Usage tracking** - Maps Anthropic's token fields
4. **Stop reasons** - Preserves completion reasons

Example usage:
```python
from llmgine.unified.models import UnifiedResponse

# Convert Anthropic response to unified format
anthropic_response = {...}  # From API
unified = UnifiedResponse.from_anthropic(anthropic_response)

print(unified.content)       # Combined text/tool content
print(unified.usage)         # Token usage with Anthropic-specific fields
print(unified.finish_reason) # Stop reason
```

## Adapter Implementation

The `AnthropicAdapter` handles:

### Request Conversion
- Extracts system messages to separate `system` field
- Converts content blocks (text, images)
- Maps unified parameters to Anthropic format

### Response Conversion
- Uses `UnifiedResponse.from_anthropic()`
- Preserves all Anthropic-specific fields in `raw_response`

### Streaming Support
- Processes SSE events incrementally
- Extracts text from `content_block_delta` events
- Tracks completion via `message_delta` and `message_stop`

## Model-Specific Behaviors

### Claude-3-5-Haiku-20241022
- Primary model for all normal operations
- Fastest responses with excellent capability
- Supports all standard features (tools, system prompts, stop sequences)
- Optimal for high-volume use cases
- Does NOT support thinking mode

### Claude-Sonnet-4-20250514
- Used specifically for testing thinking mode syntax
- Supports extended thinking with `thinking` parameter
- Requires beta header: `anthropic-beta: interleaved-thinking-2025-05-14`
- Can interleave thinking between tool calls
- Higher token usage due to thinking budget

## Usage Examples

### Basic Text Generation (Haiku)
```python
from llmgine.providers.anthropic import AnthropicClient

async with AnthropicClient() as client:
    response = await client.messages(
        model="claude-3-5-haiku-20241022",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=100
    )
```

### Thinking Mode (Claude 4 Sonnet)
```python
async with AnthropicClient() as client:
    # Add beta header for thinking mode
    client._client.headers["anthropic-beta"] = "interleaved-thinking-2025-05-14"
    
    response = await client.messages(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "What is 25 * 17?"}],
        thinking={"type": "enabled", "budget_tokens": 1000},
        max_tokens=100
    )
```

### With System Prompt
```python
response = await client.messages(
    model="claude-3-5-haiku-20241022",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Who are you?"}],
    max_tokens=100
)
```

### Tool Calling
```python
response = await client.messages(
    model="claude-3-5-haiku-20241022",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[{
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }],
    max_tokens=100
)
```

### Streaming
```python
async for chunk in client.messages_stream(
    model="claude-3-5-haiku-20241022",
    messages=[{"role": "user", "content": "Count to 5"}],
    max_tokens=50
):
    if chunk["type"] == "content_block_delta":
        print(chunk["delta"]["text"], end="")
```

## Error Handling

Common error types:
- `invalid_request_error` - Bad parameters
- `authentication_error` - Invalid API key
- `rate_limit_error` - Too many requests
- `api_error` - Server-side issues

Example error handling:
```python
try:
    response = await client.messages(...)
except RuntimeError as e:
    # Parse error from exception message
    if "invalid_request_error" in str(e):
        # Handle invalid request
        pass
```

## Best Practices

1. **Always validate responses** before processing
2. **Handle multi-block content** properly (text + tools)
3. **Track token usage** for cost management
4. **Use appropriate stop sequences** for your use case
5. **Implement proper error handling** for all API calls
6. **Aggregate streaming chunks** correctly for complete responses

## Testing

The implementation includes comprehensive syntax validation tests covering:
- All three Claude models
- Basic responses
- System prompts
- Stop sequences
- Tool calling (single and multiple)
- Multi-turn conversations
- Streaming responses
- Error cases
- Long responses
- Forced tool calling

Test results are stored in `tests/providers/response/stored_responses/` for analysis.