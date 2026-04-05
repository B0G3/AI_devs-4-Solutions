import functools
from typing import List

from langchain_core.tools import BaseTool

from logger import _current_agent

from .api import call_api
from .memory_tools import list_memories, read_memory, write_memory
from .supply import get_supply_requirements

RESEARCH_TOOLS = [call_api, get_supply_requirements, write_memory, read_memory, list_memories]
EXECUTOR_TOOLS = [call_api, read_memory, list_memories]
PLANNER_TOOLS = [write_memory, read_memory, list_memories]


def agent_tools(agent_name: str, tools: List[BaseTool]) -> List[BaseTool]:
    """Return copies of tools that stamp the agent name into logs before each call."""
    result = []
    for t in tools:
        if t.func is None:
            result.append(t)
            continue

        def _make_wrapper(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                token = _current_agent.set(agent_name)
                try:
                    return fn(*args, **kwargs)
                finally:
                    _current_agent.reset(token)
            return wrapper

        result.append(t.model_copy(update={"func": _make_wrapper(t.func)}))
    return result
