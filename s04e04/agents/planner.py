import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from deepagents import create_deep_agent
from logger import get_logger
from tools import ASSEMBLY_TOOLS, RESEARCH_TOOLS

from .assembly import ASSEMBLY_SUBAGENT
from .research import RESEARCH_SUBAGENT

log = get_logger("planner")

_SYSTEM_PROMPT = """\
You are the memory planner. Your job is to orchestrate a two-stage pipeline that processes
Natan Rams's notes and produces a structured memory system.

## Pipeline (execute in strict order)

### Stage 1 — Research
Delegate to the **research** subagent.
Task: "Read all files in original/ and extract cities (miasta), people (osoby), and goods
(towary). Write one .md note per entity into temp/."

Wait for the research subagent to finish before proceeding.

### Stage 2 — Assembly
Delegate to the **assembly** subagent.
Task: "Read all notes from temp/ and write final output files to output/miasta/,
output/osoby/, and output/towary/ in the required formats."

Wait for the assembly subagent to finish.

### Done
Once both stages complete, report a brief summary:
- How many city files were created
- How many person files were created
- How many goods files were created

## Rules
- Call ONE tool / delegate ONE subagent at a time.
- Do NOT read or write files yourself — delegate all file work to subagents.
- NEVER stop early. Drive the pipeline to completion.
"""


def run(task: str) -> str:
    log.info("planner: starting")

    llm = ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = create_deep_agent(
        model=llm,
        tools=[],
        system_prompt=_SYSTEM_PROMPT,
        subagents=[RESEARCH_SUBAGENT, ASSEMBLY_SUBAGENT],
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
