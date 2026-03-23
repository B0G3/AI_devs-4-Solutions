import io
import json
import os
import re
import zipfile
from pathlib import Path

import requests
from langchain_core.tools import tool

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

_BASE_DIR = Path(__file__).parent.parent
_DATA_DIR = _BASE_DIR / "data" / "initial"
_FILTERED_DIR = _BASE_DIR / "data" / "filtered"

VALID_RANGES = {
    "temperature_K":      (553, 873),
    "pressure_bar":       (60, 160),
    "water_level_meters": (5.0, 15.0),
    "voltage_supply_v":   (229.0, 231.0),
    "humidity_percent":   (40.0, 80.0),
}

SENSOR_FIELDS = {
    "temperature": "temperature_K",
    "pressure":    "pressure_bar",
    "water":       "water_level_meters",
    "voltage":     "voltage_supply_v",
    "humidity":    "humidity_percent",
}


def _is_invalid(reading: dict) -> bool:
    sensor_type = reading.get("sensor_type", "")
    for field, (lo, hi) in VALID_RANGES.items():
        value = reading.get(field, 0)
        field_key = next((k for k, v in SENSOR_FIELDS.items() if v == field), None)
        sensor_measures_this = field_key is not None and field_key in sensor_type
        if sensor_measures_this:
            if not (lo <= value <= hi):
                return True
        else:
            if value != 0:
                return True
    return False


@tool
def download_logs() -> str:
    """Download and unpack sensor data from the hub.

    Fetches sensors.zip and extracts all JSON files to the local data/initial/ directory.

    Returns:
        Confirmation message with the number of extracted files.
    """
    url = f"{HUB_URL}/dane/sensors.zip"
    print(f">>> [download_logs] fetching {url}")
    response = requests.get(url)
    response.raise_for_status()

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        json_files = [name for name in zf.namelist() if name.endswith(".json")]
        for name in json_files:
            zf.extract(name, _DATA_DIR)

    result = f"Extracted {len(json_files)} JSON files to {_DATA_DIR}"
    print(f"<<< [download_logs] {result}")
    return result


@tool
def filter_logs() -> list[str]:
    """Filter downloaded sensor logs to find all invalid readings.

    Checks each sensor reading against two rules:
    - Measurement value is outside the valid range for its sensor type
    - Sensor reports a non-zero value for a field it should not be measuring
      (e.g. a water level sensor reporting a non-zero voltage value)

    Copies invalid files to data/filtered/ and returns their IDs.

    Returns:
        List of invalid sensor IDs (file stems).
    """
    _FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    invalid = []
    for path in sorted(_DATA_DIR.rglob("*.json")):
        reading = json.loads(path.read_text())
        if _is_invalid(reading):
            invalid.append(path.stem)
            (_FILTERED_DIR / path.name).write_text(path.read_text())

    print(f">>> [filter_logs] found {len(invalid)} invalid sensors: {invalid}")
    return invalid


_DATA_ROOT = _BASE_DIR / "data"


def _safe_path(path: str) -> Path:
    resolved = (_DATA_ROOT / path).resolve()
    if not str(resolved).startswith(str(_DATA_ROOT.resolve())):
        raise ValueError(f"Path '{path}' is outside the allowed data directory")
    return resolved


@tool
def read_file(path: str) -> str:
    """Read a file from the data directory and return its contents.

    Args:
        path: File path relative to the s03e01/data/ directory.

    Returns:
        File contents as a string.
    """
    file_path = _safe_path(path)
    print(f">>> [read_file] reading {file_path}")
    result = file_path.read_text()
    print(f"<<< [read_file] {len(result)} chars")
    return result


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file in the data directory.

    Args:
        path: File path relative to the s03e01/data/ directory.
        content: Content to write.

    Returns:
        Confirmation message.
    """
    file_path = _safe_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    result = f"Wrote {len(content)} chars to {file_path}"
    print(f">>> [write_file] {result}")
    return result


@tool
def grep(pattern: str, path: str = "") -> list[str]:
    """Search for a regex pattern across files in the data directory.

    Args:
        pattern: Regular expression pattern to search for.
        path: Optional subdirectory or file path relative to s03e01/data/.
              Defaults to searching all files under data/.

    Returns:
        List of matching lines in the format "filename:line_number: line_content".
    """
    search_root = _safe_path(path) if path else _DATA_ROOT.resolve()
    compiled = re.compile(pattern)
    matches = []

    paths = [search_root] if search_root.is_file() else sorted(search_root.rglob("*"))
    for file_path in paths:
        if not file_path.is_file():
            continue
        try:
            for i, line in enumerate(file_path.read_text().splitlines(), start=1):
                if compiled.search(line):
                    matches.append(f"{file_path.relative_to(_DATA_ROOT)}:{i}: {line}")
        except Exception:
            continue

    print(f">>> [grep] pattern={pattern!r} path={path!r} → {len(matches)} match(es)")
    return matches


@tool
def send_to_hub(invalid_ids: list[str]) -> dict:
    """Submit the list of invalid sensor IDs to the hub for verification.

    Args:
        invalid_ids: List of sensor IDs (file stems) that are invalid.

    Returns:
        JSON response from the hub. Contains a flag {FLG:...} when the answer is correct.
    """
    payload = {
        "apikey": AGENT_API_KEY,
        "task": "evaluation",
        "answer": {"recheck": invalid_ids},
    }
    print(f">>> [send_to_hub] invalid_ids={invalid_ids}")
    response = requests.post(f"{HUB_URL}/verify", json=payload)

    try:
        result = response.json()
    except Exception:
        result = {"error": response.text, "status_code": response.status_code}

    print(f"<<< [send_to_hub] {result}")
    return result
