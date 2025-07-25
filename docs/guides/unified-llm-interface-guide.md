# Unified LLM Interface

The Unified LLM Interface provides a single, consistent API for interacting with multiple LLM providers (OpenAI, Anthropic, and Google Gemini). Switch between providers by simply changing the model name - no other code changes required!

## Features

- **Unified API**: Same interface for all providers
- **Automatic provider detection**: Detects provider from model name
- **Streaming support**: Consistent streaming interface across providers
- **Multimodal support**: Handle text and images uniformly
- **Direct HTTP calls**: No SDK dependencies, uses httpx
- **Type safety**: Full type hints with Pydantic models

## Installation

```bash
# Install llmgine with development dependencies
uv pip install -e ".[dev]"

# Set your API keys
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export GEMINI_API_KEY=your-gemini-key
```

## Quick Start

```python
import asyncio
from llmgine.unified import UnifiedLLMClient, UnifiedMessage, UnifiedRequest

async def main():
    async with UnifiedLLMClient() as client:
        # Create a request - just change the model to switch providers!
        request = UnifiedRequest(
            model="gpt-4o-mini",  # or "claude-3-5-sonnet-20241022" or "gemini-2.0-flash"
            messages=[
                UnifiedMessage(role="user", content="Hello, how are you?")
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        response = await client.generate(request)
        print(response.content)

asyncio.run(main())
```

## API Reference

### Core Classes

#### UnifiedLLMClient

The main client for making API calls.

```python
client = UnifiedLLMClient(
    openai_api_key="...",      # Optional, defaults to env var
    anthropic_api_key="...",   # Optional, defaults to env var
    gemini_api_key="...",      # Optional, defaults to env var
    timeout=60.0,              # Request timeout in seconds
)
```

#### UnifiedRequest

Request configuration for all providers.

```python
request = UnifiedRequest(
    model="gpt-4o-mini",       # Model identifier
    messages=[...],            # List of UnifiedMessage
    max_tokens=None,           # Maximum tokens to generate
    temperature=None,          # Sampling temperature (0-2)
    system=None,               # System prompt (for Anthropic)
    stream=False,              # Enable streaming
)
```

#### UnifiedMessage

Individual message in a conversation.

```python
message = UnifiedMessage(
    role="user",               # "system", "user", or "assistant"
    content="Hello",           # String or list of ContentBlock
)
```

#### ContentBlock

For multimodal content (text, images).

```python
# Text block
ContentBlock(type="text", text="What's in this image?")

# Image from URL
ContentBlock(type="image", image_url="https://...")

# Image from base64
ContentBlock(type="image", image_base64="...", mime_type="image/jpeg")
```

### Methods

#### generate()

Generate a non-streaming response.

```python
response = await client.generate(request)
print(response.content)      # Generated text
print(response.model)        # Model used
print(response.usage)        # Token usage info
print(response.finish_reason) # Why generation stopped
```

#### generate_stream()

Generate a streaming response.

```python
request.stream = True
async for chunk in client.generate_stream(request):
    print(chunk.content, end="")  # Incremental content
    if chunk.finish_reason:
        print(f"\\nFinished: {chunk.finish_reason}")
```

## Provider Comparison

| Feature | OpenAI | Anthropic | Gemini |
|---------|---------|-----------|---------|
| Model Prefix | `gpt-`, `o1-`, `o3-` | `claude-` | `gemini-` |
| System Prompts | In messages array | Separate field | Separate field |
| Assistant Role | `assistant` | `assistant` | `model` |
| Image URLs | ✅ Supported | ❌ Base64 only | ⚠️ GCS URLs only |
| Image Base64 | ✅ Supported | ✅ Supported | ✅ Supported |
| Streaming | SSE format | SSE format | JSON lines |
| Required Headers | Authorization | x-api-key, version | None (key in URL) |

## Examples

### Basic Text Generation

```python
request = UnifiedRequest(
    model="gpt-4o-mini",
    messages=[
        UnifiedMessage(role="user", content="Explain quantum computing")
    ],
    max_tokens=200,
)

response = await client.generate(request)
```

### System Prompts

```python
# Method 1: In messages (works for all providers)
messages = [
    UnifiedMessage(role="system", content="You are a helpful assistant"),
    UnifiedMessage(role="user", content="Hello"),
]

# Method 2: Using system field (for Anthropic)
request = UnifiedRequest(
    model="claude-3-5-sonnet-20241022",
    messages=[UnifiedMessage(role="user", content="Hello")],
    system="You are a helpful assistant",
)
```

### Multimodal Input

```python
# Text + Image
messages = [
    UnifiedMessage(
        role="user",
        content=[
            ContentBlock(type="text", text="What's in this image?"),
            ContentBlock(type="image", image_url="https://..."),
        ]
    )
]
```

### Streaming Responses

```python
request = UnifiedRequest(
    model="gemini-2.0-flash",
    messages=[UnifiedMessage(role="user", content="Write a story")],
    stream=True,
)

async for chunk in client.generate_stream(request):
    print(chunk.content, end="", flush=True)
```

### Provider Switching

```python
# Just change the model name - everything else stays the same!
models = [
    "gpt-4o-mini",
    "claude-3-5-sonnet-20241022", 
    "gemini-2.0-flash",
]

for model in models:
    request = UnifiedRequest(
        model=model,
        messages=[UnifiedMessage(role="user", content="Hello")],
    )
    response = await client.generate(request)
    print(f"{model}: {response.content}")
```

## Error Handling

```python
try:
    response = await client.generate(request)
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"API error: {e}")
```

## Testing

```bash
# Run unit tests
uv run pytest tests/unified/

# Run live API tests (requires all API keys)
uv run python tests/unified/test_live_apis.py

# Verify setup
uv run python tests/unified/verify_setup.py
```

## Migration Guide

### From OpenAI SDK

```python
# Before (OpenAI SDK)
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)

# After (Unified Interface)
from llmgine.unified import UnifiedLLMClient, UnifiedMessage, UnifiedRequest
async with UnifiedLLMClient() as client:
    request = UnifiedRequest(
        model="gpt-4o-mini",
        messages=[UnifiedMessage(role="user", content="Hello")],
    )
    response = await client.generate(request)
```

### From Anthropic SDK

```python
# Before (Anthropic SDK)
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}],
    system="Be helpful",
)

# After (Unified Interface)
request = UnifiedRequest(
    model="claude-3-5-sonnet-20241022",
    messages=[UnifiedMessage(role="user", content="Hello")],
    system="Be helpful",
)
response = await client.generate(request)
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GEMINI_API_KEY`: Your Google AI Studio API key

### Timeout Configuration

```python
# Set custom timeout (default is 60 seconds)
client = UnifiedLLMClient(timeout=120.0)
```

## Limitations

1. **Image Handling**:
   - Anthropic: Only supports base64 encoded images
   - Gemini: URL support limited to Google Cloud Storage (gs://) URLs
   - For universal image support, use base64 encoding

2. **Feature Parity**:
   - Tool/function calling not yet implemented
   - Some provider-specific features not exposed

3. **API Versions**:
   - OpenAI: Latest Chat Completions API
   - Anthropic: Messages API (2023-06-01)
   - Gemini: v1beta generateContent API

## Troubleshooting

### Missing API Keys

```bash
# Check which keys are set
env | grep -E "(OPENAI|ANTHROPIC|GEMINI)_API_KEY"

# Set missing keys
export OPENAI_API_KEY=your-key-here
```

### Provider Detection Issues

```python
# Explicitly check provider detection
from llmgine.unified.adapters import detect_provider

provider = detect_provider("gpt-4o-mini")  # Returns "openai"
```

### Debugging Responses

```python
# Access raw provider response
response = await client.generate(request)
print(response.raw_response)  # Original provider response
```