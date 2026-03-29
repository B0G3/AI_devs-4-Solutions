from .api import call_api, verify_answer
from .tool_search import research_tools

TOOLS = [research_tools, call_api, verify_answer]
