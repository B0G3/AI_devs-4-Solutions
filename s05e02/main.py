from dotenv import load_dotenv

load_dotenv()

from agents import run
from logger import LOG_FILE, get_logger

log = get_logger("main")

if __name__ == "__main__":
    log.info("=== s05e02 start === log: %s", LOG_FILE)
    result = run()
    log.info("result: %s", result)
    log.info("=== s05e02 done ===")
