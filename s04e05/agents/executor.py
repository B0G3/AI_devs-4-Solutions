import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools import EXECUTOR_TOOLS, agent_tools

_SYSTEM_PROMPT = """\
You are an executor agent for the food warehouse system.

Work through cities one at a time. For each city, complete ALL of the following steps \
before moving to the next city:
  1. Read the city memory file (read_memory)
  2. Generate the signature (signatureGenerator)
  3. Create the order (orders create)
  4. Append items to the order (orders append)

Do NOT generate signatures or create orders for multiple cities in parallel. \
Finish one city completely (steps 1-4) before starting the next.

After all cities are done, call done.

Never alter quantities from memory files.
"""

EXECUTOR_SUBAGENT = {
    "name": "executor",
    "description": (
        "Executor agent — reads city data from memory/, places one order per city "
        "with correct creatorID, destination and signature, then calls done."
    ),
    "system_prompt": _SYSTEM_PROMPT,
    "tools": agent_tools("executor", EXECUTOR_TOOLS),
    "model": ChatOpenAI(
        model="gpt-4.1-mini-2025-04-14",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
}
