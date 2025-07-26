"""Syntax validation tests for OpenAI provider responses.

This module tests response parsing and field validation for both
o4-mini-2025-04-16 and gpt-4o-mini-2024-07-18 models.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from llmgine.providers.openai import OpenAIClient


class TestOpenAISyntaxValidation:
    """Test response syntax validation for OpenAI models."""

    @pytest.fixture
    def response_dir(self) -> Path:
        """Get directory for storing test responses."""
        # Use the tests directory for permanent storage
        response_dir = Path(__file__).parent / "stored_responses"
        response_dir.mkdir(exist_ok=True)
        (response_dir / "o4-mini").mkdir(exist_ok=True)
        (response_dir / "gpt-4o-mini").mkdir(exist_ok=True)
        return response_dir

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """Get all test cases for syntax validation."""
        return [
            # Test 1: o4-mini basic call
            {
                "test_id": "test_1_o4_basic",
                "model": "o4-mini-2025-04-16",
                "params": {
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_completion_tokens": 10,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
            },
            # Test 2: gpt-4o-mini basic call
            {
                "test_id": "test_2_gpt4o_basic",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_tokens": 10,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
            },
            # Test 3: o4-mini with reasoning_effort
            {
                "test_id": "test_3_o4_reasoning",
                "model": "o4-mini-2025-04-16",
                "params": {
                    "messages": [{"role": "user", "content": "What is 2+2?"}],
                    "reasoning_effort": "high",
                    "max_completion_tokens": 500,  # Increased for reasoning model
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
                "expected_usage_fields": ["reasoning_tokens"],
            },
            # Test 4: gpt-4o-mini with logprobs
            {
                "test_id": "test_4_gpt4o_logprobs",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "logprobs": True,
                    "top_logprobs": 3,
                    "max_tokens": 5,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
                "expected_choice_fields": ["logprobs"],
            },
            # Test 5: Single tool call
            {
                "test_id": "test_5_single_tool",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "description": "Get weather for a location",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {"type": "string"},
                                    },
                                    "required": ["location"],
                                },
                            },
                        }
                    ],
                    "tool_choice": "auto",
                    "max_tokens": 100,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
                "possible_finish_reasons": ["tool_calls", "stop"],
            },
            # Test 6: Multiple tools with parallel calls
            {
                "test_id": "test_6_parallel_tools",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "What's the weather in Paris and London?",
                        }
                    ],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "description": "Get weather for a location",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {"type": "string"},
                                    },
                                    "required": ["location"],
                                },
                            },
                        }
                    ],
                    "parallel_tool_calls": True,
                    "max_tokens": 150,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
            },
            # Test 7: JSON response format
            {
                "test_id": "test_7_json_format",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Generate a JSON object with name and age fields",
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 50,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
            },
            # Test 8: Streaming response
            {
                "test_id": "test_8_streaming",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "Count to 5"}],
                    "stream": True,
                    "max_tokens": 50,
                },
                "expected_fields": ["id", "object", "created", "model", "choices"],
                "is_streaming": True,
            },
            # Test 9: Error case
            {
                "test_id": "test_9_error",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "Test error"}],
                    "invalid_parameter": "This should cause an error",
                    "max_tokens": 10,
                },
                "expect_error": True,
                "expected_error_fields": ["error"],
            },
            # Test 10: Required tool call
            {
                "test_id": "test_10_required_tool",
                "model": "gpt-4o-mini-2024-07-18",
                "params": {
                    "messages": [{"role": "user", "content": "Call the function"}],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "test_function",
                                "description": "A test function",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                },
                            },
                        }
                    ],
                    "tool_choice": "required",
                    "max_tokens": 100,
                },
                "expected_fields": ["id", "object", "created", "model", "choices", "usage"],
                "expected_finish_reason": "tool_calls",
            },
        ]

    async def execute_test_case(
        self, client: OpenAIClient, test_case: Dict[str, Any], response_dir: Path
    ) -> Dict[str, Any]:
        """Execute a single test case and store the response."""
        test_id = test_case["test_id"]
        model = test_case["model"]
        params = test_case["params"]

        # Determine storage directory based on model
        model_dir = "o4-mini" if "o4-mini" in model else "gpt-4o-mini"
        storage_path = response_dir / model_dir / f"{test_id}.json"

        try:
            # Execute the API call
            if params.get("stream", False):
                # Handle streaming response
                chunks = []
                async for chunk in client.stream_chat_completion(model=model, **params):
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
                response_data = await client.chat_completion(model=model, **params)
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
                # Validate error fields
                error_fields = test_case.get("expected_error_fields", [])
                for field in error_fields:
                    if field not in response:
                        errors.append(f"Missing expected error field: {field}")
            return errors

        # For streaming responses, validate chunks
        if response.get("streaming", False):
            chunks = response.get("chunks", [])
            if not chunks:
                errors.append("No chunks in streaming response")
            else:
                # Validate first chunk has expected fields
                first_chunk = chunks[0]
                for field in test_case.get("expected_fields", []):
                    if field not in first_chunk and field != "usage":
                        errors.append(f"Missing field in first chunk: {field}")

                # Check if last chunk has usage
                last_chunk = chunks[-1]
                if "usage" in test_case.get("expected_fields", []) and "usage" not in last_chunk:
                    errors.append("Missing usage field in last chunk")
            return errors

        # Validate non-streaming response
        response_data = response.get("response", {})
        
        # Check top-level fields
        for field in test_case.get("expected_fields", []):
            if field not in response_data:
                errors.append(f"Missing expected field: {field}")

        # Validate choices structure
        if "choices" in response_data:
            choices = response_data["choices"]
            if not isinstance(choices, list) or len(choices) == 0:
                errors.append("Invalid choices structure")
            else:
                choice = choices[0]
                
                # Check for expected choice fields
                for field in test_case.get("expected_choice_fields", []):
                    if field not in choice:
                        errors.append(f"Missing expected choice field: {field}")

                # Validate finish reason
                if "expected_finish_reason" in test_case:
                    if choice.get("finish_reason") != test_case["expected_finish_reason"]:
                        errors.append(
                            f"Expected finish_reason '{test_case['expected_finish_reason']}' "
                            f"but got '{choice.get('finish_reason')}'"
                        )
                elif "possible_finish_reasons" in test_case:
                    if choice.get("finish_reason") not in test_case["possible_finish_reasons"]:
                        errors.append(
                            f"Unexpected finish_reason: {choice.get('finish_reason')}"
                        )

                # Check for tool calls
                if choice.get("finish_reason") == "tool_calls":
                    message = choice.get("message", {})
                    if "tool_calls" not in message:
                        errors.append("Missing tool_calls in message with tool_calls finish_reason")

        # Validate usage fields
        if "usage" in response_data:
            usage = response_data["usage"]
            for field in test_case.get("expected_usage_fields", []):
                # Check in usage directly
                if field in usage:
                    continue
                # Check in completion_tokens_details for o4-mini specific fields
                if "completion_tokens_details" in usage and field in usage["completion_tokens_details"]:
                    continue
                errors.append(f"Missing expected usage field: {field}")

        return errors

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    async def test_syntax_validation(self, response_dir: Path):
        """Execute all syntax validation tests."""
        test_cases = self.get_test_cases()
        results = []

        async with OpenAIClient() as client:
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
        summary_path = response_dir / "validation_summary.json"
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
        o4_responses = list((response_dir / "o4-mini").glob("*.json"))
        gpt4o_responses = list((response_dir / "gpt-4o-mini").glob("*.json"))
        
        assert len(o4_responses) > 0, "No o4-mini responses found"
        assert len(gpt4o_responses) > 0, "No gpt-4o-mini responses found"
        
        # Verify summary exists
        summary_path = response_dir / "validation_summary.json"
        assert summary_path.exists(), "Validation summary not found"

    def test_response_validator_completeness(self):
        """Verify the OpenAIResponseValidator has all necessary methods."""
        from llmgine.providers.openai.response_validator import OpenAIResponseValidator
        
        # Check required methods exist
        required_methods = [
            "validate_chat_completion",
            "validate_streaming_chunk",
            "validate_error_response",
            "aggregate_streaming_chunks",
            "extract_tool_calls",
            "extract_logprobs",
            "extract_reasoning_tokens",
        ]
        
        for method_name in required_methods:
            assert hasattr(OpenAIResponseValidator, method_name), f"Missing method: {method_name}"
            method = getattr(OpenAIResponseValidator, method_name)
            assert callable(method), f"{method_name} is not callable"
