#!/usr/bin/env python
"""Quick verification script for unified LLM setup."""

import asyncio
import os

from llmgine.unified import UnifiedLLMClient, UnifiedMessage, UnifiedRequest


async def verify_provider(client: UnifiedLLMClient, model: str, provider_name: str):
    """Verify a single provider works."""
    try:
        request = UnifiedRequest(
            model=model,
            messages=[UnifiedMessage(role="user", content="Say 'OK'")],
            max_tokens=10,
            temperature=0,
        )
        
        response = await client.generate(request)
        print(f"✅ {provider_name}: {response.content.strip()}")
        return True
    except Exception as e:
        print(f"❌ {provider_name}: {str(e)}")
        return False


async def main():
    """Verify all providers."""
    print("Verifying Unified LLM Interface Setup\n")
    
    # Check which API keys are available
    providers = []
    if os.environ.get("OPENAI_API_KEY"):
        providers.append(("gpt-4o-mini", "OpenAI"))
    else:
        print("⚠️  OPENAI_API_KEY not set")
    
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append(("claude-3-5-sonnet-20241022", "Anthropic"))
    else:
        print("⚠️  ANTHROPIC_API_KEY not set")
    
    if os.environ.get("GEMINI_API_KEY"):
        providers.append(("gemini-2.0-flash", "Gemini"))
    else:
        print("⚠️  GEMINI_API_KEY not set")
    
    if not providers:
        print("\n❌ No API keys found. Please set at least one API key.")
        return
    
    print(f"\nTesting {len(providers)} provider(s)...\n")
    
    async with UnifiedLLMClient() as client:
        results = []
        for model, name in providers:
            result = await verify_provider(client, model, name)
            results.append(result)
    
    success_count = sum(results)
    print(f"\n{'✅' if success_count == len(providers) else '⚠️'} {success_count}/{len(providers)} providers working")


if __name__ == "__main__":
    asyncio.run(main())