import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from langchain_core.tools import tool

from logger import get_logger

AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
HUB_URL = os.getenv("HUB_URL", "")

log = get_logger("planning_agent")


@tool
def call_api(endpoint: str, query: str) -> str:
    """Call a hub API endpoint with a query.

    Args:
        endpoint: The API endpoint name (e.g. 'map', 'vehicles').
        query: The query string to send to the endpoint.

    Returns:
        JSON string with the API response.
    """
    log.info("call_api called: endpoint=%r query=%r", endpoint, query)
    resp = requests.post(
        f"{HUB_URL}/api/{endpoint}",
        json={"apikey": AGENT_API_KEY, "query": query},
    )
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text, "status_code": resp.status_code}
    log.info("call_api returned: status=%d body=%s", resp.status_code, json.dumps(data))
    return json.dumps(data)


@tool
def verify_answer(vehicle: str, actions: list[str]) -> str:
    """Submit the planned route for verification.

    Args:
        vehicle: The name of the chosen vehicle.
        actions: Ordered list of movement actions (e.g. 'right', 'up', 'down').

    Returns:
        JSON string with the verification response.
    """
    answer = [vehicle] + actions
    log.info("verify_answer called: answer=%r", answer)
    resp = requests.post(
        f"{HUB_URL}/verify",
        json={"apikey": AGENT_API_KEY, "task": "savethem", "answer": answer},
    )
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text, "status_code": resp.status_code}
    log.info("verify_answer returned: status=%d body=%s", resp.status_code, json.dumps(data))
    return json.dumps(data)
