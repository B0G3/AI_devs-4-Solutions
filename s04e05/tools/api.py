import json
import os

import requests
from langchain_core.tools import tool

from logger import get_logger

log = get_logger("tools.api")

HUB_URL = os.environ.get("HUB_URL", "")
HUB_API_KEY = os.environ.get("HUB_API_KEY", "")


@tool
def call_api(tool_name: str, params: dict = None) -> str:
    """Call the foodwarehouse hub API.

    Args:
        tool_name: The tool/action to invoke (e.g. "help", "getOrders", "addOrder", "done", "reset").
        params: Optional dict of additional parameters for the tool.
    """
    answer: dict = {"tool": tool_name}
    if params:
        answer.update(params)

    payload = {
        "apikey": HUB_API_KEY,
        "task": "foodwarehouse",
        "answer": answer,
    }
    log.info("→ %s", json.dumps(answer, ensure_ascii=False))
    resp = requests.post(f"{HUB_URL.rstrip('/')}/verify", json=payload, timeout=30)
    try:
        result = resp.json()
    except Exception:
        result = {"error": resp.text, "status_code": resp.status_code}
    log.info("← %s", json.dumps(result, ensure_ascii=False))
    return json.dumps(result, ensure_ascii=False)
