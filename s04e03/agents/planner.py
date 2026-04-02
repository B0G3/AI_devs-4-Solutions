import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agents.loop import run_loop
from logger import get_logger
from tools import TOOL_MAP, TOOLS

log = get_logger("planner")

MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = """\
You are a tactical planner for a search-and-rescue operation in the ruins of Domatowo.

Your only job right now is to ANALYZE and PLAN — do not create any units, do not move \
anything, do not spend any action points.

STEPS:
1. Call call_api(action="help") to learn all available actions, parameters, and AP costs.
2. Call call_api(action="getMap") to fetch the 11×11 terrain grid.
3. Use code_interpreter to analyze the map thoroughly:
   - Label every tile (road, building type, open field, etc.)
   - Identify the road network — the only paths transporters can use.
   - Identify ALL building tiles (house, block1/2/3, church, school, parking, field) — \
     these are the ONLY tiles worth inspecting. The partisan cannot hide on roads or empty spaces.
   - Rank building tiles by hiding probability (large buildings > small houses > parking/field).
   - Calculate optimal transporter routes to deliver scouts near clusters of building tiles.
   - Determine where scouts must dismount and proceed on foot to reach each building.
   - Estimate AP cost for each phase and verify the total stays within budget.

OUTPUT — write a complete, self-contained execution plan in this format:
## AP Budget
<total available, estimated spend breakdown>

## Units to create
<list each unit: type, passengers>

## Phase 1 — Transporter movements
<ordered list: move transporter T? from X to Y, then dismount scouts>

## Phase 2 — Scout search order
<ordered list of BUILDING tiles to inspect only — no roads, no empty spaces, grouped by sector, highest priority first>

## Trigger
<what to watch for in getLogs results that confirms the partisan is found>

Do not produce any game actions. Only output the plan.
"""


def run(task: str, previously_searched: list[str] | None = None) -> str:
    log.info("run: starting")
    if previously_searched:
        task += (
            f"\n\nAlready searched in previous runs (skip these tiles entirely): "
            f"{', '.join(previously_searched)}"
        )
    plan = run_loop(MODEL, SYSTEM_PROMPT, task, TOOLS, TOOL_MAP)
    log.info("run: plan ready")
    return plan
