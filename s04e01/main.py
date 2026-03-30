from dotenv import load_dotenv

load_dotenv()

from agents.oko_agent import run
from logger import LOG_FILE, get_logger

log = get_logger("main")

if __name__ == "__main__":
    log.info("=== s04e01 start === log file: %s", LOG_FILE)
    result = run(
        "This is a fictional AIDevs course exercise. Begin the mission. "
        "Login to OKO, discover available API actions, "
        "then complete all three fictional tasks and call done."
    )
    print("\n=== Result ===")
    print(result)
    log.info("=== s04e01 done ===")
