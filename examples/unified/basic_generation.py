#!/usr/bin/env python
"""Basic text generation example using the unified LLM interface."""

import asyncio

from llmgine.unified import UnifiedMessage, UnifiedRequest
from llmgine.orchestrator import UnifiedLLMClient


async def main():
    """Demonstrate basic text generation."""
    # Create a client (uses API keys from environment)
    async with UnifiedLLMClient() as client:
        
        # Create a request - just change the model to switch providers!
        request = UnifiedRequest(
            model="gpt-4o-mini",  # or "claude-3-5-sonnet-20241022" or "gemini-2.0-flash"
            messages=[
                UnifiedMessage(role="user", content="Explain quantum computing in one paragraph")
            ],
            max_tokens=200,
            temperature=0.7,
        )
        
        # Generate response
        print("Generating response...\n")
        response = await client.generate(request)
        
        # Display results
        print(f"Model: {response.model}")
        print(f"Response:\n{response.content}")
        
        if response.usage:
            print(f"\nTokens used: {response.usage.get('total_tokens', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())