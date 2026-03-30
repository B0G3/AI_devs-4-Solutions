import json
import os
import sys

from langchain_core.tools import tool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger
from tools.browser import session

log = get_logger("api")

AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
HUB_URL = os.getenv("HUB_URL", "")


@tool
def call_api(data: dict) -> str:
    """Call the OKO API to perform actions or modifications.

    Start with {"action": "help"} to discover all available actions and parameters.
    Use this tool for ALL data modifications (never edit through the browser).

    Args:
        data: Dict with at least "action" key, plus any action-specific parameters.

    Returns:
        JSON string with the API response.
    """
    payload = {"apikey": AGENT_API_KEY, "task": "okoeditor", "answer": data}
    log.info("call_api: POST %s/verify answer=%s", HUB_URL, json.dumps(data, ensure_ascii=False))
    resp = session.post(f"{HUB_URL}/verify", json=payload)
    try:
        result = resp.json()
    except Exception:
        result = {"error": resp.text, "status_code": resp.status_code}
    log.info("call_api: status=%d response=%s", resp.status_code, json.dumps(result, ensure_ascii=False))
    return json.dumps(result, ensure_ascii=False)


