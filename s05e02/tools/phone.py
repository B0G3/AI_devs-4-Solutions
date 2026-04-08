import base64
import json
import os
import tempfile
import time

import requests
from langchain_core.tools import tool
from openai import OpenAI

from logger import get_logger

log = get_logger("tools.phone")

HUB_URL = os.environ["HUB_URL"]
HUB_API_KEY = os.environ["HUB_API_KEY"]
TASK = "phonecall"
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

_openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _post(answer: dict) -> dict:
    payload = {"apikey": HUB_API_KEY, "task": TASK, "answer": answer}
    log.info("→ %s", json.dumps(answer, ensure_ascii=False))
    resp = requests.post(f"{HUB_URL.rstrip('/')}/verify", json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    log.info("← code=%s message=%s", result.get("code"), result.get("message"))
    return result


def _transcribe_audio(audio_b64: str) -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)
    audio_bytes = base64.b64decode(audio_b64)
    path = os.path.join(TEMP_DIR, f"recv_{int(time.time() * 1000)}.mp3")
    with open(path, "wb") as f:
        f.write(audio_bytes)
    log.info("transcribing audio: %s (%d bytes)", path, len(audio_bytes))
    with open(path, "rb") as f:
        transcript = _openai.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="pl",
        )
    text = transcript.text
    log.info("transcript: %s", text)
    return text


@tool
def start_call() -> str:
    """Start the phone call. Returns transcribed operator greeting, or raw response if no audio."""
    log.info("start_call →")
    result = _post({"action": "start"})
    audio = result.get("audio")
    if audio:
        text = _transcribe_audio(audio)
        log.info("start_call ← operator: %s", text)
        return text
    out = json.dumps(result, ensure_ascii=False)
    log.info("start_call ← (no audio): %s", out)
    return out


@tool
def speak(message: str) -> str:
    """Speak a Polish message to the operator and return their transcribed response.

    Args:
        message: Polish message to speak to the operator.
    """
    log.info("speak → tymon: %s", message)
    tts_response = _openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=message,
        response_format="mp3",
    )
    audio_b64 = base64.b64encode(tts_response.content).decode()

    result = _post({"audio": audio_b64})
    audio = result.get("audio")
    if audio:
        text = _transcribe_audio(audio)
        log.info("speak ← operator: %s", text)
        return text
    out = json.dumps(result, ensure_ascii=False)
    log.info("speak ← (no audio): %s", out)
    return out
