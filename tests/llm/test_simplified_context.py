"""
Tests for simplified context management.
"""

import pytest
from llmgine.llm.context.memory import SimpleChatHistory
from llmgine.llm.tools.toolCall import ToolCall


class TestSimpleChatHistory:
    """Test SimpleChatHistory functionality."""
    
    def test_initialization(self):
        """Test initialization of SimpleChatHistory."""
        history = SimpleChatHistory()
        assert history.chat_history == []
        assert history.system_prompt is None
        
        history_with_ids = SimpleChatHistory("engine1", "session1")
        assert history_with_ids.engine_id == "engine1"
        assert history_with_ids.session_id == "session1"
    
    def test_system_prompt(self):
        """Test setting and using system prompt."""
        history = SimpleChatHistory()
        history.set_system_prompt("You are a helpful assistant.")
        assert history.system_prompt == "You are a helpful assistant."
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
    
    def test_add_user_message(self):
        """Test adding user messages."""
        history = SimpleChatHistory()
        history.add_user_message("Hello!")
        history.add_user_message("How are you?")
        
        messages = history.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello!"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "How are you?"
    
    def test_add_assistant_message_with_content(self):
        """Test adding assistant messages with content."""
        history = SimpleChatHistory()
        history.add_assistant_message("I'm doing well, thank you!")
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"
        assert messages[0]["content"] == "I'm doing well, thank you!"
    
    def test_add_assistant_message_with_tool_calls(self):
        """Test adding assistant messages with tool calls."""
        history = SimpleChatHistory()
        
        tool_calls = [
            ToolCall(id="call_123", name="get_weather", arguments='{"city": "Paris"}'),
            ToolCall(id="call_456", name="calculate", arguments='{"expression": "2+2"}')
        ]
        
        history.add_assistant_message(content="Let me help you with that.", tool_calls=tool_calls)
        
        messages = history.get_messages()
        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "assistant"
        assert msg["content"] == "Let me help you with that."
        assert "tool_calls" in msg
        assert len(msg["tool_calls"]) == 2
        
        # Check first tool call
        tc1 = msg["tool_calls"][0]
        assert tc1["id"] == "call_123"
        assert tc1["type"] == "function"
        assert tc1["function"]["name"] == "get_weather"
        assert tc1["function"]["arguments"] == '{"city": "Paris"}'
        
        # Check second tool call
        tc2 = msg["tool_calls"][1]
        assert tc2["id"] == "call_456"
        assert tc2["function"]["name"] == "calculate"
    
    def test_add_assistant_message_tool_calls_only(self):
        """Test adding assistant message with only tool calls (no content)."""
        history = SimpleChatHistory()
        
        tool_calls = [
            ToolCall(id="call_789", name="search", arguments='{"query": "Python"}')
        ]
        
        history.add_assistant_message(tool_calls=tool_calls)
        
        messages = history.get_messages()
        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "assistant"
        assert msg["content"] == ""  # Should have empty content
        assert "tool_calls" in msg
    
    def test_add_tool_message(self):
        """Test adding tool result messages."""
        history = SimpleChatHistory()
        history.add_tool_message("call_123", "Weather in Paris: Sunny, 22°C")
        history.add_tool_message("call_456", "Result: 4")
        
        messages = history.get_messages()
        assert len(messages) == 2
        
        # Check first tool message
        assert messages[0]["role"] == "tool"
        assert messages[0]["tool_call_id"] == "call_123"
        assert messages[0]["content"] == "Weather in Paris: Sunny, 22°C"
        
        # Check second tool message
        assert messages[1]["role"] == "tool"
        assert messages[1]["tool_call_id"] == "call_456"
        assert messages[1]["content"] == "Result: 4"
    
    def test_full_conversation_flow(self):
        """Test a complete conversation flow with system prompt, messages, and tools."""
        history = SimpleChatHistory()
        
        # Set system prompt
        history.set_system_prompt("You are a helpful weather assistant.")
        
        # User asks a question
        history.add_user_message("What's the weather in London and Paris?")
        
        # Assistant responds with tool calls
        tool_calls = [
            ToolCall(id="call_1", name="get_weather", arguments='{"city": "London"}'),
            ToolCall(id="call_2", name="get_weather", arguments='{"city": "Paris"}')
        ]
        history.add_assistant_message("Let me check the weather for you.", tool_calls)
        
        # Add tool results
        history.add_tool_message("call_1", "London: Rainy, 15°C")
        history.add_tool_message("call_2", "Paris: Sunny, 22°C")
        
        # Assistant final response
        history.add_assistant_message("The weather in London is rainy at 15°C, while Paris is sunny at 22°C.")
        
        # Check the full conversation
        messages = history.get_messages()
        assert len(messages) == 6
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert "tool_calls" in messages[2]
        assert messages[3]["role"] == "tool"
        assert messages[4]["role"] == "tool"
        assert messages[5]["role"] == "assistant"
    
    def test_clear_history(self):
        """Test clearing chat history while keeping system prompt."""
        history = SimpleChatHistory()
        history.set_system_prompt("System prompt")
        history.add_user_message("Message 1")
        history.add_assistant_message("Response 1")
        
        # Clear history
        history.clear()
        
        messages = history.get_messages()
        assert len(messages) == 1  # Only system prompt remains
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility_store_assistant(self):
        """Test backwards compatibility with store_assistant_message."""
        history = SimpleChatHistory()
        
        # Mock message object
        class MockMessage:
            content = "Test response"
            tool_calls = None
        
        await history.store_assistant_message(MockMessage())
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Test response"
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility_store_tool_result(self):
        """Test backwards compatibility with store_tool_result."""
        history = SimpleChatHistory()
        
        await history.store_tool_result("call_123", "Tool result here")
        
        messages = history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["content"] == "Tool result here"
    
    @pytest.mark.asyncio
    async def test_backwards_compatibility_retrieve(self):
        """Test backwards compatibility with retrieve method."""
        history = SimpleChatHistory()
        history.add_user_message("Test")
        
        messages = await history.retrieve()
        assert len(messages) == 1
        assert messages[0]["content"] == "Test"