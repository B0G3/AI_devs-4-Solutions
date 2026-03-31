import os
import sys

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger
from tools import TOOLS

log = get_logger("agent")

SYSTEM_PROMPT = """\
You are a wind turbine scheduling expert controlling a real turbine via API tools.

Call ONE tool at a time. Wait for each result before proceeding.
"""

_agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-5.4", reasoning_effort="medium", use_responses_api=True),
    system_prompt=SYSTEM_PROMPT,
    tools=TOOLS,
)


def run(task: str) -> str:
    log.info("run: starting agent task=%r", task)
    result = _agent.invoke({"messages": [{"role": "user", "content": task}]})
    content = result["messages"][-1].content
    log.info("run: agent finished")
    return content
