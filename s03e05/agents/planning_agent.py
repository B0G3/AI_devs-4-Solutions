from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.research_agent import SUBAGENT
from tools.api import call_api, verify_answer

load_dotenv()

SYSTEM_PROMPT = """\
You are a planning agent. Your goal is to plan an optimal route to a destination.

Start by obtaining a map of the area. Then select a vehicle from the available options.

Keep in mind:
- Fuel consumption is critical — running out means mission failure.
- Food is critical — the messenger must have enough for the entire journey.

Use the research-agent subagent to discover available data sources and APIs whenever you need \
information about the map, vehicles, fuel, food, or routes.

Call ONE tool at a time — never call multiple tools in parallel. Wait for each result before proceeding.

Once you have a plan, submit it using verify_answer. If the response does not contain a flag, \
revise your plan and try again. Keep iterating until you receive a flag.
"""

_agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-5.4", reasoning_effort="medium", use_responses_api=True),
    system_prompt=SYSTEM_PROMPT,
    tools=[call_api, verify_answer],
    subagents=[SUBAGENT],
)


def run(task: str) -> str:
    """Run the planning agent with the given task description."""
    result = _agent.invoke({"messages": [{"role": "user", "content": task}]})
    return result["messages"][-1].content
