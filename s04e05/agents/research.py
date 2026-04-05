import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools import RESEARCH_TOOLS, agent_tools

_SYSTEM_PROMPT = """\
You are a research agent for the food warehouse system. \
Your goal is to gather everything needed to place orders and save it to memory/ so the executor can use it. \
Call one tool at a time.

Read food4cities.json to get ALL cities and their required goods/quantities — \
do not skip any city. Save the full list to memory/cities_list.json.

Use the API help tool to discover available tools and the database tool to explore the schema. \
Find the destination code for every city, and determine the correct creatorID for each city — \
the creator must be the person responsible for transport to that city (each city likely has a different creator). \
Look for a table linking users to cities and check the users table for login and birthday. \
Do not assume all cities share the same creatorID.

Generate a signature for each city using the correct creator's login, birthday, and destination. \

Save one file per city to memory/city_<Name>.md with: destination, creatorID, login, birthday, signature, and items dict. \
Write memory/plan.md with the full executor plan listing all cities with their title, creatorID, destination, signature, and items batch.
"""

RESEARCH_SUBAGENT = {
    "name": "research",
    "description": (
        "Research agent — fetches food4cities.json, discovers API tools via 'help', "
        "collects destination/creatorID/signature for each city, writes results to memory/."
    ),
    "system_prompt": _SYSTEM_PROMPT,
    "tools": agent_tools("research", RESEARCH_TOOLS),
    "model": ChatOpenAI(
        model="gpt-5-mini-2025-08-07",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
}
