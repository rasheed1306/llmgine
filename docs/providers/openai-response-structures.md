# OpenAI Response Structures Documentation

This document provides comprehensive details about OpenAI API response structures based on validated syntax testing with o4-mini-2025-04-16 and gpt-4o-mini-2024-07-18 models.

## Table of Contents
1. [Standard Chat Completion Response](#standard-chat-completion-response)
2. [Model-Specific Features](#model-specific-features)
3. [Tool Calling Responses](#tool-calling-responses)
4. [Streaming Responses](#streaming-responses)
5. [Error Responses](#error-responses)
6. [Field Descriptions](#field-descriptions)

## Standard Chat Completion Response

### Basic Structure
```json
{
  "id": "chatcmpl-XXXXX",
  "object": "chat.completion",
  "created": 1753493884,
  "model": "gpt-4o-mini-2024-07-18",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?",
        "refusal": null,
        "annotations": []
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 9,
    "total_tokens": 17,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "audio_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0,
      "audio_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    }
  },
  "service_tier": "default",
  "system_fingerprint": "fp_XXXXX"
}
```

## Model-Specific Features

### o4-mini-2025-04-16 Specific Features

1. **Parameter Differences**:
   - Uses `max_completion_tokens` instead of `max_tokens`
   - Supports `reasoning_effort` parameter ("low", "medium", "high")

2. **Reasoning Tokens**:
   When `reasoning_effort` is used, the response includes reasoning tokens in the usage details:
   ```json
   "usage": {
     "completion_tokens_details": {
       "reasoning_tokens": 50
     }
   }
   ```

### gpt-4o-mini-2024-07-18 Specific Features

1. **Logprobs Support**:
   When `logprobs=true` and `top_logprobs=N` are specified:
   ```json
   "choices": [{
     "message": {...},
     "logprobs": {
       "content": [
         {
           "token": "Hello",
           "logprob": -0.0009119403548538685,
           "bytes": [72, 101, 108, 108, 111],
           "top_logprobs": [
             {
               "token": "Hello",
               "logprob": -0.0009119403548538685,
               "bytes": [72, 101, 108, 108, 111]
             },
             {
               "token": "Hi",
               "logprob": -7.000911712646484,
               "bytes": [72, 105]
             }
           ]
         }
       ],
       "refusal": null
     }
   }]
   ```

## Tool Calling Responses

### Single Tool Call
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_XXXXX",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"location\":\"Paris\"}"
          }
        }
      ]
    },
    "finish_reason": "tool_calls"
  }]
}
```

### Multiple/Parallel Tool Calls
When `parallel_tool_calls=true`, multiple tools can be called in a single response:
```json
{
  "tool_calls": [
    {
      "id": "call_1",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"location\":\"Paris\"}"
      }
    },
    {
      "id": "call_2", 
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"location\":\"London\"}"
      }
    }
  ]
}
```

## Streaming Responses

### Chunk Structure
```json
{
  "id": "chatcmpl-XXXXX",
  "object": "chat.completion.chunk",
  "created": 1753493889,
  "model": "gpt-4o-mini-2024-07-18",
  "choices": [
    {
      "index": 0,
      "delta": {
        "content": "Hello"
      },
      "finish_reason": null
    }
  ]
}
```

### Final Chunk with Usage
The last chunk includes usage information:
```json
{
  "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 10,
    "total_tokens": 18
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "message": "Unsupported parameter: 'invalid_parameter' is not supported with this model",
    "type": "invalid_request_error",
    "param": "invalid_parameter",
    "code": "unsupported_parameter"
  }
}
```

## Field Descriptions

### Top-Level Fields
- `id`: Unique identifier for the completion (format: "chatcmpl-XXXXX")
- `object`: Type of object ("chat.completion" or "chat.completion.chunk")
- `created`: Unix timestamp of creation
- `model`: Model identifier used for the completion
- `service_tier`: Service tier used (e.g., "default")
- `system_fingerprint`: System configuration identifier

### Choice Fields
- `index`: Position in the choices array (0-based)
- `message`: Complete message object (non-streaming)
- `delta`: Incremental content (streaming only)
- `finish_reason`: Reason for completion ("stop", "length", "tool_calls", etc.)
- `logprobs`: Log probability information (when requested)

### Message Fields
- `role`: Message role ("assistant", "user", "system", "tool")
- `content`: Text content of the message (null for tool calls)
- `tool_calls`: Array of tool call objects
- `refusal`: Content refusal information (usually null)
- `annotations`: Additional annotations array

### Usage Fields
- `prompt_tokens`: Tokens used in the prompt
- `completion_tokens`: Tokens generated in the completion
- `total_tokens`: Sum of prompt and completion tokens
- `prompt_tokens_details`: Detailed prompt token breakdown
- `completion_tokens_details`: Detailed completion token breakdown

### Tool Call Fields
- `id`: Unique identifier for the tool call
- `type`: Type of tool ("function")
- `function.name`: Name of the function to call
- `function.arguments`: JSON string of function arguments

## Usage Examples

### Basic Completion (gpt-4o-mini)
```python
response = await client.chat_completion(
    model="gpt-4o-mini-2024-07-18",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=10
)
```

### Basic Completion (o4-mini)
```python
response = await client.chat_completion(
    model="o4-mini-2025-04-16",
    messages=[{"role": "user", "content": "Hello"}],
    max_completion_tokens=10  # Note: different parameter name
)
```

### With Reasoning (o4-mini)
```python
response = await client.chat_completion(
    model="o4-mini-2025-04-16",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    reasoning_effort="high",
    max_completion_tokens=50
)
# Access reasoning tokens: response["usage"]["completion_tokens_details"]["reasoning_tokens"]
```

### With Logprobs (gpt-4o-mini)
```python
response = await client.chat_completion(
    model="gpt-4o-mini-2024-07-18",
    messages=[{"role": "user", "content": "Hello"}],
    logprobs=True,
    top_logprobs=3,
    max_tokens=5
)
# Access logprobs: response["choices"][0]["logprobs"]
```

### Tool Calling
```python
response = await client.chat_completion(
    model="gpt-4o-mini-2024-07-18",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[weather_tool_schema],
    tool_choice="auto"
)
# Check if tool was called: response["choices"][0]["finish_reason"] == "tool_calls"
```

## Important Notes

1. **Model Compatibility**: Always check model-specific parameter requirements (e.g., `max_tokens` vs `max_completion_tokens`)
2. **Field Presence**: Some fields like `logprobs` or `tool_calls` are only present when relevant
3. **Streaming Aggregation**: When processing streaming responses, aggregate chunks to build the complete response
4. **Error Handling**: Always validate response structure before accessing nested fields
5. **Token Counting**: Different models may have different token counting methods and limits