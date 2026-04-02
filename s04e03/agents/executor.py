import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agents.loop import run_loop
from logger import get_logger
from tools import TOOL_MAP, TOOLS

log = get_logger("executor")

MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = """\
You are a field commander executing a search-and-rescue operation in the ruins of Domatowo. \
You will receive a tactical plan. Follow it precisely, step by step.

EXECUTION RULES:
- Execute the plan in order. Do not skip steps or improvise — UNLESS the API returns a hint \
  (e.g. "getting warmer", a directional clue, or any non-empty signal in getLogs). \
  If the API hints at a location, immediately pivot: move scouts toward that area and inspect \
  those tiles before continuing the original plan.
- When calling call_api, pass all action-specific fields as top-level arguments alongside action, \
  e.g. call_api(action="create", type="transporter").
- Only inspect building tiles (house, block, church, school, parking, field). \
  Never waste AP inspecting roads or empty spaces — the partisan cannot be there.
- After every inspect action, call call_api(action="getLogs") and read the result carefully.
- If getLogs indicates the partisan has been found, immediately call \
  call_api(action="callHelicopter") with the correct tile.
- Track AP spent. If you are near the budget limit, stop creating new units.
- Never stop mid-mission, never ask for input. Keep executing until the helicopter is called \
  or you have no AP left.

OUTPUT FORMAT — end your final response with exactly these two lines (no markdown, no extra text):
STATUS: COMPLETE
SEARCHED: A1, B3, C5, ...

Use STATUS: COMPLETE if the helicopter was successfully called, STATUS: AP_EXHAUSTED otherwise.
SEARCHED must list every tile coordinate passed to inspect during this run, comma-separated.
"""


def run(plan: str) -> str:
    log.info("run: starting execution")
    task = f"Execute the following tactical plan:\n\n{plan}"
    result = run_loop(MODEL, SYSTEM_PROMPT, task, TOOLS, TOOL_MAP)
    log.info("run: execution finished")
    return result
