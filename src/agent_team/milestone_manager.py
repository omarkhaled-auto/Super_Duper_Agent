"""Milestone health checking and cross-milestone wiring analysis.

Implements Agent 17 (Milestone Health Monitor) and Agent 18 (Cross-Milestone
Wiring Checker).  Provides the ``MilestoneManager`` class that reads per-
milestone ``REQUIREMENTS.md`` files from ``.agent-team/milestones/{id}/``,
computes convergence health, and detects wiring gaps where one milestone
references files or symbols produced by another milestone but those files
do not yet exist or do not export the expected symbols.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .state import ConvergenceReport


# ---------------------------------------------------------------------------
# Regex patterns (reuse the review_cycles pattern from config.py)
# ---------------------------------------------------------------------------

_REVIEW_CYCLES_RE = re.compile(r'\(review_cycles:\s*(\d+)\)')
_CHECKED_RE = re.compile(r'^\s*-\s*\[x\]', re.MULTILINE | re.IGNORECASE)
_UNCHECKED_RE = re.compile(r'^\s*-\s*\[ \]', re.MULTILINE)

# Detect import references in REQUIREMENTS.md content.
# Matches patterns like:
#   import { Foo } from "src/services/bar"
#   from src.services.bar import Foo
#   imports Foo from src/services/bar.ts
_IMPORT_REF_RE = re.compile(
    r'(?:'
    r'import\s*\{?\s*(\w+)\s*\}?\s*from\s*["\']([^"\']+)["\']'  # TS/JS style
    r'|from\s+([\w./]+)\s+import\s+(\w+)'                        # Python style
    r'|imports?\s+(\w+)\s+from\s+([\w./]+)'                       # prose style
    r')',
    re.IGNORECASE,
)

# Detect file references in REQUIREMENTS.md content.
# Matches file paths like src/foo/bar.ts, lib/utils.py, etc.
_FILE_REF_RE = re.compile(
    r'(?:^|\s|[`"\'])((?:src|lib|app|server|client|packages|modules)/[\w/.-]+\.(?:py|ts|tsx|js|jsx|go|rs))',
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MilestoneState:
    """Tracks the convergence state of a single milestone."""

    milestone_id: str
    requirements_total: int = 0
    requirements_checked: int = 0
    convergence_cycles: int = 0
    status: str = "pending"  # "pending" | "in_progress" | "converged" | "failed"


@dataclass
class WiringGap:
    """Describes a missing cross-milestone wiring connection.

    Indicates that *target_milestone* references a file or symbol that
    is expected to be produced by *source_milestone*, but the file
    either does not exist or does not export the expected symbol.
    """

    source_milestone: str
    target_milestone: str
    missing_export: str
    expected_in_file: str


# ---------------------------------------------------------------------------
# MilestoneManager
# ---------------------------------------------------------------------------

class MilestoneManager:
    """Monitor milestone health and detect cross-milestone wiring gaps.

    Parameters
    ----------
    project_root : Path
        Root directory of the project.  Milestone requirements are
        expected at ``{project_root}/.agent-team/milestones/{id}/REQUIREMENTS.md``.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _milestones_dir(self) -> Path:
        """Return the base directory containing all milestone sub-directories."""
        return self.project_root / ".agent-team" / "milestones"

    def _read_requirements(self, milestone_id: str) -> str | None:
        """Read the REQUIREMENTS.md for *milestone_id*.

        Returns ``None`` when the file does not exist or cannot be read.
        """
        path = self._milestones_dir / milestone_id / "REQUIREMENTS.md"
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, PermissionError):
            return None

    def _list_milestone_ids(self) -> list[str]:
        """Return sorted list of milestone directory names."""
        milestones_dir = self._milestones_dir
        if not milestones_dir.is_dir():
            return []
        return sorted(
            d.name
            for d in milestones_dir.iterdir()
            if d.is_dir() and (d / "REQUIREMENTS.md").is_file()
        )

    @staticmethod
    def _parse_requirements_counts(content: str) -> tuple[int, int]:
        """Parse checked and total requirement counts from REQUIREMENTS.md.

        Returns
        -------
        tuple[int, int]
            ``(checked, total)`` counts.
        """
        checked = len(_CHECKED_RE.findall(content))
        unchecked = len(_UNCHECKED_RE.findall(content))
        return checked, checked + unchecked

    @staticmethod
    def _parse_max_review_cycles(content: str) -> int:
        """Parse the maximum ``review_cycles`` value from content.

        Uses the same regex pattern as :func:`config.parse_max_review_cycles`.
        """
        matches = _REVIEW_CYCLES_RE.findall(content)
        return max((int(m) for m in matches), default=0)

    @staticmethod
    def _extract_import_references(content: str) -> list[tuple[str, str]]:
        """Extract ``(symbol, file_path)`` pairs from REQUIREMENTS.md content.

        Scans for import-like references in the requirements document that
        indicate cross-module dependencies.

        Returns
        -------
        list[tuple[str, str]]
            Each tuple is ``(symbol_name, file_path)``.
        """
        refs: list[tuple[str, str]] = []
        for match in _IMPORT_REF_RE.finditer(content):
            # TS/JS style: group(1)=symbol, group(2)=path
            if match.group(1) and match.group(2):
                refs.append((match.group(1), match.group(2)))
            # Python style: group(3)=module_path, group(4)=symbol
            elif match.group(3) and match.group(4):
                refs.append((match.group(4), match.group(3)))
            # Prose style: group(5)=symbol, group(6)=path
            elif match.group(5) and match.group(6):
                refs.append((match.group(5), match.group(6)))
        return refs

    @staticmethod
    def _extract_file_references(content: str) -> list[str]:
        """Extract file path references from REQUIREMENTS.md content.

        Returns
        -------
        list[str]
            Unique file paths found in the content.
        """
        return list(dict.fromkeys(_FILE_REF_RE.findall(content)))

    def _collect_milestone_files(self, milestone_id: str) -> set[str]:
        """Collect all file paths referenced in a milestone's REQUIREMENTS.md.

        This approximates the set of files that a milestone is responsible
        for creating.
        """
        content = self._read_requirements(milestone_id)
        if not content:
            return set()
        return set(self._extract_file_references(content))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_milestone_health(self, milestone_id: str) -> ConvergenceReport:
        """Check the convergence health of a single milestone.

        Reads ``milestones/{milestone_id}/REQUIREMENTS.md``, counts
        checked vs unchecked items, and parses ``review_cycles`` markers.

        Parameters
        ----------
        milestone_id : str
            The milestone directory name (e.g. ``"milestone-1"``).

        Returns
        -------
        ConvergenceReport
            Health report with requirements counts, review cycle count,
            convergence ratio, and overall health assessment.
        """
        content = self._read_requirements(milestone_id)

        if content is None:
            return ConvergenceReport(
                total_requirements=0,
                checked_requirements=0,
                review_cycles=0,
                convergence_ratio=0.0,
                review_fleet_deployed=False,
                health="unknown",
            )

        if not content.strip():
            return ConvergenceReport(
                total_requirements=0,
                checked_requirements=0,
                review_cycles=0,
                convergence_ratio=0.0,
                review_fleet_deployed=False,
                health="unknown",
            )

        checked, total = self._parse_requirements_counts(content)
        cycles = self._parse_max_review_cycles(content)

        # Compute convergence ratio
        ratio = checked / total if total > 0 else 0.0

        # Determine health status
        if total == 0:
            health = "unknown"
        elif ratio >= 0.9:
            health = "healthy"
        elif cycles > 0 and ratio >= 0.5:
            health = "degraded"
        else:
            health = "failed"

        return ConvergenceReport(
            total_requirements=total,
            checked_requirements=checked,
            review_cycles=cycles,
            convergence_ratio=ratio,
            review_fleet_deployed=cycles > 0,
            health=health,
        )

    def get_cross_milestone_wiring(self) -> list[WiringGap]:
        """Scan all milestones for cross-milestone wiring gaps.

        For each milestone, examines import references in its
        ``REQUIREMENTS.md``.  If a reference points to a file that
        belongs to a different milestone, verifies that the file
        exists on disk.  Returns a :class:`WiringGap` for each
        missing connection.

        Returns
        -------
        list[WiringGap]
            Wiring gaps where a milestone references a file or symbol
            from another milestone that does not exist.
        """
        milestone_ids = self._list_milestone_ids()
        if not milestone_ids:
            return []

        # Build a mapping of file_path -> milestone_id for all milestones
        file_to_milestone: dict[str, str] = {}
        milestone_contents: dict[str, str] = {}

        for mid in milestone_ids:
            content = self._read_requirements(mid)
            if content is None:
                continue
            milestone_contents[mid] = content
            for file_path in self._extract_file_references(content):
                # First milestone to claim a file owns it
                if file_path not in file_to_milestone:
                    file_to_milestone[file_path] = mid

        gaps: list[WiringGap] = []

        for mid, content in milestone_contents.items():
            # Check import references
            for symbol, file_path in self._extract_import_references(content):
                owner = file_to_milestone.get(file_path)
                if owner is not None and owner != mid:
                    # Cross-milestone reference: verify the file exists
                    full_path = self.project_root / file_path
                    if not full_path.is_file():
                        gaps.append(WiringGap(
                            source_milestone=owner,
                            target_milestone=mid,
                            missing_export=symbol,
                            expected_in_file=file_path,
                        ))

            # Check file references that belong to other milestones
            for file_path in self._extract_file_references(content):
                owner = file_to_milestone.get(file_path)
                if owner is not None and owner != mid:
                    full_path = self.project_root / file_path
                    if not full_path.is_file():
                        # Avoid duplicate gaps (already caught via import refs)
                        already_reported = any(
                            g.expected_in_file == file_path
                            and g.target_milestone == mid
                            for g in gaps
                        )
                        if not already_reported:
                            gaps.append(WiringGap(
                                source_milestone=owner,
                                target_milestone=mid,
                                missing_export="(file)",
                                expected_in_file=file_path,
                            ))

        return gaps

    def verify_milestone_exports(self, milestone_id: str) -> list[str]:
        """Verify that files created by a milestone are available for dependents.

        After milestone N completes, scan milestone N+1 (and later
        milestones) for references to files that milestone N is
        responsible for.  Verify those files exist on disk.

        Parameters
        ----------
        milestone_id : str
            The completed milestone whose exports to verify.

        Returns
        -------
        list[str]
            Human-readable descriptions of each missing export.
        """
        milestone_ids = self._list_milestone_ids()
        if not milestone_ids or milestone_id not in milestone_ids:
            return []

        # Collect files owned by this milestone
        owned_files = self._collect_milestone_files(milestone_id)
        if not owned_files:
            return []

        issues: list[str] = []

        # Scan all other milestones for references to owned files
        for other_id in milestone_ids:
            if other_id == milestone_id:
                continue

            content = self._read_requirements(other_id)
            if content is None:
                continue

            # Check import references that point to files owned by this milestone
            for symbol, file_path in self._extract_import_references(content):
                if file_path in owned_files:
                    full_path = self.project_root / file_path
                    if not full_path.is_file():
                        issues.append(
                            f"Milestone '{other_id}' expects '{file_path}' "
                            f"(symbol '{symbol}') from milestone '{milestone_id}', "
                            f"but the file does not exist."
                        )
                    elif symbol != "(file)":
                        # File exists; do a basic symbol presence check
                        try:
                            file_content = full_path.read_text(
                                encoding="utf-8", errors="replace"
                            )
                        except OSError:
                            issues.append(
                                f"Milestone '{other_id}' expects symbol '{symbol}' "
                                f"in '{file_path}' from milestone '{milestone_id}', "
                                f"but the file could not be read."
                            )
                            continue

                        # Simple presence check: symbol name appears in file
                        if not re.search(rf'\b{re.escape(symbol)}\b', file_content):
                            issues.append(
                                f"Milestone '{other_id}' expects symbol '{symbol}' "
                                f"in '{file_path}' from milestone '{milestone_id}', "
                                f"but the symbol was not found in the file."
                            )

            # Check bare file references to owned files
            for file_path in self._extract_file_references(content):
                if file_path in owned_files:
                    full_path = self.project_root / file_path
                    if not full_path.is_file():
                        # Avoid duplicates from import references
                        desc_prefix = (
                            f"Milestone '{other_id}' references '{file_path}' "
                            f"from milestone '{milestone_id}', "
                            f"but the file does not exist."
                        )
                        if desc_prefix not in issues:
                            issues.append(desc_prefix)

        return issues
