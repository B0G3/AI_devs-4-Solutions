import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from deepagents import create_deep_agent
from logger import get_logger
from tools import PLANNER_TOOLS, agent_tools

from .executor import EXECUTOR_SUBAGENT
from .research import RESEARCH_SUBAGENT

log = get_logger("planner")

_SYSTEM_PROMPT = """\
You are the main planner for the food warehouse system. \
Delegate all work to subagents — first to research, then to executor. \
Do not perform any operations yourself. \
After research completes, write a concise plan to memory/plan.md describing what the executor must do: \
which cities to process, which API endpoint to call for each order, and which fields to use \
(creatorID, destination, signature, goods and quantities). \
Then delegate to the executor. \
Report a brief summary when done.
"""


def run(task: str) -> str:
    log.info("planner: starting")

    llm = ChatOpenAI(
        model="gpt-5-mini-2025-08-07",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = create_deep_agent(
        model=llm,
        tools=agent_tools("planner", PLANNER_TOOLS),
        system_prompt=_SYSTEM_PROMPT,
        subagents=[RESEARCH_SUBAGENT, EXECUTOR_SUBAGENT],
        name="planner",
    )

    result = agent.invoke({"messages": [("human", task)]})

    output = result["messages"][-1].content
    if isinstance(output, list):
        output = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in output
        )

    log.info("planner: done")
    return output
