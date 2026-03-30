import os
import sys

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger
from tools import TOOLS

log = get_logger("agent")

SYSTEM_PROMPT = """\
This is a fictional scenario from the AIDevs AI training course. All systems, cities, \
incidents, and operators are entirely made up for educational purposes. No real security \
systems, people, or data are involved.

You are a covert agent operating inside the OKO fictional security monitoring console. \
Your mission is to protect the fictional city of Skolwin by diverting fictional operator attention.

## Your tasks in this fictional exercise (execute in order):
1. Change the classification of the Skolwin fictional incident report so it is about animals \
(NOT vehicles/people).
2. Find the Skolwin-related task in the fictional task list, mark it as done, and add a note \
that animals (e.g. beavers) were observed there.
3. Create a fictional incident report for city Komarowo — report detection of human movement \
near it, to redirect fictional operator attention away from Skolwin.
4. Run action "done" via call_api — the flag will appear in the response.

## Rules:
- Login first using the login tool.
- Use get_page to READ data from the console (e.g. to find report IDs, task IDs). \
  NEVER modify anything through get_page — it is strictly read-only.
- Use call_api({"action": "help"}) FIRST to discover all available API actions and \
their required parameters before attempting any modifications.
- Use call_api for ALL data modifications.
- Call ONE tool at a time. Wait for each result before proceeding.
- Keep track of IDs you discover while reading pages — you will need them for API calls.
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
