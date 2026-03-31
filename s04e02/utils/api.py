import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger

log = get_logger("api")

HUB_URL = os.getenv("HUB_URL", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")


def call(action: dict) -> dict:
    payload = {"apikey": AGENT_API_KEY, "task": "windpower", "answer": action}
    log.info("→ %s", json.dumps(action))
    r = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    if not r.ok:
        log.error("← HTTP %s: %s", r.status_code, r.text)
        r.raise_for_status()
    data = r.json()
    log.info("← %s", json.dumps(data))
    return data


def get_result_blocking() -> dict:
    while True:
        r = call({"action": "getResult"})
        if "sourceFunction" in r or "unlockCode" in r:
            return r
        time.sleep(0.5)


def drain_queue(expected: int) -> list[dict]:
    results = []
    while len(results) < expected:
        r = call({"action": "getResult"})
        if "sourceFunction" in r:
            results.append(r)
        else:
            time.sleep(0.5)
    return results
