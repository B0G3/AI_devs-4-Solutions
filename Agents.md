# AI Agents Course

A hands-on course for building AI agents. Each task is a standalone Python project with its own virtual environment and dependencies.

## Project Structure

```
AIdevs/
├── Agents.md         # This file
├── s01e01/           # Season 1, Episode 1
├── s01e02/           # Season 1, Episode 2
└── ...
```

## Task Index

| Task    | Title                        | Topics                              |
|---------|------------------------------|-------------------------------------|
| s01e01  | People Classifier            | Load a CSV, filter by gender/age/city, classify jobs with OpenAI structured output (Instructor + Pydantic), POST results to a verification hub |
| s01e02  | Find Him                     | Fetch power plant locations from hub, resolve city coordinates via OpenAI, compute haversine distances, fetch person locations and access levels from hub API, submit closest high-access candidate |
| s01e03  | Logistics Agent              | FastAPI server exposing `/completion` endpoint, LangChain agent with tool use (check/redirect packages), session-based conversation history, covert destination override via Pydantic model validator; expose via ngrok and register URL with hub `/validate` |
| s01e04  | Parcel Declaration Generator | Fetch a multi-file document index from hub, resolve `[include file="..."]` directives (Markdown fetched as text, PNG fetched and OCR'd via GPT-4o vision), assemble into one complete doc, use it as system prompt to generate a formatted customs declaration for a fictional parcel, POST answer to hub |
| s01e05  | Railway Route Agent          | LangChain agent with two tools (`get_route_status`, `set_route_status`) that call hub `/verify` with structured action payloads; agent must check status, reconfigure, set status to RTOPEN, and save route X-01; flag is returned in the final assistant message |
| s02e01  | Item Hazard Classifier       | LangChain agent with tools to fetch items from a CSV, classify each sequentially via hub prompts (NEU/DNG), handle balance resets on wrong answers with cached overrides, extract flag from hub response |
| s02e02  | Circuit Puzzle               | LangChain agent with tools to fetch current/target circuit grids (image → GPT-4o vision interpretation), compute required 90° CW rotations for each cell, rotate one cell at a time until all match and flag is received |
| s02e03  | Power Plant Failure Log      | LangChain agent with tools to download a failure log, search/merge/compress critical log entries, and submit them to hub iteratively until the hub accepts and returns a flag |
| s02e04  | Mail API Agent               | LangChain agent interacting with a zmail API (help, list, get, search, decode_attachment); searches inbox for attack date, password, and SEC- confirmation code (or a hidden flag in ZIP attachments), then submits answer to hub |
| s02e05  | Drone Flight Instructions    | LangChain agent with tools to inspect drone documentation and a map, then submit a list of flight instructions to the hub; must navigate safely to a target while accounting for obstacles |
| s03e01  | Sensor Anomaly Detection     | Non-agentic pipeline: fetch sensor ZIP from hub, validate readings against per-type ranges, classify operator notes via OpenAI (parallel, with cache), union rule-based and NLP-flagged sensor IDs, POST recheck list to hub |

## Setup Convention

Each task follows the same pattern:

```bash
cd sXXeYY
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys
python main.py
```

## Environment Variables

Each task uses a local `.env` file (never committed). Copy `.env.example` and fill in values.

Common keys:
- `OPENAI_API_KEY` — your OpenAI API key
- `AGENT_API_KEY` — API key for the verification hub
- `HUB_URL` — verification hub endpoint
