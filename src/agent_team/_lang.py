"""Shared language detection utilities.

Consolidates the duplicated _LANGUAGE_MAP logic that existed in both
codebase_map.py and contracts.py (Finding #11).
"""

from __future__ import annotations

# Core language map shared between codebase_map and contracts
_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
}


def detect_language(path: str) -> str:
    """Detect programming language from file extension.

    Parameters
    ----------
    path : str
        File path (only extension is inspected).

    Returns
    -------
    str
        Lowercase language name, or ``"unknown"`` for unrecognized extensions.
    """
    from pathlib import PurePosixPath
    ext = PurePosixPath(path).suffix.lower()
    return _LANGUAGE_MAP.get(ext, "unknown")
