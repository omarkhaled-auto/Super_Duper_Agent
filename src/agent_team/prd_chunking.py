"""PRD chunking utilities for handling large PRD files.

When a PRD exceeds the size threshold, it is split into focused section chunks
before the PRD Analyzer Fleet is deployed. This prevents context overflow for
very large PRDs (e.g., 80KB+).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import PRDChunkingConfig

# Section detection patterns - map PRD headings to analysis focus areas
_SECTION_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"features?|user\s+stories?|requirements?", re.I), "features", "Extract features and user stories"),
    (re.compile(r"database|schema|data\s+model|entities", re.I), "database", "Map data models and database schema"),
    (re.compile(r"api|endpoints?|rest|graphql|routes", re.I), "api", "Identify API endpoints and integrations"),
    (re.compile(r"frontend|ui|ux|components?|pages?|views?", re.I), "frontend", "Map frontend pages and components"),
    (re.compile(r"auth|authentication|authorization|security|permissions?", re.I), "auth", "Identify authentication needs"),
    (re.compile(r"infrastructure|deployment|devops|docker|ci.?cd", re.I), "infrastructure", "Map infrastructure requirements"),
    (re.compile(r"testing|tests?|acceptance|quality", re.I), "testing", "Identify testing requirements"),
    (re.compile(r"dependencies|third.party|external|integrations?", re.I), "dependencies", "Identify external dependencies"),
    (re.compile(r"appendix|reference|glossary", re.I), "appendix", "Reference material"),
]


@dataclass
class PRDChunk:
    """Represents a chunk of the PRD."""

    name: str
    focus: str
    description: str
    file: str
    start_line: int
    end_line: int
    size_bytes: int

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


def detect_large_prd(content: str, threshold: int = 80000) -> bool:
    """Check if PRD exceeds size threshold for chunking.

    Args:
        content: PRD content as string
        threshold: Size threshold in bytes (default 80KB)

    Returns:
        True if PRD size exceeds threshold
    """
    return len(content.encode("utf-8")) > threshold


def _find_section_boundaries(content: str) -> list[tuple[int, int, str, str]]:
    """Find major section boundaries in PRD content.

    Returns list of (start_line, end_line, section_name, heading_text).
    """
    lines = content.split("\n")
    sections: list[tuple[int, int, str, str]] = []
    current_section_start = 0
    current_section_name = "overview"
    current_heading = "Overview"

    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$")

    for i, line in enumerate(lines):
        match = heading_pattern.match(line)
        if match:
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()

            # Only split on top-level headings (# or ##)
            if heading_level <= 2:
                # Save previous section
                if i > current_section_start:
                    sections.append((current_section_start, i - 1, current_section_name, current_heading))

                # Detect section type
                section_name = "general"
                for pattern, name, _ in _SECTION_PATTERNS:
                    if pattern.search(heading_text):
                        section_name = name
                        break

                current_section_start = i
                current_section_name = section_name
                current_heading = heading_text

    # Add final section
    sections.append((current_section_start, len(lines) - 1, current_section_name, current_heading))

    return sections


def _get_focus_description(section_name: str) -> str:
    """Get analysis focus description for a section type."""
    for _, name, description in _SECTION_PATTERNS:
        if name == section_name:
            return description
    return "Analyze this section for relevant requirements"


def create_prd_chunks(
    content: str,
    output_dir: Path,
    max_chunk_size: int = 20000,
) -> list[PRDChunk]:
    """Split PRD into chunk files based on section boundaries.

    Args:
        content: Full PRD content
        output_dir: Directory to write chunk files
        max_chunk_size: Target max size per chunk in bytes (unused currently,
                        reserved for future splitting of large sections)

    Returns:
        List of PRDChunk metadata objects
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = content.split("\n")
    sections = _find_section_boundaries(content)

    chunks: list[PRDChunk] = []
    chunk_counter: dict[str, int] = {}  # Track duplicates

    for start_line, end_line, section_name, heading in sections:
        # Handle duplicate section names
        if section_name in chunk_counter:
            chunk_counter[section_name] += 1
            unique_name = f"{section_name}_{chunk_counter[section_name]}"
        else:
            chunk_counter[section_name] = 1
            unique_name = section_name

        # Extract section content
        section_lines = lines[start_line : end_line + 1]
        section_content = "\n".join(section_lines)

        # Skip very small sections (< 100 bytes)
        if len(section_content.encode("utf-8")) < 100:
            continue

        # Write chunk file
        chunk_file = output_dir / f"{unique_name}.md"
        chunk_file.write_text(section_content, encoding="utf-8")

        chunks.append(
            PRDChunk(
                name=unique_name,
                focus=_get_focus_description(section_name),
                description=heading,
                file=f".agent-team/prd-chunks/{unique_name}.md",
                start_line=start_line + 1,  # 1-indexed for display
                end_line=end_line + 1,
                size_bytes=len(section_content.encode("utf-8")),
            )
        )

    return chunks


def build_prd_index(content: str) -> dict[str, dict]:
    """Create structured index of PRD for orchestrator reference.

    Returns dict mapping section names to metadata.
    """
    sections = _find_section_boundaries(content)
    lines = content.split("\n")

    index: dict[str, dict] = {}
    for start_line, end_line, section_name, heading in sections:
        section_content = "\n".join(lines[start_line : end_line + 1])
        size = len(section_content.encode("utf-8"))

        # Skip tiny sections
        if size < 100:
            continue

        # Create brief summary (first 200 chars of non-heading content)
        summary_lines = [
            line
            for line in lines[start_line : min(start_line + 10, end_line)]
            if line.strip() and not line.startswith("#")
        ]
        summary = " ".join(summary_lines)[:200] + "..." if summary_lines else heading

        index[section_name] = {
            "heading": heading,
            "summary": summary,
            "line_range": f"{start_line + 1}-{end_line + 1}",
            "size_bytes": size,
            "focus": _get_focus_description(section_name),
        }

    return index


def validate_chunks(chunks: list[PRDChunk], output_dir: Path) -> bool:
    """Validate that all chunk files exist and are readable.

    Args:
        chunks: List of PRDChunk objects to validate
        output_dir: Directory containing chunk files

    Returns:
        True if all chunks are valid, False otherwise
    """
    for chunk in chunks:
        chunk_path = output_dir / f"{chunk.name}.md"
        if not chunk_path.is_file():
            return False
        try:
            chunk_path.read_text(encoding="utf-8")
        except Exception:
            return False
    return True
