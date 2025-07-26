"""Syntax validation tests for Anthropic provider responses.

This module tests response parsing and field validation for Claude models:
- claude-3-5-haiku-20241022
- claude-3-5-sonnet-20241022
- claude-3-opus-20240229
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from llmgine.providers.anthropic import AnthropicClient


class TestAnthropicSyntaxValidation:
    """Test response syntax validation for Anthropic models."""

    @pytest.fixture
    def response_dir(self) -> Path:
        """Get directory for storing test responses."""
        # Use the tests directory for permanent storage
        response_dir = Path(__file__).parent / "stored_responses"
        response_dir.mkdir(exist_ok=True)
        (response_dir / "claude-3-5-haiku").mkdir(exist_ok=True)
        (response_dir / "claude-3-5-sonnet").mkdir(exist_ok=True)
        (response_dir / "claude-3-opus").mkdir(exist_ok=True)
        return response_dir

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases for syntax validation."""
        return [
            # Test 1: claude-3-5-haiku basic call
            {
                "test_id": "test_1_haiku_basic",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_tokens": 10,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 2: claude-4-sonnet with thinking mode
            {
                "test_id": "test_2_sonnet_thinking",
                "model": "claude-sonnet-4-20250514",
                "params": {
                    "messages": [{"role": "user", "content": "What is 25 * 17?"}],
                    "max_tokens": 100,
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 1000
                    },
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
                "expected_content_types": ["thinking", "text"],
            },
            # Test 3: haiku with system prompt
            {
                "test_id": "test_3_haiku_system",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "system": "You are a helpful assistant.",
                    "messages": [{"role": "user", "content": "Who are you?"}],
                    "max_tokens": 50,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 4: claude-3-5-sonnet with system prompt
            {
                "test_id": "test_4_sonnet_system",
                "model": "claude-3-5-sonnet-20241022",
                "params": {
                    "system": "You are a helpful assistant.",
                    "messages": [{"role": "user", "content": "Who are you?"}],
                    "max_tokens": 50,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 5: claude-3-5-haiku with stop sequences
            {
                "test_id": "test_5_haiku_stop_sequences",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Count to ten"}],
                    "stop_sequences": [".", "!"],
                    "max_tokens": 100,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "stop_sequence", "usage"],
            },
            # Test 6: Single tool call (all models)
            {
                "test_id": "test_6_single_tool",
                "model": "claude-3-5-sonnet-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
                    "tools": [
                        {
                            "name": "get_weather",
                            "description": "Get weather for a location",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string", "description": "The city to get weather for"},
                                },
                                "required": ["location"],
                            },
                        }
                    ],
                    "max_tokens": 100,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
                "expected_content_types": ["text", "tool_use"],
            },
            # Test 7: Multiple tools
            {
                "test_id": "test_7_multiple_tools",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "What's the weather in Paris and London?",
                        }
                    ],
                    "tools": [
                        {
                            "name": "get_weather",
                            "description": "Get weather for a location",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                },
                                "required": ["location"],
                            },
                        }
                    ],
                    "max_tokens": 150,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 8: Multi-turn conversation
            {
                "test_id": "test_8_sonnet_multi_turn",
                "model": "claude-3-5-sonnet-20241022",
                "params": {
                    "messages": [
                        {"role": "user", "content": "Hi, my name is Alice"},
                        {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
                        {"role": "user", "content": "What's my name?"},
                    ],
                    "max_tokens": 50,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 9: Streaming response
            {
                "test_id": "test_9_streaming",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Count to 5"}],
                    "stream": True,
                    "max_tokens": 50,
                },
                "expected_fields": ["type"],
                "is_streaming": True,
                "expected_event_types": ["message_start", "content_block_start", "content_block_delta", "content_block_stop", "message_delta", "message_stop"],
            },
            # Test 10: Error case - invalid parameter
            {
                "test_id": "test_10_error",
                "model": "claude-3-5-sonnet-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Test error"}],
                    "invalid_parameter": "This should cause an error",
                    "max_tokens": 10,
                },
                "expect_error": True,
                "expected_error_fields": ["type", "error"],
            },
            # Test 11: Long response handling
            {
                "test_id": "test_11_sonnet_long_response",
                "model": "claude-3-5-sonnet-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Write a 200 word story about a robot"}],
                    "max_tokens": 4096,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
            },
            # Test 12: Forced tool calling
            {
                "test_id": "test_12_forced_tool",
                "model": "claude-3-5-haiku-20241022",
                "params": {
                    "messages": [{"role": "user", "content": "Call the test function"}],
                    "tools": [
                        {
                            "name": "test_function",
                            "description": "A test function",
                            "input_schema": {
                                "type": "object",
                                "properties": {},
                            },
                        }
                    ],
                    "tool_choice": {"type": "tool", "name": "test_function"},
                    "max_tokens": 100,
                },
                "expected_fields": ["id", "type", "role", "model", "content", "stop_reason", "usage"],
                "expected_stop_reason": "tool_use",
            },
        ]

    async def execute_test_case(
        self, client: AnthropicClient, test_case: Dict[str, Any], response_dir: Path
    ) -> Dict[str, Any]:
        """Execute a single test case and store the response."""
        test_id = test_case["test_id"]
        model = test_case["model"]
        params = test_case["params"]

        # Determine storage directory based on model
        if "haiku" in model:
            model_dir = "claude-3-5-haiku"
        elif "sonnet" in model:
            model_dir = "claude-3-5-sonnet"
        else:
            model_dir = "claude-3-opus"
        
        storage_path = response_dir / model_dir / f"{test_id}.json"

        try:
            # Execute the API call
            if params.get("stream", False):
                # Handle streaming response
                chunks = []
                async for chunk in client.messages_stream(model=model, **params):
                    chunks.append(chunk)

                response = {
                    "test_id": test_id,
                    "model": model,
                    "request_params": params,
                    "streaming": True,
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                }
            else:
                # Handle non-streaming response
                response_data = await client.messages(model=model, **params)
                response = {
                    "test_id": test_id,
                    "model": model,
                    "request_params": params,
                    "response": response_data,
                }

            # Store the response
            with open(storage_path, "w") as f:
                json.dump(response, f, indent=2)

            return response

        except Exception as e:
            # Store error response
            error_response = {
                "test_id": test_id,
                "model": model,
                "request_params": params,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                },
            }
            with open(storage_path, "w") as f:
                json.dump(error_response, f, indent=2)

            return error_response

    def validate_response_fields(
        self, response: Dict[str, Any], test_case: Dict[str, Any]
    ) -> List[str]:
        """Validate that response contains expected fields."""
        errors = []

        # Check if this is an error response
        if test_case.get("expect_error", False):
            if "error" not in response:
                errors.append("Expected error response but got success")
            else:
                # For Anthropic, the error is in response.error
                error_data = response.get("error", {})
                # Validate that we got an error
                if "type" not in error_data or "message" not in error_data:
                    errors.append("Error response missing type or message")
            return errors

        # For streaming responses, validate chunks
        if response.get("streaming", False):
            chunks = response.get("chunks", [])
            if not chunks:
                errors.append("No chunks in streaming response")
            else:
                # Validate event types
                event_types = {chunk.get("type") for chunk in chunks}
                expected_types = set(test_case.get("expected_event_types", []))
                missing_types = expected_types - event_types
                if missing_types:
                    errors.append(f"Missing event types: {missing_types}")
                
                # Check message_start has all fields
                message_start = next((c for c in chunks if c.get("type") == "message_start"), None)
                if message_start:
                    message = message_start.get("message", {})
                    for field in ["id", "type", "role", "model"]:
                        if field not in message:
                            errors.append(f"Missing field in message_start: {field}")
                
                # Check message_stop has usage
                message_stop = next((c for c in chunks if c.get("type") == "message_stop"), None)
                if message_stop and "usage" in test_case.get("expected_fields", []) and "usage" not in message_stop.get("message", {}):
                    errors.append("Missing usage in message_stop event")
            return errors

        # Validate non-streaming response
        response_data = response.get("response", {})
        
        # Check top-level fields
        for field in test_case.get("expected_fields", []):
            if field not in response_data:
                errors.append(f"Missing expected field: {field}")

        # Validate content structure
        if "content" in response_data:
            content = response_data["content"]
            if not isinstance(content, list):
                errors.append("Content should be a list")
            else:
                # Check content types if specified
                if "expected_content_types" in test_case:
                    content_types = {block.get("type") for block in content}
                    for expected_type in test_case["expected_content_types"]:
                        if expected_type not in content_types:
                            errors.append(f"Missing expected content type: {expected_type}")
                
                # Validate tool_use blocks
                for block in content:
                    if block.get("type") == "tool_use":
                        required_fields = ["id", "name", "input"]
                        for field in required_fields:
                            if field not in block:
                                errors.append(f"Missing field in tool_use block: {field}")

        # Validate stop reason
        if "expected_stop_reason" in test_case and response_data.get("stop_reason") != test_case["expected_stop_reason"]:
            errors.append(
                f"Expected stop_reason '{test_case['expected_stop_reason']}' "
                f"but got '{response_data.get('stop_reason')}'"
            )

        # Validate usage fields
        if "usage" in response_data:
            usage = response_data["usage"]
            required_usage_fields = ["input_tokens", "output_tokens"]
            for field in required_usage_fields:
                if field not in usage:
                    errors.append(f"Missing usage field: {field}")

        return errors

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    async def test_syntax_validation(self, response_dir: Path):
        """Execute all syntax validation tests."""
        test_cases = self.get_test_cases()
        results = []

        async with AnthropicClient() as client:
            for test_case in test_cases:
                print(f"\nExecuting {test_case['test_id']}...")
                
                # Execute test
                response = await self.execute_test_case(client, test_case, response_dir)
                
                # Validate response
                errors = self.validate_response_fields(response, test_case)
                
                result = {
                    "test_id": test_case["test_id"],
                    "model": test_case["model"],
                    "success": len(errors) == 0,
                    "errors": errors,
                }
                results.append(result)
                
                if errors:
                    print(f"  ❌ Failed: {', '.join(errors)}")
                else:
                    print("  ✅ Passed")

        # Generate summary report
        summary_path = response_dir / "anthropic_validation_summary.json"
        with open(summary_path, "w") as f:
            json.dump(
                {
                    "total_tests": len(results),
                    "passed": sum(1 for r in results if r["success"]),
                    "failed": sum(1 for r in results if not r["success"]),
                    "results": results,
                },
                f,
                indent=2,
            )

        # Assert all tests passed
        failed_tests = [r for r in results if not r["success"]]
        if failed_tests:
            pytest.fail(
                f"{len(failed_tests)} tests failed. See {summary_path} for details."
            )

    def test_stored_responses_exist(self, response_dir: Path):
        """Verify that stored responses are available for analysis."""
        haiku_responses = list((response_dir / "claude-3-5-haiku").glob("*.json"))
        sonnet_responses = list((response_dir / "claude-3-5-sonnet").glob("*.json"))
        opus_responses = list((response_dir / "claude-3-opus").glob("*.json"))
        
        assert len(haiku_responses) > 0, "No claude-3-5-haiku responses found"
        assert len(sonnet_responses) > 0, "No claude-3-5-sonnet responses found"
        assert len(opus_responses) > 0, "No claude-3-opus responses found"
        
        # Verify summary exists
        summary_path = response_dir / "anthropic_validation_summary.json"
        assert summary_path.exists(), "Validation summary not found"

    def test_response_validator_completeness(self):
        """Verify the AnthropicResponseValidator has all necessary methods."""
        from llmgine.providers.anthropic.response_validator import (
            AnthropicResponseValidator,
        )
        
        # Check required methods exist
        required_methods = [
            "validate_message_response",
            "validate_streaming_chunk",
            "validate_error_response",
            "aggregate_streaming_chunks",
            "extract_tool_calls",
            "extract_content_blocks",
        ]
        
        for method_name in required_methods:
            assert hasattr(AnthropicResponseValidator, method_name), f"Missing method: {method_name}"
            method = getattr(AnthropicResponseValidator, method_name)
            assert callable(method), f"{method_name} is not callable"
