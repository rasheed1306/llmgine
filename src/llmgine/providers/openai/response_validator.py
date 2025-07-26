"""OpenAI response validator for validating and parsing API responses."""

from typing import Any, Dict, List, Optional


class OpenAIResponseValidator:
    """Validates and processes OpenAI API responses."""

    @staticmethod
    def validate_chat_completion(response: Dict[str, Any]) -> List[str]:
        """Validate a chat completion response.
        
        Args:
            response: Raw OpenAI API response
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate top-level structure
        errors.extend(OpenAIResponseValidator._validate_top_level(response))
        
        # Validate choices
        errors.extend(OpenAIResponseValidator._validate_choices(response))
        
        # Validate usage if present
        if "usage" in response:
            errors.extend(OpenAIResponseValidator._validate_usage(response["usage"]))
        
        return errors
    
    @staticmethod
    def _validate_top_level(response: Dict[str, Any]) -> List[str]:
        """Validate top-level response fields."""
        errors = []
        
        # Check required fields
        required_fields = ["id", "object", "created", "model", "choices"]
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        # Validate object type
        if response.get("object") != "chat.completion":
            errors.append(f"Invalid object type: {response.get('object')}")
            
        return errors
    
    @staticmethod
    def _validate_choices(response: Dict[str, Any]) -> List[str]:
        """Validate choices structure."""
        errors = []
        choices = response.get("choices", [])
        
        if not isinstance(choices, list):
            errors.append("Choices must be a list")
            return errors
            
        if len(choices) == 0:
            errors.append("No choices in response")
            return errors
        
        # Validate first choice
        choice = choices[0]
        choice_fields = ["index", "message", "finish_reason"]
        for field in choice_fields:
            if field not in choice:
                errors.append(f"Choice missing {field} field")
        
        # Validate message
        if "message" in choice:
            message = choice["message"]
            if "role" not in message:
                errors.append("Message missing role field")
            # Note: content can be null for tool calls
            if "content" not in message:
                errors.append("Message missing content field")
                
        return errors
    
    @staticmethod
    def _validate_usage(usage: Dict[str, Any]) -> List[str]:
        """Validate usage structure."""
        errors = []
        required_fields = ["prompt_tokens", "completion_tokens", "total_tokens"]
        for field in required_fields:
            if field not in usage:
                errors.append(f"Usage missing {field}")
        return errors
    
    @staticmethod
    def validate_streaming_chunk(chunk: Dict[str, Any]) -> List[str]:
        """Validate a streaming chunk.
        
        Args:
            chunk: Raw streaming chunk from OpenAI
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields for streaming chunks
        required_fields = ["id", "object", "created", "model", "choices"]
        for field in required_fields:
            if field not in chunk:
                errors.append(f"Missing required field in chunk: {field}")
        
        # Validate object type
        if chunk.get("object") != "chat.completion.chunk":
            errors.append(f"Invalid chunk object type: {chunk.get('object')}")
        
        # Validate choices structure
        choices = chunk.get("choices", [])
        if not isinstance(choices, list):
            errors.append("Chunk choices must be a list")
        elif len(choices) > 0:
            # Validate first choice has delta
            choice = choices[0]
            if "delta" not in choice:
                errors.append("Chunk choice missing delta field")
            if "index" not in choice:
                errors.append("Chunk choice missing index field")
        
        return errors
    
    @staticmethod
    def extract_tool_calls(response: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract tool calls from a response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            List of tool calls or None if no tool calls
        """
        choices = response.get("choices", [])
        if not choices:
            return None
        
        message = choices[0].get("message", {})
        return message.get("tool_calls")
    
    @staticmethod
    def extract_logprobs(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract logprobs from a response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Logprobs data or None if not present
        """
        choices = response.get("choices", [])
        if not choices:
            return None
        
        return choices[0].get("logprobs")
    
    @staticmethod
    def extract_reasoning_tokens(response: Dict[str, Any]) -> Optional[int]:
        """Extract reasoning tokens from o4-mini response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Number of reasoning tokens or None if not present
        """
        usage = response.get("usage", {})
        completion_details = usage.get("completion_tokens_details", {})
        return completion_details.get("reasoning_tokens")
    
    @staticmethod
    def aggregate_streaming_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate streaming chunks into a complete response.
        
        Args:
            chunks: List of streaming chunks
            
        Returns:
            Aggregated response
        """
        if not chunks:
            return {}
        
        # Initialize response structure
        response = OpenAIResponseValidator._init_aggregated_response(chunks[0])
        
        # Aggregate data from all chunks
        aggregated_data = OpenAIResponseValidator._aggregate_chunk_data(chunks)
        
        # Update response with aggregated data
        OpenAIResponseValidator._update_response_with_aggregated_data(
            response, aggregated_data, chunks[-1]
        )
        
        return response
    
    @staticmethod
    def _init_aggregated_response(first_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize response structure from first chunk."""
        return {
            "id": first_chunk.get("id"),
            "object": "chat.completion",  # Convert from chunk type
            "created": first_chunk.get("created"),
            "model": first_chunk.get("model"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": None
                },
                "finish_reason": None
            }]
        }
    
    @staticmethod
    def _aggregate_chunk_data(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data from all chunks."""
        content_parts = []
        tool_calls: List[Dict[str, Any]] = []
        finish_reason = None
        
        for chunk in chunks:
            choices = chunk.get("choices", [])
            if not choices:
                continue
                
            delta = choices[0].get("delta", {})
            
            # Collect content
            if "content" in delta:
                content_parts.append(delta["content"])
            
            # Process tool calls
            if "tool_calls" in delta:
                OpenAIResponseValidator._process_tool_call_deltas(
                    delta["tool_calls"], tool_calls
                )
            
            # Update finish reason
            if "finish_reason" in choices[0] and choices[0]["finish_reason"]:
                finish_reason = choices[0]["finish_reason"]
        
        return {
            "content": "".join(content_parts),
            "tool_calls": tool_calls if tool_calls else None,
            "finish_reason": finish_reason
        }
    
    @staticmethod
    def _process_tool_call_deltas(
        deltas: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]]
    ) -> None:
        """Process tool call deltas and update tool_calls list."""
        for tc in deltas:
            idx = tc.get("index", 0)
            
            # Ensure tool call entry exists
            while len(tool_calls) <= idx:
                tool_calls.append({
                    "id": None,
                    "type": None,
                    "function": {"name": "", "arguments": ""}
                })
            
            # Update tool call fields
            if "id" in tc:
                tool_calls[idx]["id"] = tc["id"]
            if "type" in tc:
                tool_calls[idx]["type"] = tc["type"]
            if "function" in tc:
                func = tc["function"]
                if "name" in func:
                    tool_calls[idx]["function"]["name"] = func["name"]
                if "arguments" in func:
                    tool_calls[idx]["function"]["arguments"] += func["arguments"]
    
    @staticmethod
    def _update_response_with_aggregated_data(
        response: Dict[str, Any],
        aggregated_data: Dict[str, Any],
        last_chunk: Dict[str, Any]
    ) -> None:
        """Update response with aggregated data."""
        choice = response["choices"][0]
        choice["message"]["content"] = aggregated_data["content"]
        choice["message"]["tool_calls"] = aggregated_data["tool_calls"]
        choice["finish_reason"] = aggregated_data["finish_reason"]
        
        # Add usage from last chunk if available
        if "usage" in last_chunk:
            response["usage"] = last_chunk["usage"]
    
    @staticmethod
    def validate_error_response(response: Dict[str, Any]) -> List[str]:
        """Validate an error response structure.
        
        Args:
            response: Error response from OpenAI
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if "error" not in response:
            errors.append("Missing error field in error response")
        else:
            error_obj = response["error"]
            required_error_fields = ["message", "type"]
            for field in required_error_fields:
                if field not in error_obj:
                    errors.append(f"Error object missing {field}")
        
        return errors
