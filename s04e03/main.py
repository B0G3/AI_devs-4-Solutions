import re

from dotenv import load_dotenv

load_dotenv()

from agents.executor import run as execute
from agents.planner import run as plan
from logger import LOG_FILE, get_logger
from tools import reset_game

log = get_logger("main")

MAX_RUNS = 5


def parse_result(text: str) -> tuple[bool, list[str]]:
    """Extract STATUS and SEARCHED lines from executor output."""
    complete = bool(re.search(r"STATUS:\s*COMPLETE", text, re.IGNORECASE))
    match = re.search(r"SEARCHED:\s*(.+)", text, re.IGNORECASE)
    searched = [t.strip() for t in match.group(1).split(",")] if match else []
    return complete, searched


if __name__ == "__main__":
    log.info("=== s04e03 start === log file: %s", LOG_FILE)

    all_searched: list[str] = []

    for run_num in range(1, MAX_RUNS + 1):
        log.info("=== run %d / %d ===", run_num, MAX_RUNS)

        log.info("--- planning ---")
        tactical_plan = plan(
            "Analyze the map of Domatowo and produce a full tactical plan for the rescue operation.",
            previously_searched=all_searched or None,
        )
        print(f"\n=== Tactical Plan (run {run_num}) ===")
        print(tactical_plan)

        log.info("--- execution ---")
        result = execute(tactical_plan)
        print(f"\n=== Execution Result (run {run_num}) ===")
        print(result)

        complete, searched_this_run = parse_result(result)
        all_searched = list(dict.fromkeys(all_searched + searched_this_run))  # deduplicated
        log.info("searched so far: %d tiles", len(all_searched))

        if complete:
            log.info("mission complete — helicopter called successfully")
            break

        if run_num < MAX_RUNS:
            log.info("resetting game for next run (%d tiles already searched)", len(all_searched))
            reset_game()
    else:
        log.info("max runs reached without finding the partisan")

    log.info("=== s04e03 done ===")
