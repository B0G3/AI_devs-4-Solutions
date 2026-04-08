import json
import os
import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logger import get_logger
from tools import receive_transmission, submit_response

log = get_logger("radio_operator")

TRANSMISSION_PATH = os.path.join(os.path.dirname(__file__), "..", "temp", "transmission.json")

_SYSTEM_PROMPT = """\
You are a radio operator analyst. You will receive a JSON transmission history and must extract specific information from it.
Respond with ONLY a valid JSON object — no markdown, no explanation.
"""

_USER_PROMPT = """\
Analyze the following radio transmission history and extract:

- cityName: real name of the city referred to as "Syjon"
- cityArea: area of the city in square km, rounded to exactly 2 decimal places (e.g. "12.34")
- warehousesCount: number of warehouses in Syjon (positive integer, minimum 1)
- phoneNumber: phone number of the contact person from Syjon

Respond with ONLY a JSON object in this exact format:
{"cityName": "...", "cityArea": "12.34", "warehousesCount": 5, "phoneNumber": "..."}

Transmission history:
"""


def run() -> str:
    log.info("radio_operator: starting")

    # Step 1: Receive transmission if not already downloaded
    if not os.path.exists(TRANSMISSION_PATH):
        log.info("radio_operator: transmission.json not found — downloading")
        receive_transmission()
        log.info("radio_operator: transmission saved to %s", TRANSMISSION_PATH)
        log.info("radio_operator: review and alter objects in temp/ as needed, then re-run")
        return "Transmission downloaded. Review temp/ contents and re-run."

    # Step 2: Read transmission.json — extract only the "out" field from each message
    with open(TRANSMISSION_PATH, encoding="utf-8") as f:
        history = json.load(f)
    content = "\n".join(msg.get("out", "") for msg in history if msg.get("out"))
    log.info("radio_operator: read transmission.json (%d messages)", len(history))

    # Step 3: Prompt LLM and retry on submission failure
    llm = ChatOpenAI(model="gpt-5-nano-2025-08-07", openai_api_key=os.environ["OPENAI_API_KEY"])
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_USER_PROMPT + content),
    ]

    MAX_RETRIES = 5
    for attempt in range(1, MAX_RETRIES + 1):
        response = llm.invoke(messages)
        log.info("radio_operator: llm response (attempt %d): %s", attempt, response.content)

        parsed = json.loads(response.content)

        try:
            result = submit_response(
                city_name=parsed["cityName"],
                city_area=parsed["cityArea"],
                warehouses_count=parsed["warehousesCount"],
                phone_number=parsed["phoneNumber"],
            )
            log.info("radio_operator: done")
            return result
        except Exception as e:
            error_msg = str(e)
            log.warning("radio_operator: submission failed (attempt %d): %s", attempt, error_msg)
            if attempt == MAX_RETRIES:
                raise
            messages.append(response)
            messages.append(HumanMessage(content=f"Submission failed: {error_msg}\nRevise your answer and respond again with ONLY a JSON object."))
