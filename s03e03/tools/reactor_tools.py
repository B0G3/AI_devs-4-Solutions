import os

import requests
from langchain_core.tools import tool

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")


@tool
def show_map() -> str:
    """Fetch and return the reactor map from headquarters.

    Returns:
        The HTML content of the reactor preview page.
    """
    print(">>> [show_map]")
    response = requests.get(f"{HUB_URL}/reactor_preview.html")
    result = response.text
    print(f"<<< [show_map] {len(result)} chars")
    return result


@tool
def call_api(command: str) -> dict:
    """Submit a command to the reactor API for verification.

    Args:
        command: The command to send to the reactor.

    Returns:
        The JSON response from the hub.
    """
    payload = {
        "apikey": AGENT_API_KEY,
        "task": "reactor",
        "answer": {
            "command": command,
        },
    }
    print(f">>> [call_api] command={command!r}")
    confirm = input(f"Send command {command!r}? [y/N] ").strip().lower()
    if confirm != "y":
        return {"aborted": True, "reason": "User declined to send the command."}
    response = requests.post(f"{HUB_URL}/verify", json=payload)

    try:
        result = response.json()
    except Exception:
        result = {"error": response.text, "status_code": response.status_code}

    print(f"<<< [call_api] {result}")
    return result
