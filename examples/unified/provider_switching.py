#!/usr/bin/env python
"""Demonstrate seamless provider switching with the unified interface."""

import asyncio
import os

from llmgine.unified import UnifiedMessage, UnifiedRequest
from llmgine.orchestrator import UnifiedLLMClient


async def generate_with_provider(
    client: UnifiedLLMClient, model: str, provider_name: str
):
    """Generate a response with a specific provider."""
    request = UnifiedRequest(
        model=model,
        messages=[
            UnifiedMessage(
                role="user", content="Write a haiku about artificial intelligence"
            )
        ],
        max_tokens=100,
        temperature=0.8,
    )

    print(f"\n{provider_name} ({model}):")
    print("-" * 50)

    try:
        response = await client.generate(request)
        print(response.content)
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Show how easy it is to switch between providers."""
    print("Unified LLM Interface - Provider Switching Demo")
    print("=" * 50)

    async with UnifiedLLMClient() as client:
        # Same code, different models - that's all!
        providers = []

        if os.environ.get("OPENAI_API_KEY"):
            providers.append(("gpt-4o-mini", "OpenAI"))

        if os.environ.get("ANTHROPIC_API_KEY"):
            providers.append(("claude-3-5-sonnet-20241022", "Anthropic"))

        if os.environ.get("GEMINI_API_KEY"):
            providers.append(("gemini-2.0-flash", "Google Gemini"))

        if not providers:
            print("\n⚠️  No API keys found. Please set at least one:")
            print("   export OPENAI_API_KEY=your-key")
            print("   export ANTHROPIC_API_KEY=your-key")
            print("   export GEMINI_API_KEY=your-key")
            return

        print(f"\nGenerating haikus from {len(providers)} provider(s)...")

        for model, name in providers:
            await generate_with_provider(client, model, name)


if __name__ == "__main__":
    asyncio.run(main())
