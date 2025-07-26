#!/usr/bin/env python
"""Live API testing script for unified LLM interface.

This script tests all three providers with real API calls.
Requires environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY

Usage:
    python tests/unified/test_live_apis.py
"""

import asyncio
import os
import sys
from datetime import datetime

from llmgine.unified import (
    UnifiedLLMClient,
    UnifiedMessage,
    UnifiedRequest,
)


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f" {text}")
    print(f"{'=' * 60}\n")


def print_result(provider: str, success: bool, message: str):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{provider:<20} {status:<10} {message}")


async def test_basic_generation(client: UnifiedLLMClient):
    """Test basic text generation for all providers."""
    print_header("Test 1: Basic Text Generation")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    prompt = "Say exactly 'Hello from [provider]!' where [provider] is OpenAI, Anthropic, or Gemini based on which model you are."

    for provider_name, model in models:
        try:
            request = UnifiedRequest(
                model=model,
                messages=[UnifiedMessage(role="user", content=prompt)],
                max_tokens=20,
                temperature=0,
            )

            response = await client.generate(request)

            # Check if response contains expected provider name
            success = provider_name.lower() in response.content.lower()
            print_result(provider_name, success, f"Response: {response.content[:50]}...")

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def test_system_prompts(client: UnifiedLLMClient):
    """Test system prompt handling."""
    print_header("Test 2: System Prompts")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    for provider_name, model in models:
        try:
            request = UnifiedRequest(
                model=model,
                messages=[
                    UnifiedMessage(role="system", content="Always respond in uppercase."),
                    UnifiedMessage(role="user", content="hello"),
                ],
                max_tokens=20,
                temperature=0,
            )

            response = await client.generate(request)

            # Check if response is uppercase
            success = response.content.strip() == response.content.strip().upper()
            print_result(provider_name, success, f"Response: {response.content[:30]}...")

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def test_streaming(client: UnifiedLLMClient):
    """Test streaming responses."""
    print_header("Test 3: Streaming Responses")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    for provider_name, model in models:
        try:
            request = UnifiedRequest(
                model=model,
                messages=[UnifiedMessage(role="user", content="Count from 1 to 5")],
                stream=True,
                temperature=0,
            )

            chunks = []
            async for chunk in client.generate_stream(request):
                chunks.append(chunk)

            # Check if we got multiple chunks
            success = len(chunks) > 1
            content = "".join(chunk.content for chunk in chunks)
            print_result(
                provider_name,
                success,
                f"Chunks: {len(chunks)}, Content: {content[:30]}...",
            )

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def test_conversation(client: UnifiedLLMClient):
    """Test multi-turn conversation."""
    print_header("Test 4: Multi-turn Conversation")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    for provider_name, model in models:
        try:
            request = UnifiedRequest(
                model=model,
                messages=[
                    UnifiedMessage(role="user", content="Remember the number 42"),
                    UnifiedMessage(
                        role="assistant", content="I'll remember the number 42."
                    ),
                    UnifiedMessage(
                        role="user", content="What number did I ask you to remember?"
                    ),
                ],
                max_tokens=50,
                temperature=0,
            )

            response = await client.generate(request)

            # Check if response contains 42
            success = "42" in response.content
            print_result(provider_name, success, f"Response: {response.content[:50]}...")

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def test_temperature_variation(client: UnifiedLLMClient):
    """Test temperature parameter effect."""
    print_header("Test 5: Temperature Variation")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    prompt = "Write one creative word:"

    for provider_name, model in models:
        try:
            # Get two responses with high temperature
            responses = []
            for _ in range(2):
                request = UnifiedRequest(
                    model=model,
                    messages=[UnifiedMessage(role="user", content=prompt)],
                    max_tokens=10,
                    temperature=1.0,
                )
                response = await client.generate(request)
                responses.append(response.content.strip())

            # Check if responses are different (showing temperature effect)
            success = responses[0] != responses[1]
            print_result(
                provider_name, success, f"Responses: '{responses[0]}' vs '{responses[1]}'"
            )

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def test_token_limits(client: UnifiedLLMClient):
    """Test max_tokens parameter."""
    print_header("Test 6: Token Limits")

    models = [
        ("OpenAI", "gpt-4o-mini"),
        ("Anthropic", "claude-3-5-sonnet-20241022"),
        ("Gemini", "gemini-2.0-flash"),
    ]

    prompt = "Write a long story about a dragon. Make it at least 500 words."

    for provider_name, model in models:
        try:
            request = UnifiedRequest(
                model=model,
                messages=[UnifiedMessage(role="user", content=prompt)],
                max_tokens=50,  # Very limited
                temperature=0.7,
            )

            response = await client.generate(request)

            # Check if response is reasonably short (rough check)
            word_count = len(response.content.split())
            success = (
                word_count < 100
            )  # Should be well under 100 words with 50 token limit
            print_result(
                provider_name,
                success,
                f"Words: {word_count}, Finish: {response.finish_reason}",
            )

        except Exception as e:
            print_result(provider_name, False, f"Error: {str(e)[:50]}...")


async def main():
    """Run all tests."""
    print("\nUnified LLM Interface - Live API Tests")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check for API keys
    missing_keys = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing_keys.append("ANTHROPIC_API_KEY")
    if not os.environ.get("GEMINI_API_KEY"):
        missing_keys.append("GEMINI_API_KEY")

    if missing_keys:
        print(f"\n❌ Missing environment variables: {', '.join(missing_keys)}")
        print("Please set all required API keys before running tests.")
        sys.exit(1)

    # Run tests
    async with UnifiedLLMClient() as client:
        await test_basic_generation(client)
        await test_system_prompts(client)
        await test_streaming(client)
        await test_conversation(client)
        await test_temperature_variation(client)
        await test_token_limits(client)

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
