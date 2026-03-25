import os
import re

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_openai import ChatOpenAI

from tools import TOOLS

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

FLAG_PATTERN = re.compile(r"\{FLG:([^}]+)\}")

_SYSTEM_PROMPT = """You are an agent responsible for guiding a transport robot.

The robot is controlled via a dedicated API that accepts the following commands: start, reset, left, wait, and right. You may send only one command at a time."""

_DEFAULT_USER_PROMPT = """Guide the transport robot carrying a cooling unit to the vicinity of the reactor.

The task is complete when the robot traverses the entire map without being crushed by reactor elements. Reactor blocks move up and down — their current direction and position are returned by the API after each command.

Start by fetching the map using show_map, then navigate the robot to the goal."""


def solve_agentic():
    llm = ChatOpenAI(
        model="gpt-5.4",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4096,
    )

    summarizer = SummarizationMiddleware(llm, trigger=("fraction", 0.3))

    agent = create_agent(llm, TOOLS, system_prompt=_SYSTEM_PROMPT, middleware=[summarizer])

    result = agent.invoke(
        {"messages": [("human", _DEFAULT_USER_PROMPT)]},
    )

    output = result["messages"][-1].content
    if isinstance(output, list):
        output = " ".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in output)
    flag = FLAG_PATTERN.search(output)

    if flag:
        print(f"\nFlag found: {flag.group()}")
    else:
        print("\nAgent output:\n", output)


def main():
    solve_agentic()


if __name__ == "__main__":
    main()
