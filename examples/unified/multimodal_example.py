#!/usr/bin/env python
"""Multimodal example - text and images with the unified interface."""

import asyncio
import base64
from pathlib import Path

from llmgine.unified import (
    ContentBlock,
    UnifiedMessage,
    UnifiedRequest,
)
from llmgine.orchestrator import UnifiedLLMClient


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and convert to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def analyze_image_url(client: UnifiedLLMClient, model: str):
    """Analyze an image from URL (OpenAI and Gemini)."""
    print(f"\nAnalyzing image from URL with {model}...")

    request = UnifiedRequest(
        model=model,
        messages=[
            UnifiedMessage(
                role="user",
                content=[
                    ContentBlock(type="text", text="What's in this image?"),
                    ContentBlock(
                        type="image",
                        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/640px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                    ),
                ],
            )
        ],
        max_tokens=200,
        temperature=0.7,
    )

    try:
        response = await client.generate(request)
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")


async def analyze_image_base64(client: UnifiedLLMClient, model: str, image_base64: str):
    """Analyze an image from base64 (all providers)."""
    print(f"\nAnalyzing base64 image with {model}...")

    request = UnifiedRequest(
        model=model,
        messages=[
            UnifiedMessage(
                role="user",
                content=[
                    ContentBlock(type="text", text="Describe this image in detail."),
                    ContentBlock(
                        type="image", image_base64=image_base64, mime_type="image/jpeg"
                    ),
                ],
            )
        ],
        max_tokens=300,
        temperature=0.7,
    )

    try:
        response = await client.generate(request)
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Demonstrate multimodal capabilities."""
    print("Unified LLM Interface - Multimodal Example")
    print("=" * 50)

    # For this example, we'll create a simple test image
    # In practice, you'd load a real image file
    # Example: image_base64 = load_image_as_base64("path/to/image.jpg")

    # This is a tiny 1x1 red pixel as base64 for demonstration
    test_image_base64 = (
        "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
        "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
        "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
        "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
        "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmY"
        "AAA="
    )

    async with UnifiedLLMClient() as client:
        # OpenAI supports both URLs and base64
        if os.environ.get("OPENAI_API_KEY"):
            print("\n### OpenAI Tests ###")
            await analyze_image_url(client, "gpt-4o-mini")
            await analyze_image_base64(client, "gpt-4o-mini", test_image_base64)

        # Anthropic only supports base64
        if os.environ.get("ANTHROPIC_API_KEY"):
            print("\n### Anthropic Tests ###")
            print("Note: Anthropic only supports base64 images")
            await analyze_image_base64(
                client, "claude-3-5-sonnet-20241022", test_image_base64
            )

        # Gemini supports various formats
        if os.environ.get("GEMINI_API_KEY"):
            print("\n### Gemini Tests ###")
            print("Note: URL support limited to Google Cloud Storage (gs://) URLs")
            await analyze_image_base64(client, "gemini-2.0-flash", test_image_base64)

        if not any([
            os.environ.get("OPENAI_API_KEY"),
            os.environ.get("ANTHROPIC_API_KEY"),
            os.environ.get("GEMINI_API_KEY"),
        ]):
            print("\n❌ No API keys found. Please set at least one API key.")


if __name__ == "__main__":
    import os

    asyncio.run(main())
