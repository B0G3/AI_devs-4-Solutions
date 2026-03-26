from langchain_core.tools import tool
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "memory"


@tool
def read_memory(filename: str, keywords: str = "", offset: int = 0) -> str:
    """Read a file from the memory directory. Pass space-separated keywords to filter rows — all keywords must appear somewhere in the row (case-insensitive, order-independent). Use offset for pagination. Returns up to 2000 characters."""
    print(f">>> [read_memory] filename={filename!r} keywords={keywords!r} offset={offset}")
    path = MEMORY_DIR / filename
    if not path.exists():
        return f"File '{filename}' not found in memory."
    lines = path.read_text(encoding="utf-8").splitlines()
    header, rows = lines[:1], lines[1:]
    if keywords:
        terms = keywords.lower().split()
        rows = [r for r in rows if all(t in r.lower() for t in terms)]
    data = "\n".join(rows)[offset:offset + 2000]
    content = "\n".join(header + [data]) if data else ""
    result = content if content else f"{header[0]}\nNo rows matched."
    print(f"<<< [read_memory] {len(result)} chars")
    return result
