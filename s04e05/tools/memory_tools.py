import os
from pathlib import Path

from langchain_core.tools import tool

_MEMORY_DIR = Path(__file__).parent.parent / "memory"


def _resolve(filename: str) -> Path:
    """Resolve filename inside memory dir, preventing path traversal."""
    resolved = (_MEMORY_DIR / filename).resolve()
    if not str(resolved).startswith(str(_MEMORY_DIR.resolve())):
        raise ValueError(f"Path traversal not allowed: {filename}")
    return resolved


@tool
def write_memory(filename: str, content: str) -> str:
    """Write content to a file in the memory directory.

    Args:
        filename: File name (e.g. "city_Warszawa.md"). No subdirectories allowed.
        content: Text content to write.
    """
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    target = _resolve(filename)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} chars to memory/{filename}"


@tool
def read_memory(filename: str) -> str:
    """Read a file from the memory directory.

    Args:
        filename: File name to read (e.g. "city_Warszawa.md").
    """
    target = _resolve(filename)
    if not target.exists():
        return f"(file does not exist: memory/{filename})"
    return target.read_text(encoding="utf-8")


@tool
def list_memories() -> str:
    """List all files currently stored in the memory directory."""
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(f.name for f in _MEMORY_DIR.iterdir() if f.is_file())
    return "\n".join(files) if files else "(memory directory is empty)"
