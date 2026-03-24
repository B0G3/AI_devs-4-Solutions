import os

import requests
from langchain_core.tools import tool

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")


@tool
def run_command(cmd: str) -> dict:
    """Run a shell command on the remote server.

    Args:
        cmd: The shell command to execute.

    Returns:
        The JSON response from the hub.
    """
    payload = {
        "apikey": AGENT_API_KEY,
        "cmd": cmd,
    }
    print(f">>> [run_command] cmd={cmd!r}")
    response = requests.post(f"{HUB_URL}/api/shell", json=payload)

    try:
        result = response.json()
    except Exception:
        result = {"error": response.text, "status_code": response.status_code}

    print(f"<<< [run_command] {result}")
    return result


@tool
def verify_answer(confirmation: str) -> dict:
    """Submit the code obtained from the firmware to headquarters for verification.

    Args:
        confirmation: The code displayed after running the firmware.

    Returns:
        The JSON response from the hub.
    """
    payload = {
        "apikey": AGENT_API_KEY,
        "task": "firmware",
        "answer": {
            "confirmation": confirmation,
        },
    }
    print(f">>> [verify_answer] confirmation={confirmation!r}")
    response = requests.post(f"{HUB_URL}/verify", json=payload)

    try:
        result = response.json()
    except Exception:
        result = {"error": response.text, "status_code": response.status_code}

    print(f"<<< [verify_answer] {result}")
    return result
