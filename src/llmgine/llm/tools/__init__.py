"""Tools for LLMs.

This module provides tools that can be called by language models.
"""

# Re-export tool call events from messages
from llmgine.llm import AsyncToolFunction, ToolFunction
from llmgine.llm.tools.tool import Parameter, Tool
from llmgine.llm.tools.tool_manager import ToolManager
from llmgine.llm.tools.toolCall import ToolCall

__all__ = [
    "AsyncToolFunction",
    "Parameter",
    "Tool",
    "ToolCall",
    "ToolFunction",
    "ToolManager",
]
