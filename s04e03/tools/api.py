import json
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger

log = get_logger("api")

HUB_API_KEY = os.getenv("HUB_API_KEY", "")
HUB_URL = os.getenv("HUB_URL", "")

TOOL_DEF = {
    "type": "function",
    "name": "call_api",
    "description": (
        "Call the Domatowo game API. "
        "Start with action='help' to discover all available actions and their costs. "
        "Then use action='map' to fetch the terrain grid. "
        "Pass all action-specific fields as top-level arguments alongside action."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The game action to perform (e.g. 'help', 'map', 'move', 'inspect', 'helicopter').",
            },
        },
        "required": ["action"],
        "additionalProperties": True,
    },
}


def reset_game() -> dict:
    data = {"action": "reset"}
    payload = {"apikey": HUB_API_KEY, "task": "domatowo", "answer": data}
    log.info("→ %s", json.dumps(data))
    resp = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    result = resp.json() if resp.ok else {"error": resp.text}
    log.info("← %s", json.dumps(result))
    return result


def call_api(action: str, **kwargs) -> str:
    data = {"action": action, **kwargs}
    payload = {"apikey": HUB_API_KEY, "task": "domatowo", "answer": data}
    log.info("→ %s", json.dumps(data, ensure_ascii=False))
    resp = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    try:
        result = resp.json()
    except Exception:
        result = {"error": resp.text, "status_code": resp.status_code}
    log.info("← %s", json.dumps(result, ensure_ascii=False))
    return json.dumps(result, ensure_ascii=False)
