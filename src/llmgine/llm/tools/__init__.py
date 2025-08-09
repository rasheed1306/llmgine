"""
Simplified tools for litellm.
"""

from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall

__all__ = [
    "ToolCall",
    "ToolManager",
]