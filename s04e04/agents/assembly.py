import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools import ASSEMBLY_TOOLS

_SYSTEM_PROMPT = """\
You are an assembly agent. Your job is to read per-entity notes from temp/ and write the
final output files into the correct output directories.

## Input
All source notes are in temp/:
- temp/miasto_*.md   — city supply needs
- temp/osoba_*.md    — person → city mapping
- temp/towar_*.md    — good → selling city mapping

## Output directories and formats

### output/miasta/{CityName}.json
One JSON file per city. Content is a flat JSON object mapping good names (nominative
singular, Polish) to integer quantities. Example:
{"chleb": 50, "ryż": 45, "woda": 175, "wiertarka": 7}

### output/osoby/{First_Last}.md
One Markdown file per person (underscore instead of space in filename).
Content: the person's full name on the first line, then a Markdown link to their city file.
Example for "Damian Kroll" who manages "Puck":
```
Damian Kroll
[Puck](../miasta/Puck.json)
```

### output/towary/{good}.md
One Markdown file per good (nominative singular, lowercase).
Content: a Markdown link to the city that sells this good.
Example for "ryż" sold by "Darzlubie":
```
[Darzlubie](../miasta/Darzlubie.json)
```

## Workflow (one tool call at a time)
1. list_dir("temp") to see all available notes.
2. Read each note file one by one.
3. After reading all notes, write output files one by one:
   a. For each miasto note → write output/miasta/{CityName}.json
   b. For each osoba note  → write output/osoby/{First_Last}.md
   c. For each towar note  → write output/towary/{good}.md
4. When all output files are written, stop.

## Rules
- Call ONE tool at a time. Wait for the result before calling the next tool.
- City names in filenames keep their original Polish spelling (e.g. "Domatowo.json").
- Good names in filenames are nominative singular lowercase (e.g. "wiertarka.md").
- Person filenames use underscore instead of space (e.g. "Natan_Rams.md").
- Do NOT add extra commentary inside the output files — only the required content.
- JSON must be valid (no trailing commas).
"""


ASSEMBLY_SUBAGENT = {
    "name": "assembly",
    "description": (
        "Assembly agent — reads per-entity notes from temp/ and writes final output files "
        "to output/miasta/, output/osoby/, and output/towary/."
    ),
    "system_prompt": _SYSTEM_PROMPT,
    "tools": ASSEMBLY_TOOLS,
    "model": ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
}
