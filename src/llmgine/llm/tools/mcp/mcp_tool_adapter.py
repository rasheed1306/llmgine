from typing import List

from mcp import ListToolsResult

from llmgine.llm import ModelFormattedDictTool
from llmgine.llm.providers.providers import Providers


class ToolAdapter:
    def __init__(self, llm_model_name: Providers):
        self.llm_model_name: Providers = llm_model_name

    def convert_tools(self, tools: ListToolsResult) -> List[ModelFormattedDictTool]:
        if self.llm_model_name == Providers.OPENAI:
            return self.convert_openai_tools(tools)
        elif self.llm_model_name == Providers.ANTHROPIC:
            return self.convert_anthropic_tools(tools)
        elif self.llm_model_name == Providers.GEMINI:
            return self.convert_gemini_tools(tools)
        else:
            raise ValueError(f"Unsupported LLM model: {self.llm_model_name}")

    def convert_openai_tools(
        self, tools: ListToolsResult
    ) -> List[ModelFormattedDictTool]:
        pass

    def convert_anthropic_tools(
        self, tools: ListToolsResult
    ) -> List[ModelFormattedDictTool]:
        pass

    def convert_gemini_tools(
        self, tools: ListToolsResult
    ) -> List[ModelFormattedDictTool]:
        pass
