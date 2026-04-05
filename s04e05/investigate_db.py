"""Query the database to find correct city destinations and creator assignments."""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

HUB_URL = os.environ["HUB_URL"].rstrip("/")
HUB_API_KEY = os.environ["HUB_API_KEY"]


def call_api(answer: dict) -> dict:
    payload = {"apikey": HUB_API_KEY, "task": "foodwarehouse", "answer": answer}
    resp = requests.post(f"{HUB_URL}/verify", json=payload, timeout=30)
    return resp.json()


def db(query: str) -> dict:
    result = call_api({"tool": "database", "query": query})
    print(f"Q: {query}")
    print(f"R: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
    return result


# Schema
db("show tables")
db(".schema")
