import os
from pathlib import Path

from langchain_core.tools import tool

_BASE = Path(__file__).parent.parent


def _resolve(path: str) -> Path:
    """Resolve a path relative to the project root, preventing traversal outside it."""
    resolved = (_BASE / path).resolve()
    if not str(resolved).startswith(str(_BASE.resolve())):
        raise ValueError(f"Path traversal not allowed: {path}")
    return resolved


@tool
def list_dir(path: str) -> str:
    """List files and directories at the given path (relative to project root).

    Args:
        path: Directory path relative to project root, e.g. "original" or "temp".
    """
    target = _resolve(path)
    if not target.exists():
        return f"(directory does not exist: {path})"
    entries = sorted(target.iterdir(), key=lambda p: (p.is_dir(), p.name))
    lines = []
    for entry in entries:
        kind = "DIR " if entry.is_dir() else "FILE"
        lines.append(f"{kind}  {entry.name}")
    return "\n".join(lines) if lines else "(empty directory)"


@tool
def read_file(path: str) -> str:
    """Read and return the full text content of a file (relative to project root).

    Args:
        path: File path relative to project root, e.g. "original/rozmowy.txt".
    """
    target = _resolve(path)
    if not target.exists():
        return f"(file does not exist: {path})"
    return target.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file (relative to project root), creating directories as needed.

    Args:
        path: File path relative to project root, e.g. "temp/miasto_Puck.md".
        content: Text content to write.
    """
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} chars to {path}"
