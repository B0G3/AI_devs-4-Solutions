import base64
import json
import os
import time

import requests

from logger import get_logger

log = get_logger("tools.radio")

HUB_URL = os.environ["HUB_URL"]
HUB_API_KEY = os.environ["HUB_API_KEY"]
TASK = "radiomonitoring"
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")


def _verify(action: str) -> dict:
    payload = {"apikey": HUB_API_KEY, "task": TASK, "answer": {"action": action}}
    resp = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


_NOISE_PATTERNS = {"Bzzz", "ksss", "shhh", "khhh"}

_MAGIC = [
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"ID3", ".mp3"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"%PDF", ".pdf"),
]


def _guess_ext(data: bytes) -> str:
    for magic, ext in _MAGIC:
        if data[:len(magic)] == magic:
            return ext
    try:
        text = data.decode("utf-8").lstrip()
        if text.startswith("<?xml") or text.startswith("<"):
            return ".xml"
        if text.startswith("{") or text.startswith("["):
            return ".json"
        return ".csv" if "," in text.split("\n")[0] else ".txt"
    except UnicodeDecodeError:
        return ".bin"


def _process_response(result: dict) -> dict:
    """Apply noise filtering and attachment decoding to a single listen response.

    Never modifies ``transcription`` in place. Instead, sets ``result["out"]``
    to the processed value, or to the original transcription if no change is needed.
    """
    attachment = result.pop("attachment", None)
    if attachment:
        decoded = base64.b64decode(attachment)
        os.makedirs(TEMP_DIR, exist_ok=True)
        ext = _guess_ext(decoded)
        filepath = os.path.join(TEMP_DIR, f"attachment_{int(time.time() * 1000)}{ext}")
        with open(filepath, "wb") as f:
            f.write(decoded)
        try:
            result["out"] = decoded.decode("utf-8")
        except UnicodeDecodeError:
            result["out"] = filepath
    else:
        transcription = result.get("transcription", "")
        if any(noise in transcription for noise in _NOISE_PATTERNS):
            result["out"] = "*Zakłócenia*"
        else:
            result["out"] = transcription
    return result


def receive_transmission() -> str:
    """Start the radio transmission and collect the full signal.
    Loops until the server returns code 101 (signal captured).
    All intermediate messages are processed (noise filtered, attachments decoded)
    and saved together with the final signal to a single history file.
    Returns the full history as text for analysis.
    """
    log.info("receive_transmission: start →")
    result = _verify("start")
    log.info("receive_transmission: start ← %s", json.dumps(result, ensure_ascii=False))

    history = []
    MAX_ITER = 60
    for i in range(MAX_ITER):
        result = _verify("listen")
        code = result.get("code")
        log.info("receive_transmission: listen[%d] ← code=%s", i, code)
        processed = _process_response(result)
        history.append(processed)
        if code == 101:
            break
    else:
        return json.dumps({"error": "max iterations reached without code 101"})

    os.makedirs(TEMP_DIR, exist_ok=True)
    filepath = os.path.join(TEMP_DIR, "transmission.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    log.info("receive_transmission: saved history (%d messages) → %s", len(history), filepath)

    return json.dumps(history, ensure_ascii=False, indent=2)


def submit_response(city_name: str, city_area: str, warehouses_count: int, phone_number: str) -> str:
    """Submit the extracted information from the radio transmission.

    Args:
        city_name: Name of the city mentioned in the transmission.
        city_area: Area of the city in square kilometers (as a decimal string, e.g. "12.34").
        warehouses_count: Number of warehouses in the city.
        phone_number: Phone number extracted from the transmission.
    """
    payload = {
        "apikey": HUB_API_KEY,
        "task": TASK,
        "answer": {
            "action": "transmit",
            "cityName": city_name,
            "cityArea": city_area,
            "warehousesCount": warehouses_count,
            "phoneNumber": phone_number,
        },
    }
    log.info("transmit → %s", json.dumps(payload["answer"], ensure_ascii=False))
    resp = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    result = resp.json()
    output = json.dumps(result, ensure_ascii=False)
    if not resp.ok:
        log.error("transmit error %s ← %s", resp.status_code, output)
    else:
        log.info("transmit ← %s", output)
    resp.raise_for_status()
    return output
