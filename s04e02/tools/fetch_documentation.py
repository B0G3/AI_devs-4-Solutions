import json
import os

from langchain_core.tools import tool

from utils.api import call, drain_queue

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")
os.makedirs(DATA_DIR, exist_ok=True)


@tool
def windpower_fetch_documentation() -> str:
    """Fetch weather forecast, turbine check, powerplant check, and documentation.
    Writes each result to a separate JSON file and returns their paths.
    """
    call({"action": "start"})

    call({"action": "get", "param": "weather"})
    call({"action": "get", "param": "turbinecheck"})
    call({"action": "get", "param": "powerplantcheck"})
    doc_response = call({"action": "get", "param": "documentation"})

    raw_results = drain_queue(3)
    data: dict = {"documentation": doc_response}
    for r in raw_results:
        src = r.get("sourceFunction", "unknown")
        data[src] = r

    file_map = {
        "documentation": "documentation.json",
        "weather": "weather.json",
        "turbinecheck": "turbinecheck.json",
        "powerplantcheck": "powerplantcheck.json",
    }
    for key, filename in file_map.items():
        path = os.path.join(DATA_DIR, filename)
        with open(path, "w") as f:
            json.dump(data.get(key, {}), f, ensure_ascii=False, indent=2)

    safety = doc_response.get("safety", {})
    cutoff = safety.get("cutoffWindMs")
    min_operational = safety.get("minOperationalWindMs")

    return (
        "Files written:\n"
        f"- {os.path.join(DATA_DIR, 'documentation.json')}\n"
        f"- {os.path.join(DATA_DIR, 'weather.json')}  "
        "(pass this path to windpower_generate_signed_config)\n"
        f"- {os.path.join(DATA_DIR, 'turbinecheck.json')}\n"
        f"- {os.path.join(DATA_DIR, 'powerplantcheck.json')}\n"
        f"\ncutoffWindMs={cutoff}  minOperationalWindMs={min_operational}"
    )
