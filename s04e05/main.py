from dotenv import load_dotenv

load_dotenv()

from agents import run
from logger import LOG_FILE, get_logger

log = get_logger("main")

TASK = """\
- Determine which cities are part of the operation based on food4cities.json
- Find the correct destination value for each of those cities
- Read from food4cities.json what goods and quantities are needed in each city
- Prepare a separate order for each required city
- Each order must have a correct creatorID, destination, and signature generated from the SQLite database
- Fill each order with exactly the goods the city needs — no missing items, no extras
- When everything is ready, call the done tool
"""

if __name__ == "__main__":
    log.info("=== s04e05 start === log: %s", LOG_FILE)
    result = run(TASK)
    log.info("result: %s", result)
    log.info("=== s04e05 done ===")
