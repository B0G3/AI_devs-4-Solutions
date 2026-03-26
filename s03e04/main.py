import os
import time
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from tools import TOOLS
from utils import fetch_csv_files

def _delayed_verify():
    time.sleep(5)
    verify()


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=_delayed_verify, daemon=True).start()

HUB_URL = os.getenv("HUB_URL", "")
APP_URL = os.getenv("APP_URL", "")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")


@app.post("/api/lookup-data")
async def lookup_data(request: Request):
    body = await request.json()
    params = body.get("params", "")
    print(f">>> [lookup_data] params={params!r}")

    llm = ChatOpenAI(model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))
    agent = create_agent(llm, TOOLS, system_prompt=(
        "You are a data lookup assistant. Your memory is within CSV files."
        "When asked about an item return the item and its cities (along with city codes)"
        "Use read_memory with space-separated keywords to filter rows. All keywords must appear in the row (case-insensitive, order-independent). If no results, retry with fewer keywords. "
        "Always base your answer strictly on data retrieved from memory."
    ))
    result = agent.invoke({"messages": [("human", params)]})
    output = result["messages"][-1].content
    print(f"<<< [lookup_data] {output!r}")
    return {"output": output}


def verify():
    payload = {
        "apikey": AGENT_API_KEY,
        "task": "negotiations",
        "answer": {
            "tools": [
                {
                    "URL": f"{APP_URL}/api/lookup-data",
                    "description": (
                        # "Search memory files (CSV data). "
                        "Pass a natural language query in 'params' describing what to find."
                    ),
                }
            ]
        },
    }
    response = requests.post(f"{HUB_URL}/verify", json=payload)
    print(f"Verify response: {response.status_code} {response.text}")

    check_payload = {
        "apikey": AGENT_API_KEY,
        "task": "negotiations",
        "answer": {"action": "check"},
    }
    while True:
        time.sleep(10)
        check = requests.post(f"{HUB_URL}/verify", json=check_payload)
        print(f"Check response: {check.status_code} {check.text}")
        data = check.json()
        if data.get("code", 0) == 0:
            break


if __name__ == "__main__":
    fetch_csv_files()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
