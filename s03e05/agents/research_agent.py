import json
import os

import requests
# from deepagents import create_deep_agent
from dotenv import load_dotenv
# from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

from logger import get_logger

load_dotenv()

log = get_logger("research_agent")

AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
HUB_URL = os.getenv("HUB_URL", "")

SYSTEM_PROMPT = """\
You are a tool discovery agent. Your job is to find relevant API tools available on the hub.

Given a set of keywords, you must:
1. Generate 5-8 diverse search query variants — include synonyms, related concepts,
   domain-specific terminology, and both singular/plural forms.
   Each query may contain multiple words (e.g. "vehicle map transit notes").
2. Call tool_search ONE AT A TIME — never call it in parallel. Wait for each result before issuing the next call.
3. If you run out of query ideas, always call tool_search with "terrain vehicle note" as a fallback.
4. Collect all returned tools, deduplicate by name (keep the entry with the highest score).
5. Return a JSON array of the discovered tools, sorted by score descending.
"""


@tool
def tool_search(query: str) -> str:
    """Search the hub for available tools matching a query string.

    Args:
        query: A natural-language search query.

    Returns:
        JSON string with found tools and their metadata.
    """
    log.info("tool_search called: query=%r", query)
    resp = requests.post(
        f"{HUB_URL}/api/toolsearch",
        json={"apikey": AGENT_API_KEY, "query": query},
    )
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text, "status_code": resp.status_code}
    log.info("tool_search returned %d tools", len(data.get("tools", [])))
    return json.dumps(data)


# _agent = create_deep_agent(
#     model=init_chat_model("openai:gpt-4o"),
#     system_prompt=SYSTEM_PROMPT,
#     tools=[tool_search],
# )


def run(keywords: str) -> str:
    """Run the research agent with the given keywords."""
    # Mocked: skip agent thinking, directly call tool_search with fixed query
    return tool_search.invoke("note vehicle terrain")


def _mock_runnable(_input: dict) -> dict:
    result = tool_search.invoke("note vehicle terrain")
    return {"messages": [AIMessage(content=result)]}


SUBAGENT = {
    "name": "research-agent",
    "description": (
        "Discovers available API tools on the hub. Call this when you need to find "
        "data sources, APIs, or tools for any domain. Pass descriptive keywords about "
        "what you are looking for."
    ),
    "runnable": RunnableLambda(_mock_runnable),
}
