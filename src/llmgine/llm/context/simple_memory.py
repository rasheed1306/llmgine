"""
Simplified memory management for chat conversations.
Works directly with litellm message format.
"""

from typing import Any, Dict, List, Optional
from llmgine.llm.tools.toolCall import ToolCall


class SimpleMemory:
    """Simple in-memory chat history management."""
    
    def __init__(self):
        """Initialize empty chat history."""
        self.messages: List[Dict[str, Any]] = []
        self.system_prompt: Optional[str] = None
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the conversation."""
        self.system_prompt = prompt
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the history."""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(
        self, 
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        """Add an assistant message to the history."""
        message: Dict[str, Any] = {"role": "assistant"}
        
        if content:
            message["content"] = content
        
        if tool_calls:
            # Convert ToolCall objects to litellm format
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
            # Ensure content is not None when there are tool calls
            if not content:
                message["content"] = ""
        
        self.messages.append(message)
    
    def add_tool_message(self, tool_call_id: str, content: str) -> None:
        """Add a tool result message to the history."""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages including system prompt if set."""
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        messages.extend(self.messages)
        return messages
    
    def clear(self) -> None:
        """Clear the chat history but keep system prompt."""
        self.messages.clear()
    
    def reset(self) -> None:
        """Reset everything including system prompt."""
        self.messages.clear()
        self.system_prompt = None