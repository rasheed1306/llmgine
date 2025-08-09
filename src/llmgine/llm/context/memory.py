"""
Simplified in-memory chat history management.
Compatible with litellm message format.
"""

from typing import Any, Dict, List, Optional
from llmgine.llm.tools.toolCall import ToolCall


class SimpleChatHistory:
    """Simple chat history management for litellm."""
    
    def __init__(self, engine_id: str = "", session_id: str = ""):
        """Initialize chat history."""
        self.engine_id = engine_id
        self.session_id = session_id
        self.chat_history: List[Dict[str, Any]] = []
        self.system_prompt: Optional[str] = None
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt."""
        self.system_prompt = prompt
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.chat_history.append({"role": "user", "content": content})
    
    def add_assistant_message(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        """Add an assistant message with optional tool calls."""
        message: Dict[str, Any] = {"role": "assistant"}
        
        if content:
            message["content"] = content
        elif tool_calls:
            # litellm requires content even with tool calls
            message["content"] = ""
        else:
            message["content"] = ""
        
        if tool_calls:
            message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments
                    }
                }
                for tc in tool_calls
            ]
        
        self.chat_history.append(message)
    
    def add_tool_message(self, tool_call_id: str, content: str) -> None:
        """Add a tool result message."""
        self.chat_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": str(content)
        })
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages including system prompt."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.chat_history)
        return messages
    
    def clear(self) -> None:
        """Clear chat history but keep system prompt."""
        self.chat_history.clear()
    
    # Backwards compatibility methods
    async def store_assistant_message(self, message_object: Any) -> None:
        """Store assistant message - for backwards compatibility."""
        if hasattr(message_object, 'content'):
            content = message_object.content
        else:
            content = ""
            
        tool_calls = None
        if hasattr(message_object, 'tool_calls') and message_object.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments
                )
                for tc in message_object.tool_calls
            ]
        
        self.add_assistant_message(content, tool_calls)
    
    async def store_tool_result(self, tool_call_id: str, result: str) -> None:
        """Store tool result - for backwards compatibility."""
        self.add_tool_message(tool_call_id, result)
    
    async def retrieve(self) -> List[Dict[str, Any]]:
        """Retrieve messages - for backwards compatibility."""
        return self.get_messages()