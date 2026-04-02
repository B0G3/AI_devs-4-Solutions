import os
import sys

from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools import RESEARCH_TOOLS

_SYSTEM_PROMPT = """\
You are a research agent. Your job is to read source notes left by Natan Rams and extract
structured information about cities (miasta), people (osoby), and goods (towary).

## Source files (all under original/)
- original/ogłoszenia.txt  — city supply requests with quantities
- original/rozmowy.txt     — diary entries: who Natan spoke with, which city they manage
- original/transakcje.txt  — transactions: which city sold which good to which other city

## Your workflow (strictly one tool call at a time)
1. List original/ to confirm source files exist.
2. Read each source file in turn.
3. After reading ALL three files, extract the following entities:

### Cities (miasta)
For every city mentioned in ogłoszenia.txt, extract the goods it needs and their quantities.
Quantities MUST be the exact integer numbers from the text — never use "?" or placeholders.
Example: "podrzuci 45 chlebów, 120 butelek wody i 6 młotków" → chleb: 45, woda: 120, młotek: 6.
Use the nominative singular form for good names (e.g. "chleb" not "chlebów"; "łopata" not "łopat";
"wiertarka" not "wiertarek"; "butelka wody" → just "woda"; etc.)

### People (osoby)
From rozmowy.txt, identify the full name (first + last) of the person who manages trade in
each city. Natan Rams himself manages Domatowo. Map every person to exactly one city.
IMPORTANT: first and last names may appear in different sentences — combine them.
Example: "krotki sygnal od Konkel ... Teraz to Lena pilnuje" → full name is "Lena Konkel".
Similarly "Kisiel ma do mnie dzwonic ... Rafal oddzwonil" → likely "Rafal Kisiel" for that city.
Every city must have exactly one person with a full first AND last name.

### Goods for sale (towary)
From transakcje.txt, collect every good that appears on the left side of an arrow (seller).
For each unique good (nominative singular), determine which city sells it.
If the same good appears sold by multiple cities, create a separate note per city, named
"{good}_{city}" so names stay unique.

4. Write one note file per entity into the temp/ directory:
   - temp/miasto_{CityName}.md      — one file per city
   - temp/osoba_{FirstLast}.md      — one file per person
   - temp/towar_{GoodName}.md       — one file per good (use nominative singular)

## Note format
### miasto note
```
# {CityName}
## Potrzeby
{good1}: {integer_qty1}
{good2}: {integer_qty2}
...
```
Example for Opalino: "45 chlebów, 120 butelek wody, 6 młotków" →
```
# Opalino
## Potrzeby
chleb: 45
woda: 120
młotek: 6
```

### osoba note
```
# {First} {Last}
miasto: {CityName}
```

### towar note
```
# {GoodName}
sprzedaje: {CityName}
```

## Rules
- Call ONE tool at a time. Wait for the result before calling the next.
- Use Polish nominative singular for all good names (e.g. "ryż", "chleb", "łopata",
  "marchew", "kapusta", "ziemniak", "mąka", "makaron", "wołowina", "kurczak",
  "wiertarka", "kilof", "młotek", "woda", "butelka wody" → just "woda").
- City names: use exact Polish spelling as found in the source files.
- When you have written all notes, stop.
"""


RESEARCH_SUBAGENT = {
    "name": "research",
    "description": (
        "Research agent — reads source notes (ogłoszenia, rozmowy, transakcje) and writes "
        "per-entity .md notes to temp/ for cities, people, and goods."
    ),
    "system_prompt": _SYSTEM_PROMPT,
    "tools": RESEARCH_TOOLS,
    "model": ChatOpenAI(
        model="gpt-4.1-2025-04-14",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    ),
}
