from langchain_core.tools import tool
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "memory"


@tool
def list_memories() -> str:
    """List all files available in the memory directory."""
    print(">>> [list_memories]")
    if not MEMORY_DIR.exists():
        return "Memory directory does not exist."
    files = sorted(p.name for p in MEMORY_DIR.iterdir() if p.is_file())
    result = "\n".join(files) if files else "No files found in memory."
    print(f"<<< [list_memories] {len(files)} files")
    return result
