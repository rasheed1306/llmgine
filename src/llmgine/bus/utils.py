import inspect
from typing import Any, Callable


def is_async_function(function: Callable[..., Any]) -> bool:
    return inspect.iscoroutinefunction(function)
