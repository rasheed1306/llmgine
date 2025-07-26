#!/usr/bin/env python
"""Streaming response example with the unified interface."""

import asyncio

from llmgine.unified import UnifiedMessage, UnifiedRequest
from llmgine.orchestrator import UnifiedLLMClient


async def stream_response(client: UnifiedLLMClient, model: str):
    """Stream a response from the specified model."""
    request = UnifiedRequest(
        model=model,
        messages=[
            UnifiedMessage(
                role="user",
                content="Write a short story about a robot learning to paint. Make it 3 paragraphs.",
            )
        ],
        stream=True,  # Enable streaming
        temperature=0.8,
    )

    print(f"Streaming from {model}...\n")

    # Stream the response
    full_content = ""
    async for chunk in client.generate_stream(request):
        print(chunk.content, end="", flush=True)
        full_content += chunk.content

        # Check if we're done
        if chunk.finish_reason:
            print(f"\n\n[Finished: {chunk.finish_reason}]")

    return full_content


async def main():
    """Demonstrate streaming responses."""
    print("Unified LLM Interface - Streaming Example")
    print("=" * 50)

    # You can change this to any supported model
    models = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-2.0-flash",
    }

    # Pick a model based on available API keys
    model = None
    if os.environ.get("OPENAI_API_KEY"):
        model = models["openai"]
    elif os.environ.get("ANTHROPIC_API_KEY"):
        model = models["anthropic"]
    elif os.environ.get("GEMINI_API_KEY"):
        model = models["gemini"]
    else:
        print("\n❌ No API keys found. Please set one of:")
        print("   export OPENAI_API_KEY=your-key")
        print("   export ANTHROPIC_API_KEY=your-key")
        print("   export GEMINI_API_KEY=your-key")
        return

    async with UnifiedLLMClient() as client:
        await stream_response(client, model)


if __name__ == "__main__":
    import os

    asyncio.run(main())
