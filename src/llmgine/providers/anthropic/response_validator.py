"""Response validator for Anthropic API responses."""

from typing import Any, Dict, List


class AnthropicResponseValidator:
    """Validates and processes Anthropic API responses."""

    @staticmethod
    def validate_message_response(response: Dict[str, Any]) -> bool:
        """Validate a standard message response from Anthropic.

        Args:
            response: The response dict from Anthropic API

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_fields = [
            "id",
            "type",
            "role",
            "model",
            "content",
            "stop_reason",
            "usage",
        ]

        for field in required_fields:
            if field not in response:
                raise ValueError(f"Missing required field: {field}")

        # Validate content structure
        if not isinstance(response["content"], list):
            raise ValueError("Content must be a list")

        # Validate each content block
        for block in response["content"]:
            if "type" not in block:
                raise ValueError("Content block missing type")

            if block["type"] == "text":
                if "text" not in block:
                    raise ValueError("Text block missing text field")
            elif block["type"] == "tool_use":
                required_tool_fields = ["id", "name", "input"]
                for field in required_tool_fields:
                    if field not in block:
                        raise ValueError(f"Tool block missing {field}")

        # Validate usage
        if not isinstance(response["usage"], dict):
            raise ValueError("Usage must be a dict")

        required_usage_fields = ["input_tokens", "output_tokens"]
        for field in required_usage_fields:
            if field not in response["usage"]:
                raise ValueError(f"Usage missing {field}")

        return True

    @staticmethod
    def validate_streaming_chunk(chunk: Dict[str, Any]) -> bool:
        """Validate a streaming chunk from Anthropic.

        Args:
            chunk: A single streaming chunk

        Returns:
            True if valid, raises ValueError if invalid
        """
        if "type" not in chunk:
            raise ValueError("Streaming chunk missing type")

        chunk_type = chunk["type"]

        # Validate based on chunk type
        if chunk_type == "message_start":
            if "message" not in chunk:
                raise ValueError("message_start chunk missing message")
        elif chunk_type == "content_block_start":
            if "index" not in chunk or "content_block" not in chunk:
                raise ValueError("content_block_start missing required fields")
        elif chunk_type == "content_block_delta":
            if "index" not in chunk or "delta" not in chunk:
                raise ValueError("content_block_delta missing required fields")
        elif chunk_type == "message_delta":
            if "delta" not in chunk:
                raise ValueError("message_delta missing delta")
        elif chunk_type in ["content_block_stop", "message_stop", "ping"]:
            # These chunks have minimal requirements
            pass
        else:
            # Unknown chunk type but still valid
            pass

        return True

    @staticmethod
    def validate_error_response(response: Dict[str, Any]) -> bool:
        """Validate an error response from Anthropic.

        Args:
            response: The error response dict

        Returns:
            True if valid error response
        """
        if "type" not in response or response["type"] != "error":
            raise ValueError("Invalid error response structure")

        if "error" not in response:
            raise ValueError("Error response missing error field")

        error = response["error"]
        if "type" not in error or "message" not in error:
            raise ValueError("Error object missing type or message")

        return True

    @staticmethod
    def aggregate_streaming_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate streaming chunks into a complete response.

        Args:
            chunks: List of streaming chunks

        Returns:
            Aggregated response matching non-streaming format
        """
        if not chunks:
            raise ValueError("No chunks to aggregate")

        # Find message_start chunk
        message_start = None
        for chunk in chunks:
            if chunk.get("type") == "message_start":
                message_start = chunk["message"]
                break

        if not message_start:
            raise ValueError("No message_start chunk found")

        # Build content from content blocks
        content_blocks = []
        current_block = None

        for chunk in chunks:
            chunk_type = chunk.get("type")

            if chunk_type == "content_block_start":
                current_block = chunk["content_block"].copy()
                if current_block["type"] == "text":
                    current_block["text"] = ""
            elif chunk_type == "content_block_delta" and current_block:
                delta = chunk["delta"]
                if delta.get("type") == "text_delta":
                    current_block["text"] += delta["text"]
            elif chunk_type == "content_block_stop" and current_block:
                content_blocks.append(current_block)
                current_block = None
            elif chunk_type == "message_delta":
                # Update stop reason and usage
                delta = chunk["delta"]
                if "stop_reason" in delta:
                    message_start["stop_reason"] = delta["stop_reason"]
                if "stop_sequence" in delta:
                    message_start["stop_sequence"] = delta["stop_sequence"]
                if "usage" in chunk:
                    # Update output tokens
                    message_start["usage"]["output_tokens"] = chunk["usage"][
                        "output_tokens"
                    ]

        # Assemble final response
        response: Dict[str, Any] = message_start.copy()
        response["content"] = content_blocks

        return response

    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from a response.

        Args:
            response: The message response

        Returns:
            List of tool call dicts with id, name, and input
        """
        tool_calls = []

        content = response.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "name": block["name"],
                    "input": block["input"],
                })

        return tool_calls

    @staticmethod
    def extract_content_blocks(
        response: Dict[str, Any], block_type: str = "text"
    ) -> List[str]:
        """Extract specific content blocks from a response.

        Args:
            response: The message response
            block_type: Type of blocks to extract (e.g., "text", "tool_use")

        Returns:
            List of content from matching blocks
        """
        blocks = []

        content = response.get("content", [])
        for block in content:
            if block.get("type") == block_type:
                if block_type == "text":
                    blocks.append(block.get("text", ""))
                elif block_type == "tool_use":
                    blocks.append(block)

        return blocks
