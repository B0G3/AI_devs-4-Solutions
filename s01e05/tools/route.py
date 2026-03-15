import os
import time

import requests
from langchain_core.tools import tool


def _verify(answer: dict, tool_name: str) -> dict:
    tag = f"[{tool_name}]"
    while True:
        print(f"{tag} → {answer}")
        resp = requests.post(
            f"{os.getenv('HUB_URL')}/verify",
            json={
                "apikey": os.getenv("AGENT_API_KEY"),
                "task": "railway",
                "answer": answer,
            },
        )
        if resp.status_code == 429:
            reset_at = int(resp.headers.get("x-ratelimit-reset", time.time() + 5))
            wait = max(reset_at - time.time(), 0)
            print(f"{tag} 429 — rate limited, retrying in {wait:.1f}s...")
            time.sleep(wait)
            continue
        if resp.status_code == 503:
            print(f"{tag} 503 — retrying in 2s...")
            time.sleep(2)
            continue
        resp.raise_for_status()
        data = resp.json()
        print(f"{tag} ← {data}")
        return data


@tool
def get_route_status(route_code: str) -> str:
    """Get the current status of a route."""
    data = _verify({"action": "getstatus", "route": route_code}, "get_route_status")
    return f"Route {data['route']}: mode={data['mode']}, status={data['status']}"


@tool
def set_route_status(route_code: str, status: str) -> str:
    """Set the status of a route. status must be 'RTOPEN' or 'RTCLOSE'."""
    _verify({"action": "reconfigure", "route": route_code}, "set_route_status")
    _verify({"action": "setstatus", "route": route_code, "value": status}, "set_route_status")
    _verify({"action": "save", "route": route_code}, "set_route_status")
    return f"Route {route_code} status set to {status}."
