from dotenv import load_dotenv

load_dotenv()

from agents.windpower_agent import run
from logger import LOG_FILE, get_logger

log = get_logger("main")

if __name__ == "__main__":
    log.info("=== s04e02 start === log file: %s", LOG_FILE)
    result = run("Orchestrate the wind turbine now.")
    print("\n=== Result ===")
    print(result)
    log.info("=== s04e02 done ===")
