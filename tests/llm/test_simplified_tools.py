"""
Tests for simplified tool management.
"""

import asyncio
import json
import pytest
from typing import List, Optional

from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall


# Sample tool functions for testing
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    
    :param city: The city name
    """
    return f"Weather in {city}: Sunny, 22°C"


def calculate(expression: str) -> float:
    """Calculate a mathematical expression.
    
    :param expression: The expression to evaluate
    """
    return eval(expression)


async def async_search(query: str, limit: int = 10) -> List[str]:
    """Search for information asynchronously.
    
    :param query: The search query
    :param limit: Maximum number of results
    """
    await asyncio.sleep(0.01)  # Simulate async operation
    return [f"Result {i} for '{query}'" for i in range(1, min(limit + 1, 4))]


def complex_function(
    required_str: str,
    required_int: int,
    optional_str: Optional[str] = None,
    optional_bool: bool = False,
    optional_list: Optional[List[str]] = None
) -> dict:
    """A complex function with multiple parameter types.
    
    :param required_str: A required string parameter
    :param required_int: A required integer parameter
    :param optional_str: An optional string parameter
    :param optional_bool: An optional boolean parameter
    :param optional_list: An optional list parameter
    """
    return {
        "required_str": required_str,
        "required_int": required_int,
        "optional_str": optional_str,
        "optional_bool": optional_bool,
        "optional_list": optional_list
    }


class TestToolManager:
    """Test ToolManager functionality."""
    
    def test_initialization(self):
        """Test ToolManager initialization."""
        manager = ToolManager()
        assert manager.tools == {}
        assert manager.tool_schemas == []
        assert manager.chat_history is None
        
        # With chat history
        history = SimpleChatHistory()
        manager_with_history = ToolManager(history)
        assert manager_with_history.chat_history == history
    
    def test_register_simple_tool(self):
        """Test registering a simple tool."""
        manager = ToolManager()
        manager.register_tool(get_weather)
        
        assert "get_weather" in manager.tools
        assert manager.tools["get_weather"] == get_weather
        assert len(manager.tool_schemas) == 1
        
        schema = manager.tool_schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "get_weather"
        assert "Get the current weather" in schema["function"]["description"]
        assert "city" in schema["function"]["parameters"]["properties"]
        assert schema["function"]["parameters"]["properties"]["city"]["type"] == "string"
        assert schema["function"]["parameters"]["required"] == ["city"]
    
    def test_register_async_tool(self):
        """Test registering an async tool."""
        manager = ToolManager()
        manager.register_tool(async_search)
        
        assert "async_search" in manager.tools
        schema = manager.tool_schemas[0]
        
        # Check parameters
        params = schema["function"]["parameters"]
        assert "query" in params["properties"]
        assert "limit" in params["properties"]
        assert params["properties"]["limit"]["type"] == "integer"
        # Only query is required (limit has default)
        assert params["required"] == ["query"]
    
    def test_register_complex_tool(self):
        """Test registering a tool with complex parameters."""
        manager = ToolManager()
        manager.register_tool(complex_function)
        
        schema = manager.tool_schemas[0]
        params = schema["function"]["parameters"]
        
        # Check all parameters are detected
        assert "required_str" in params["properties"]
        assert "required_int" in params["properties"]
        assert "optional_str" in params["properties"]
        assert "optional_bool" in params["properties"]
        assert "optional_list" in params["properties"]
        
        # Check types
        assert params["properties"]["required_str"]["type"] == "string"
        assert params["properties"]["required_int"]["type"] == "integer"
        assert params["properties"]["optional_bool"]["type"] == "boolean"
        assert params["properties"]["optional_list"]["type"] == "array"
        
        # Check required fields
        assert set(params["required"]) == {"required_str", "required_int"}
    
    def test_parse_tools_to_list(self):
        """Test getting tools in OpenAI format."""
        manager = ToolManager()
        
        # Empty manager
        assert manager.parse_tools_to_list() is None
        
        # With tools
        manager.register_tool(get_weather)
        manager.register_tool(calculate)
        
        tools = manager.parse_tools_to_list()
        assert len(tools) == 2
        assert all(tool["type"] == "function" for tool in tools)
        
        tool_names = [tool["function"]["name"] for tool in tools]
        assert "get_weather" in tool_names
        assert "calculate" in tool_names
    
    @pytest.mark.asyncio
    async def test_execute_simple_tool(self):
        """Test executing a simple tool."""
        manager = ToolManager()
        manager.register_tool(get_weather)
        
        tool_call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments='{"city": "London"}'
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert result == "Weather in London: Sunny, 22°C"
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_dict_arguments(self):
        """Test executing a tool with dict arguments instead of string."""
        manager = ToolManager()
        manager.register_tool(calculate)
        
        tool_call = ToolCall(
            id="call_456",
            name="calculate",
            arguments={"expression": "10 + 20"}
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert result == 30
    
    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Test executing an async tool."""
        manager = ToolManager()
        manager.register_tool(async_search)
        
        tool_call = ToolCall(
            id="call_789",
            name="async_search",
            arguments='{"query": "Python", "limit": 2}'
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert isinstance(result, list)
        assert len(result) == 2
        assert "Python" in result[0]
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        manager = ToolManager()
        
        tool_call = ToolCall(
            id="call_000",
            name="nonexistent_tool",
            arguments='{}'
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert "Error: Tool 'nonexistent_tool' not found" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self):
        """Test executing a tool that raises an error."""
        manager = ToolManager()
        manager.register_tool(calculate)
        
        tool_call = ToolCall(
            id="call_err",
            name="calculate",
            arguments='{"expression": "invalid expression"}'
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert "Error executing calculate:" in result
    
    @pytest.mark.asyncio
    async def test_execute_multiple_tools(self):
        """Test executing multiple tool calls."""
        manager = ToolManager()
        manager.register_tool(get_weather)
        manager.register_tool(calculate)
        
        tool_calls = [
            ToolCall(id="1", name="get_weather", arguments='{"city": "Paris"}'),
            ToolCall(id="2", name="calculate", arguments='{"expression": "5 * 5"}'),
            ToolCall(id="3", name="get_weather", arguments='{"city": "Tokyo"}')
        ]
        
        results = await manager.execute_tool_calls(tool_calls)
        assert len(results) == 3
        assert "Paris" in results[0]
        assert results[1] == 25
        assert "Tokyo" in results[2]
    
    def test_chat_history_integration(self):
        """Test integration with chat history."""
        history = SimpleChatHistory()
        history.set_system_prompt("You are a helpful assistant.")
        history.add_user_message("Hello!")
        history.add_assistant_message("Hi there!")
        
        manager = ToolManager(history)
        messages = manager.chat_history_to_messages()
        
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
    
    def test_chat_history_without_history(self):
        """Test chat_history_to_messages without a history object."""
        manager = ToolManager()
        messages = manager.chat_history_to_messages()
        assert messages == []
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility_register_async(self):
        """Test backwards compatibility with register_tool_async."""
        manager = ToolManager()
        await manager.register_tool_async(get_weather)
        
        assert "get_weather" in manager.tools
        assert len(manager.tool_schemas) == 1
    
    @pytest.mark.asyncio
    async def test_empty_arguments(self):
        """Test executing a tool with no arguments."""
        def no_args_tool() -> str:
            """A tool with no arguments."""
            return "Success!"
        
        manager = ToolManager()
        manager.register_tool(no_args_tool)
        
        tool_call = ToolCall(
            id="call_no_args",
            name="no_args_tool",
            arguments=""
        )
        
        result = await manager.execute_tool_call(tool_call)
        assert result == "Success!"
    
    def test_tool_schema_format_for_litellm(self):
        """Test that tool schemas are in the correct format for litellm."""
        manager = ToolManager()
        manager.register_tool(get_weather)
        
        tools = manager.parse_tools_to_list()
        assert tools is not None
        
        # Validate OpenAI tool format
        tool = tools[0]
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]
        
        params = tool["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params