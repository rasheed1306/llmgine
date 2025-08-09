"""
Integration tests for simplified context and tools with litellm.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall


# Mock tool functions
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: Sunny, 22°C"


def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    return eval(expression)


class TestLiteLLMIntegration:
    """Test integration with litellm."""
    
    @pytest.mark.asyncio
    async def test_simple_conversation_flow(self):
        """Test a simple conversation without tools."""
        history = SimpleChatHistory()
        history.set_system_prompt("You are a helpful assistant.")
        history.add_user_message("Hello!")
        
        # Mock litellm response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you today?"
        mock_response.choices[0].message.tool_calls = None
        
        with patch('litellm.acompletion', new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response
            
            # Simulate calling litellm
            from litellm import acompletion
            response = await acompletion(
                model="gpt-4o-mini",
                messages=history.get_messages()
            )
            
            # Verify the call
            mock_acompletion.assert_called_once()
            call_args = mock_acompletion.call_args
            assert call_args[1]["model"] == "gpt-4o-mini"
            assert len(call_args[1]["messages"]) == 2  # system + user
            
            # Add response to history
            history.add_assistant_message(response.choices[0].message.content)
            
            # Verify history
            messages = history.get_messages()
            assert len(messages) == 3
            assert messages[2]["content"] == "Hello! How can I help you today?"
    
    @pytest.mark.asyncio
    async def test_tool_calling_flow(self):
        """Test conversation with tool calling."""
        # Setup
        history = SimpleChatHistory()
        history.set_system_prompt("You are a helpful weather assistant.")
        
        tool_manager = ToolManager(history)
        tool_manager.register_tool(get_weather)
        tool_manager.register_tool(calculate)
        
        # User asks about weather
        history.add_user_message("What's the weather in Paris and London?")
        
        # Mock litellm response with tool calls
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.function.name = "get_weather"
        mock_tool_call_1.function.arguments = '{"city": "Paris"}'
        
        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.function.name = "get_weather"
        mock_tool_call_2.function.arguments = '{"city": "London"}'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2]
        
        with patch('litellm.acompletion', new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response
            
            # Simulate calling litellm with tools
            from litellm import acompletion
            response = await acompletion(
                model="gpt-4o-mini",
                messages=tool_manager.chat_history_to_messages(),
                tools=tool_manager.parse_tools_to_list()
            )
            
            # Verify the call included tools
            call_args = mock_acompletion.call_args
            assert "tools" in call_args[1]
            assert len(call_args[1]["tools"]) == 2
            
            # Process tool calls
            if response.choices[0].message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=tc.function.arguments
                    )
                    for tc in response.choices[0].message.tool_calls
                ]
                
                # Add assistant message with tool calls
                history.add_assistant_message(
                    content=response.choices[0].message.content,
                    tool_calls=tool_calls
                )
                
                # Execute tools
                results = await tool_manager.execute_tool_calls(tool_calls)
                
                # Add tool results to history
                for tool_call, result in zip(tool_calls, results):
                    history.add_tool_message(tool_call.id, str(result))
                
                # Verify execution
                assert len(results) == 2
                assert "Paris" in results[0]
                assert "London" in results[1]
            
            # Verify final history
            messages = history.get_messages()
            assert len(messages) == 5  # system, user, assistant, tool, tool
            assert messages[2]["role"] == "assistant"
            assert "tool_calls" in messages[2]
            assert messages[3]["role"] == "tool"
            assert messages[4]["role"] == "tool"
    
    @pytest.mark.asyncio
    async def test_tool_schema_compatibility(self):
        """Test that generated tool schemas are compatible with litellm/OpenAI format."""
        tool_manager = ToolManager()
        
        # Register various types of tools
        def simple_tool(param: str) -> str:
            """A simple tool."""
            return f"Result: {param}"
        
        def complex_tool(
            text: str,
            number: int,
            flag: bool = False,
            items: List[str] = None
        ) -> dict:
            """A complex tool with multiple parameter types."""
            return {"text": text, "number": number, "flag": flag, "items": items}
        
        tool_manager.register_tool(simple_tool)
        tool_manager.register_tool(complex_tool)
        
        tools = tool_manager.parse_tools_to_list()
        
        # Validate format matches OpenAI/litellm expectations
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            
            params = func["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params
            assert isinstance(params["required"], list)
            
            # Each property should have type and description
            for prop_name, prop_def in params["properties"].items():
                assert "type" in prop_def
                assert "description" in prop_def
                assert prop_def["type"] in ["string", "integer", "number", "boolean", "array", "object"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_tool_execution(self):
        """Test error handling when tools fail."""
        tool_manager = ToolManager()
        
        def failing_tool(param: str) -> str:
            """A tool that always fails."""
            raise ValueError(f"Intentional failure for {param}")
        
        tool_manager.register_tool(failing_tool)
        
        tool_call = ToolCall(
            id="fail_call",
            name="failing_tool",
            arguments='{"param": "test"}'
        )
        
        result = await tool_manager.execute_tool_call(tool_call)
        assert "Error executing failing_tool:" in result
        assert "Intentional failure" in result
    
    @pytest.mark.asyncio
    async def test_conversation_continuation(self):
        """Test continuing a conversation after tool execution."""
        history = SimpleChatHistory()
        tool_manager = ToolManager(history)
        tool_manager.register_tool(calculate)
        
        # Initial conversation
        history.set_system_prompt("You are a math assistant.")
        history.add_user_message("What is 15 * 8?")
        
        # Simulate tool call
        tool_call = ToolCall(
            id="calc_1",
            name="calculate",
            arguments='{"expression": "15 * 8"}'
        )
        history.add_assistant_message("Let me calculate that.", [tool_call])
        
        # Execute and add result
        result = await tool_manager.execute_tool_call(tool_call)
        history.add_tool_message(tool_call.id, str(result))
        
        # Final response
        history.add_assistant_message(f"15 * 8 equals {result}.")
        
        # Continue conversation
        history.add_user_message("Now divide that by 4.")
        
        # Verify messages are in correct order
        messages = history.get_messages()
        assert len(messages) == 6  # system, user, assistant+tool_call, tool, assistant, user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "tool"
        assert messages[4]["role"] == "assistant"
        assert messages[5]["role"] == "user"
        assert messages[5]["content"] == "Now divide that by 4."
        
        # Verify the conversation is ready for next litellm call
        assert messages == tool_manager.chat_history_to_messages()
    
    def test_message_format_for_litellm(self):
        """Test that message format is correct for litellm."""
        history = SimpleChatHistory()
        
        # Build a conversation with all message types
        history.set_system_prompt("System prompt here")
        history.add_user_message("User message")
        history.add_assistant_message(
            "Assistant with tools",
            [ToolCall(id="tc1", name="tool1", arguments='{"arg": "val"}')]
        )
        history.add_tool_message("tc1", "Tool result")
        history.add_assistant_message("Final response")
        
        messages = history.get_messages()
        
        # Validate each message format
        assert messages[0] == {"role": "system", "content": "System prompt here"}
        assert messages[1] == {"role": "user", "content": "User message"}
        
        # Assistant with tool calls
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Assistant with tools"
        assert "tool_calls" in messages[2]
        tool_call = messages[2]["tool_calls"][0]
        assert tool_call["id"] == "tc1"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "tool1"
        assert tool_call["function"]["arguments"] == '{"arg": "val"}'
        
        # Tool message
        assert messages[3] == {
            "role": "tool",
            "tool_call_id": "tc1",
            "content": "Tool result"
        }
        
        # Final assistant message
        assert messages[4] == {"role": "assistant", "content": "Final response"}