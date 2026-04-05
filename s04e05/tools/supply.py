import os

import requests
from langchain_core.tools import tool

from logger import get_logger

log = get_logger("tools.supply")

HUB_URL = os.environ.get("HUB_URL", "")


@tool
def get_supply_requirements() -> str:
    """Fetch the food supply requirements for all cities from food4cities.json.

    Returns the raw JSON string containing city names and their required goods/quantities.
    """
    url = f"{HUB_URL.rstrip('/')}/dane/food4cities.json"
    log.info("GET %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    log.info("← %d bytes", len(resp.text))
    return resp.text
