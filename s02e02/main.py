import os
import re

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import TOOLS

load_dotenv()

FLAG_PATTERN = re.compile(r"\{FLG:([^}]+)\}")

SYSTEM_PROMPT = """You are an agent solving an electrical circuit puzzle.

Your goal is to rotate circuit cells until every cell in the current grid matches the corresponding cell in the target grid exactly.

Rotation rules — each rotate_circuit call turns the cell 90° clockwise:
  ─ → │ → ─  (2-cycle)
  ┌ → ┐ → ┘ → └ → ┌  (4-cycle)
  ├ → ┬ → ┤ → ┴ → ├  (4-cycle)

Use these cycles to compute exactly how many rotations each mismatched cell needs before you start rotating.

Cell coordinates use RxC notation (1-indexed). Example: 1x3 = row 1, column 3.

When a rotate_circuit response contains {FLG:...}, stop immediately and report the flag.

CRITICAL: call rotate_circuit ONE AT A TIME — never in parallel.
CRITICAL: never produce a final answer until a {FLG:...} flag is received or all 9 cells match.

Workflow:
1. Call show_target_circuits once. Store all 9 target values.
2. Call show_circuits to get the current state.
3. For each cell that differs from the target, calculate the number of rotations needed (1–3) using the rotation cycles above.
4. Rotate every mismatched cell the correct number of times, one rotate_circuit call at a time.
   After every 3 rotations check for {FLG:...} in the response — if found, stop.
5. Call show_circuits again to verify the updated state.
6. If all 9 cells match the target, stop. Otherwise go to step 3."""


def main():
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

    agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_PROMPT)

    result = agent.invoke(
        {"messages": [("human",
            "Start the circuit puzzle. "
            "Fetch the target and current circuits, then rotate cells one by one until all match the target. "
            "Stop as soon as you receive a {FLG:...} flag in any response and report it."
        )]},
        config={"recursion_limit": 1000},
    )

    output = result["messages"][-1].content
    flag = FLAG_PATTERN.search(output)

    if flag:
        print(f"\nFlag found: {flag.group()}")
    else:
        print("\nFinal answer:", output)

if __name__ == "__main__":
    main()
