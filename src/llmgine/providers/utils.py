"""Utility functions for provider management."""

from typing import Literal


def detect_provider(model: str) -> Literal["openai", "anthropic", "gemini"]:
    """Detect provider from model name."""
    if model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o3-"):
        return "openai"
    elif model.startswith("claude-"):
        return "anthropic"
    elif model.startswith("gemini-"):
        return "gemini"
    else:
        raise ValueError(f"Cannot detect provider for model: {model}")


def get_required_headers(
    provider: Literal["openai", "anthropic", "gemini"],
) -> dict[str, str]:
    """Get required headers for each provider."""
    headers_map = {
        "openai": {
            "Content-Type": "application/json",
        },
        "anthropic": {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        "gemini": {
            "Content-Type": "application/json",
        },
    }
    return headers_map.get(provider, {})
