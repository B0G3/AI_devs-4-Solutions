import os
import sys

from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.research_agent import run as research_agent_run
from logger import get_logger

log = get_logger("planning_agent")


@tool
def research_tools(keywords: str) -> str:
    """Discover available API tools on the hub that match the given keywords.

    Delegates to the research agent, which generates keyword variants and
    searches the hub's toolsearch endpoint. Returns a JSON array of matching
    tools sorted by relevance score.

    Args:
        keywords: Natural-language description of what you are looking for.

    Returns:
        JSON array of discovered tools with name, url, description, and score.
    """
    log.info("research_tools called: keywords=%r", keywords)
    result = research_agent_run(keywords)
    log.info("research_tools done")
    return result
