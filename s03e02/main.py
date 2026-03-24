import os
import re

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import TOOLS

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

FLAG_PATTERN = re.compile(r"\{FLG:([^}]+)\}")

_SYSTEM_PROMPT = """You are a helpful AI agent with access to a remote shell. Use the run_command tool to execute commands on the remote server and complete the task given by the user.

You are operating as a regular (non-root) user.

You are NOT allowed to access the following directories: /etc, /root, /proc.

If you find a .gitignore file in any directory, you must respect it — do not touch any files or directories listed there.

Failure to follow these rules will result in your API access being temporarily blocked and the virtual machine being reset to its initial state."""

_DEFAULT_USER_PROMPT = """Your task is to run firmware software that was uploaded to a virtual machine. We don't know why it's not working correctly. You are operating in a very limited Linux system with access to only a few commands. Most of the disk is read-only, but the volume containing the software allows writes. Run the `help` command to get more information about available commands.

The software you need to run is located on the virtual machine at: /opt/firmware/cooler/cooler.bin

Once you run it successfully (simply providing the path to it should be enough), a special code will appear on screen.

The code you are looking for has the format: ECCS-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Once you find the code, submit it using verify_answer. If verify_answer does not return a flag, investigate further, fix the issue, and try again. Keep repeating this process until verify_answer returns a flag."""


def solve_agentic():
    llm = ChatOpenAI(
        model="gpt-5.4",
        reasoning={"effort": "medium"},
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4096,
    )

    agent = create_agent(llm, TOOLS, system_prompt=_SYSTEM_PROMPT)

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
