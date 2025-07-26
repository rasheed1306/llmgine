from abc import ABC, abstractmethod
from typing import Any

from llmgine.llm.providers.response import LLMResponse


class Model(ABC):
    """
    Base class for all models.
    """

    @abstractmethod
    def generate(self, **kwargs: Any) -> LLMResponse:
        """
        Generate a response from the model.
        """
