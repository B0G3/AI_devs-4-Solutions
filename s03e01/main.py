import io
import json
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HUB_URL = os.getenv("HUB_URL")
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

DATA_DIR = Path(__file__).parent / "data" / "initial"
FILTERED_DIR = Path(__file__).parent / "data" / "filtered"

VALID_RANGES = {
    "temperature_K":       (553, 873),
    "pressure_bar":        (60, 160),
    "water_level_meters":  (5.0, 15.0),
    "voltage_supply_v":    (229.0, 231.0),
    "humidity_percent":    (40.0, 80.0),
}

# Which fields each sensor_type is expected to measure (non-zero)
SENSOR_FIELDS = {
    "temperature": "temperature_K",
    "pressure":    "pressure_bar",
    "water":       "water_level_meters",
    "voltage":     "voltage_supply_v",
    "humidity":    "humidity_percent",
}


def fetch_and_unpack_sensors() -> Path:
    url = f"{HUB_URL}/dane/sensors.zip"
    print(f"Fetching {url}...")
    response = requests.get(url)
    response.raise_for_status()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        json_files = [name for name in zf.namelist() if name.endswith(".json")]
        for name in json_files:
            zf.extract(name, DATA_DIR)

    print(f"Extracted {len(json_files)} JSON file(s) to {DATA_DIR}")
    return DATA_DIR


def is_invalid(reading: dict) -> bool:
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


def find_invalid_sensors(data_dir: Path) -> list[str]:
    FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    invalid = []
    for path in sorted(data_dir.rglob("*.json")):
        reading = json.loads(path.read_text())
        if is_invalid(reading):
            invalid.append(path.stem)
            (FILTERED_DIR / path.name).write_text(path.read_text())
    print(f"Invalid sensors ({len(invalid)}): {invalid}")
    return invalid


def write_unique_notes_json(data_dir: Path) -> None:
    """Write all unique operator_notes to a single JSON file for batch classification."""
    seen = set()
    unique = []
    for path in sorted(data_dir.rglob("*.json")):
        note = json.loads(path.read_text()).get("operator_notes", "")
        if note and note not in seen:
            seen.add(note)
            unique.append({"note": note})

    out = Path(__file__).parent / "data" / "unique_notes.json"
    out.write_text(json.dumps(unique, indent=4, ensure_ascii=False))
    print(f"Wrote {len(unique)} unique notes to {out}")


# NOTE: In a real-world scenario where results aren't needed immediately,
# the OpenAI Batch API would be preferred here — it's 50% cheaper and handles
# large volumes asynchronously (completion_window="24h").
def classify_notes(notes_path: Path | None = None) -> dict[str, bool]:
    """Classify each unique operator note as working (True) or not (False). Uses cache if available."""
    cache_path = Path(__file__).parent / "data" / "unique_notes_classified.json"
    if cache_path.exists():
        print(f"Loading note classifications from cache: {cache_path}")
        classified = json.loads(cache_path.read_text())
        return {item["note"]: item["is_working"] for item in classified}

    if notes_path is None:
        notes_path = Path(__file__).parent / "data" / "unique_notes.json"
    notes = json.loads(notes_path.read_text())
    print(f"Classifying {len(notes)} notes via OpenAI API...")

    client = OpenAI()
    system_prompt = (
        "You are a sensor maintenance classifier. "
        "Given an operator note about a sensor, determine if the sensor is working properly. "
        "Answer only YES if the sensor is working properly, or NO if there is a problem."
    )

    def classify_one(i: int, note: str) -> tuple[int, bool]:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Operator note: {note}"},
            ],
            max_tokens=5,
        )
        text = response.choices[0].message.content.strip().upper()
        return i, text.startswith("YES")

    answers: dict[int, bool] = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(classify_one, i, item["note"]): i for i, item in enumerate(notes)}
        for done, future in enumerate(as_completed(futures), 1):
            i, is_working = future.result()
            answers[i] = is_working
            if done % 100 == 0 or done == len(notes):
                print(f"  Classified {done}/{len(notes)}")

    classified = [
        {"note": notes[i]["note"], "is_working": answers[i]}
        for i in range(len(notes))
    ]
    cache_path.write_text(json.dumps(classified, indent=4, ensure_ascii=False))
    print(f"Wrote {len(classified)} classified notes to {cache_path}")

    return {item["note"]: item["is_working"] for item in classified}


def find_operator_invalid_sensors(data_dir: Path, note_classifications: dict[str, bool]) -> list[str]:
    """Find sensors where the operator note flags a problem but data rules passed."""
    operator_invalid = []
    for path in sorted(data_dir.rglob("*.json")):
        reading = json.loads(path.read_text())
        note = reading.get("operator_notes", "")
        if not is_invalid(reading) and not note_classifications.get(note, True):
            operator_invalid.append(path.stem)
    print(f"Operator-reported invalid (missed by data rules): {len(operator_invalid)}")
    return operator_invalid


if __name__ == "__main__":
    sensors_dir = fetch_and_unpack_sensors()
    write_unique_notes_json(sensors_dir)
    note_classifications = classify_notes()

    invalid = find_invalid_sensors(sensors_dir)
    operator_invalid = find_operator_invalid_sensors(sensors_dir, note_classifications)

    all_invalid = sorted(set(invalid + operator_invalid))

    payload = {
        "apikey": AGENT_API_KEY,
        "task": "evaluation",
        "answer": {"recheck": all_invalid},
    }
    response = requests.post(f"{HUB_URL}/verify", json=payload)
    print(f"\nResponse ({response.status_code}): {response.text}")
