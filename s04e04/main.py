import io
import json
import os
import re
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

from logger import LOG_FILE, get_logger

log = get_logger("main")

HUB_URL = os.environ["HUB_URL"]
HUB_API_KEY = os.environ["HUB_API_KEY"]
ORIGINAL_DIR = Path(__file__).parent / "original"
OUTPUT_DIR = Path(__file__).parent / "output"


def fetch_and_extract() -> None:
    url = f"{HUB_URL.rstrip('/')}/dane/natan_notes.zip"
    log.info("Fetching %s", url)
    response = requests.get(url)
    response.raise_for_status()
    log.info("Downloaded %d bytes", len(response.content))

    ORIGINAL_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(ORIGINAL_DIR)
        extracted = zf.namelist()
    log.info("Extracted %d files to %s", len(extracted), ORIGINAL_DIR)
    for name in extracted:
        log.info("  %s", name)


_POLISH = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ",
)


def strip_polish(text: str) -> str:
    return text.translate(_POLISH)


def _hub_name(name: str) -> str:
    """Lowercase, strip Polish diacritics, replace non-alphanumeric chars with underscore."""
    name = strip_polish(name).lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name


def _fix_links(text: str) -> str:
    """Rewrite markdown links from ../subdir/Name.ext to /subdir/name (hub format)."""
    def repl(m: re.Match) -> str:
        label = strip_polish(m.group(1))
        href = m.group(2)
        p = Path(href.replace("../", ""))
        subdir = p.parent.name
        fname = _hub_name(p.stem)
        new_href = f"/{subdir}/{fname}" if subdir else f"/{fname}"
        return f"[{label}]({new_href})"
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)


def _miasto_to_json(raw: str) -> str:
    """Sanitize city JSON: strip Polish from keys, ensure integer values."""
    data = json.loads(raw)
    clean = {_hub_name(k): int(v) for k, v in data.items()}
    return json.dumps(clean, ensure_ascii=True)


def _post(actions: list[dict]) -> dict:
    payload = {"apikey": HUB_API_KEY, "task": "filesystem", "answer": actions}
    log.info("→ %d action(s): %s", len(actions), json.dumps(actions, ensure_ascii=False)[:300])
    response = requests.post(f"{HUB_URL.rstrip('/')}/verify", json=payload, timeout=30)
    log.info("← HTTP %s: %s", response.status_code, response.text[:300])
    response.raise_for_status()
    return response.json()


def submit_output() -> None:
    # 1. Reset
    _post([{"action": "reset"}])

    # 2. Create directories
    _post([
        {"action": "createDirectory", "path": "/miasta"},
        {"action": "createDirectory", "path": "/osoby"},
        {"action": "createDirectory", "path": "/towary"},
    ])

    # 3. Create files (miasta first so links to them resolve correctly)
    file_actions: list[dict] = []
    for subdir in ["miasta", "osoby", "towary"]:
        src_dir = OUTPUT_DIR / subdir
        if not src_dir.exists():
            continue

        if subdir == "towary":
            # Merge chleb.md + chleb_2.md + chleb_3.md → one /towary/chleb file
            groups: dict[str, list[str]] = {}
            for file_path in sorted(src_dir.iterdir()):
                if not file_path.is_file():
                    continue
                base = _hub_name(re.sub(r"_\d+$", "", file_path.stem))
                raw = _fix_links(strip_polish(file_path.read_text(encoding="utf-8")))
                groups.setdefault(base, []).append(raw.strip())
            for name, parts in sorted(groups.items()):
                hub_path = f"/{subdir}/{name}"
                content = "\n".join(parts)
                file_actions.append({"action": "createFile", "path": hub_path, "content": content})
                log.info("  queued %s (%d links)", hub_path, len(parts))
        else:
            for file_path in sorted(src_dir.iterdir()):
                if not file_path.is_file():
                    continue
                name = _hub_name(file_path.stem)
                hub_path = f"/{subdir}/{name}"
                raw = file_path.read_text(encoding="utf-8")
                content = _miasto_to_json(raw) if subdir == "miasta" else _fix_links(strip_polish(raw))
                file_actions.append({"action": "createFile", "path": hub_path, "content": content})
                log.info("  queued %s (%d chars)", hub_path, len(content))
    _post(file_actions)

    # 4. Verify / done (single object, not array)
    payload = {"apikey": HUB_API_KEY, "task": "filesystem", "answer": {"action": "done"}}
    log.info("→ done")
    response = requests.post(f"{HUB_URL.rstrip('/')}/verify", json=payload, timeout=30)
    log.info("← HTTP %s: %s", response.status_code, response.text)
    result = response.json()
    log.info("Final result: %s", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    log.info("=== s04e04 start === log file: %s", LOG_FILE)
    fetch_and_extract()

    from agents import run

    # result = run(
    #     "Process Natan Rams's notes: extract all cities, people, and goods, "
    #     "then write the final memory files to output/."
    # )
    # log.info("Pipeline result: %s", result)

    submit_output()
    log.info("=== s04e04 done ===")
