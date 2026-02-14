"""Milestone management for PRD-mode orchestration.

Provides MASTER_PLAN.md parsing, context building, rollup health
computation, and per-milestone health checking / cross-milestone wiring
analysis.

The per-milestone orchestration loop in ``cli._run_prd_milestones()``
uses these utilities to decompose PRDs into milestones and execute
each milestone in a fresh orchestrator session with scoped context.
Only activated when MASTER_PLAN.md exists **and**
``config.milestone.enabled`` is True.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .state import ConvergenceReport


# ---------------------------------------------------------------------------
# MASTER_PLAN.md dataclasses
# ---------------------------------------------------------------------------


@dataclass
class MasterPlanMilestone:
    """A single milestone entry parsed from MASTER_PLAN.md."""

    id: str  # e.g. "milestone-1"
    title: str
    status: str = "PENDING"  # PENDING | IN_PROGRESS | COMPLETE | FAILED
    dependencies: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class MasterPlan:
    """The full milestone plan parsed from MASTER_PLAN.md."""

    title: str = ""
    generated: str = ""
    milestones: list[MasterPlanMilestone] = field(default_factory=list)

    def all_complete(self) -> bool:
        """Return True when every milestone is COMPLETE."""
        return bool(self.milestones) and all(
            m.status == "COMPLETE" for m in self.milestones
        )

    def get_ready_milestones(self) -> list[MasterPlanMilestone]:
        """Return milestones whose dependencies are all COMPLETE and that are PENDING."""
        completed_ids = {m.id for m in self.milestones if m.status == "COMPLETE"}
        return [
            m
            for m in self.milestones
            if m.status == "PENDING"
            and all(dep in completed_ids for dep in m.dependencies)
        ]

    def get_milestone(self, milestone_id: str) -> MasterPlanMilestone | None:
        """Look up a milestone by ID."""
        for m in self.milestones:
            if m.id == milestone_id:
                return m
        return None


@dataclass
class MilestoneContext:
    """Scoped context fed to the orchestrator for a single milestone."""

    milestone_id: str
    title: str
    requirements_path: str  # path to this milestone's REQUIREMENTS.md
    predecessor_summaries: list[MilestoneCompletionSummary] = field(
        default_factory=list
    )


@dataclass
class MilestoneCompletionSummary:
    """Compressed summary of a completed milestone (~100-200 tokens)."""

    milestone_id: str
    title: str
    exported_files: list[str] = field(default_factory=list)
    exported_symbols: list[str] = field(default_factory=list)
    summary_line: str = ""


# ---------------------------------------------------------------------------
# MASTER_PLAN.md parsing regexes
# ---------------------------------------------------------------------------

_RE_MILESTONE_HEADER = re.compile(
    r"^#{2,4}\s+(?:Milestone\s+)?(\d+)[.:]?\s*(.*)", re.MULTILINE
)
_RE_FIELD = re.compile(r"^-\s*(\w[\w\s]*):\s*(.+)", re.MULTILINE)
_RE_PLAN_TITLE = re.compile(r"^#\s+(?:MASTER\s+PLAN:\s*)?(.+)", re.MULTILINE)
_RE_GENERATED = re.compile(r"Generated:\s*(.+)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# MASTER_PLAN.md parsing
# ---------------------------------------------------------------------------


def parse_master_plan(content: str) -> MasterPlan:
    """Parse a MASTER_PLAN.md string into a :class:`MasterPlan`.

    The parser is fault-tolerant: handles ``## Milestone N:``,
    ``## N.``, status case variations, and missing fields.
    """
    plan = MasterPlan()

    title_m = _RE_PLAN_TITLE.search(content)
    if title_m:
        plan.title = title_m.group(1).strip()

    gen_m = _RE_GENERATED.search(content)
    if gen_m:
        plan.generated = gen_m.group(1).strip()

    # Split at milestone headers
    splits = list(_RE_MILESTONE_HEADER.finditer(content))
    for idx, match in enumerate(splits):
        num = match.group(1)
        title = match.group(2).strip()

        # Determine the block (text until the next milestone header)
        start = match.end()
        end = splits[idx + 1].start() if idx + 1 < len(splits) else len(content)
        block = content[start:end]

        # Extract structured fields from the block
        fields: dict[str, str] = {}
        for fm in _RE_FIELD.finditer(block):
            key = fm.group(1).strip().lower()
            fields[key] = fm.group(2).strip()

        milestone_id = fields.get("id", f"milestone-{num}")
        status = fields.get("status", "PENDING").upper()
        deps_raw = fields.get("dependencies", "")
        deps = _parse_deps(deps_raw)
        description = fields.get("description", "")

        plan.milestones.append(
            MasterPlanMilestone(
                id=milestone_id,
                title=title,
                status=status,
                dependencies=deps,
                description=description,
            )
        )

    return plan


def _parse_deps(raw: str) -> list[str]:
    """Parse a dependency string like ``milestone-1, milestone-2`` or ``none``.

    Strips parenthetical comments before splitting so that e.g.
    ``milestone-2 (server-side setup can parallel with milestone-3, milestone-4)``
    is correctly parsed as ``["milestone-2"]`` rather than choking on the commas
    inside the parentheses.
    """
    if not raw or raw.strip().lower() in ("none", "n/a", "-", ""):
        return []
    # Strip parenthetical comments: "(anything)" → ""
    import re
    cleaned = re.sub(r"\([^)]*\)", "", raw)
    return [tok.strip() for tok in cleaned.split(",") if tok.strip()]


# ---------------------------------------------------------------------------
# MASTER_PLAN.md status updates
# ---------------------------------------------------------------------------


def update_master_plan_status(
    content: str,
    milestone_id: str,
    new_status: str,
) -> str:
    """Update the status of *milestone_id* in the MASTER_PLAN.md content string.

    Returns the updated content.  If the milestone ID is not found the
    content is returned unchanged.
    """
    # Find "- ID: <milestone_id>" then update the nearest Status field
    id_pattern = re.compile(
        rf"-\s*ID:\s*{re.escape(milestone_id)}", re.IGNORECASE
    )
    id_match = id_pattern.search(content)
    if not id_match:
        return content

    # Search for milestone header boundaries using the milestone regex
    # (not raw "## " prefixes) to avoid non-milestone h3/h4 subsections
    _all_headers = list(_RE_MILESTONE_HEADER.finditer(content))

    block_start = 0
    block_end = len(content)
    for i, hdr_match in enumerate(_all_headers):
        if hdr_match.start() <= id_match.start():
            block_start = hdr_match.start()
        elif hdr_match.start() > id_match.start():
            block_end = hdr_match.start()
            break

    block = content[block_start:block_end]
    status_re = re.compile(r"(-\s*Status:\s*)(\w+)", re.IGNORECASE)
    new_block = status_re.sub(rf"\g<1>{new_status}", block, count=1)

    return content[:block_start] + new_block + content[block_end:]


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------


def build_milestone_context(
    milestone: MasterPlanMilestone,
    milestones_dir: str | Path,
    predecessor_summaries: list[MilestoneCompletionSummary] | None = None,
) -> MilestoneContext:
    """Build scoped context for a single milestone execution."""
    mdir = Path(milestones_dir) / milestone.id
    return MilestoneContext(
        milestone_id=milestone.id,
        title=milestone.title,
        requirements_path=str(mdir / "REQUIREMENTS.md"),
        predecessor_summaries=predecessor_summaries or [],
    )


def build_completion_summary(
    milestone: MasterPlanMilestone,
    exported_files: list[str] | None = None,
    exported_symbols: list[str] | None = None,
    summary_line: str = "",
) -> MilestoneCompletionSummary:
    """Create a compressed completion summary for a finished milestone."""
    return MilestoneCompletionSummary(
        milestone_id=milestone.id,
        title=milestone.title,
        exported_files=exported_files or [],
        exported_symbols=exported_symbols or [],
        summary_line=summary_line,
    )


_CACHE_FILE = "COMPLETION_CACHE.json"


def save_completion_cache(
    milestones_dir: str,
    milestone_id: str,
    summary: MilestoneCompletionSummary,
) -> None:
    """Persist a completion summary as JSON for fast re-reads."""
    cache_path = Path(milestones_dir) / milestone_id / _CACHE_FILE
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(asdict(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_completion_cache(
    milestones_dir: str,
    milestone_id: str,
) -> MilestoneCompletionSummary | None:
    """Load a cached completion summary.  Returns ``None`` if not cached."""
    cache_path = Path(milestones_dir) / milestone_id / _CACHE_FILE
    if not cache_path.is_file():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return MilestoneCompletionSummary(**data)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def render_predecessor_context(
    summaries: list[MilestoneCompletionSummary],
) -> str:
    """Render predecessor summaries into a compact context string.

    Each summary is ~100-200 tokens.  Even with 20 completed milestones
    this adds only ~2000-4000 tokens to the orchestrator prompt.
    """
    if not summaries:
        return ""
    lines = ["## Completed Milestones Context\n"]
    for s in summaries:
        lines.append(f"### {s.milestone_id}: {s.title}")
        if s.summary_line:
            lines.append(f"  Summary: {s.summary_line}")
        if s.exported_files:
            lines.append(f"  Files: {', '.join(s.exported_files[:20])}")
        if s.exported_symbols:
            lines.append(f"  Exports: {', '.join(s.exported_symbols[:20])}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rollup health computation
# ---------------------------------------------------------------------------


def compute_rollup_health(
    plan: MasterPlan,
) -> dict[str, Any]:
    """Compute overall health metrics for the milestone plan.

    Returns a dict with counts and a health status string:
    ``"healthy"`` -- all milestones COMPLETE or PENDING with no failures
    ``"degraded"`` -- at least one milestone FAILED but others progressing
    ``"failed"`` -- majority of milestones FAILED
    """
    total = len(plan.milestones)
    if total == 0:
        return {"total": 0, "health": "unknown"}

    counts: dict[str, int] = {
        "PENDING": 0, "IN_PROGRESS": 0, "COMPLETE": 0, "FAILED": 0,
    }
    for m in plan.milestones:
        key = m.status.upper()
        counts[key] = counts.get(key, 0) + 1

    failed = counts.get("FAILED", 0)
    if failed == 0:
        health = "healthy"
    elif failed < total / 2:
        health = "degraded"
    else:
        health = "failed"

    return {
        "total": total,
        "complete": counts.get("COMPLETE", 0),
        "in_progress": counts.get("IN_PROGRESS", 0),
        "pending": counts.get("PENDING", 0),
        "failed": failed,
        "health": health,
    }


def aggregate_milestone_convergence(
    mm: "MilestoneManager",
    min_convergence_ratio: float = 0.9,
    degraded_threshold: float = 0.5,
) -> ConvergenceReport:
    """Aggregate convergence reports from all milestones into a single report.

    Iterates all milestone directories, calls ``check_milestone_health()``
    per milestone, and combines the results into a global
    :class:`ConvergenceReport`.

    Parameters
    ----------
    mm : MilestoneManager
        Manager instance pointing at the project root.
    min_convergence_ratio : float
        Ratio at or above which health is ``"healthy"``.
    degraded_threshold : float
        Ratio at or above which health is ``"degraded"`` when the review
        fleet has been deployed.

    Returns
    -------
    ConvergenceReport
        Aggregated health report across all milestones.
    """
    milestone_ids = mm._list_milestone_ids()
    if not milestone_ids:
        return ConvergenceReport(health="unknown")

    total_checked = 0
    total_requirements = 0
    max_cycles = 0
    all_escalated: list[str] = []
    # M3: Track zero-cycle milestones (Issue #10)
    zero_cycle_milestones: list[str] = []

    for mid in milestone_ids:
        report = mm.check_milestone_health(
            mid,
            min_convergence_ratio=min_convergence_ratio,
            degraded_threshold=degraded_threshold,
        )
        total_checked += report.checked_requirements
        total_requirements += report.total_requirements
        max_cycles = max(max_cycles, report.review_cycles)
        all_escalated.extend(report.escalated_items)
        # M3: Track milestones with requirements but 0 review cycles
        if report.review_cycles == 0 and report.total_requirements > 0:
            zero_cycle_milestones.append(mid)

    ratio = total_checked / total_requirements if total_requirements > 0 else 0.0
    fleet_deployed = max_cycles > 0

    if total_requirements == 0:
        health = "unknown"
    elif ratio >= min_convergence_ratio:
        health = "healthy"
    elif fleet_deployed and ratio >= degraded_threshold:
        health = "degraded"
    else:
        health = "failed"

    return ConvergenceReport(
        total_requirements=total_requirements,
        checked_requirements=total_checked,
        review_cycles=max_cycles,
        convergence_ratio=ratio,
        review_fleet_deployed=fleet_deployed,
        health=health,
        escalated_items=all_escalated,
        zero_cycle_milestones=zero_cycle_milestones,
    )


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
    r'import\s*\{?\s*(\w+)\s*\}?\s*from\s*["\']([^"\']+)["\']'  # TS/JS style (groups 1-2)
    r'|from\s+([\w./]+)\s+import\s+(\w+)'                        # Python style (groups 3-4)
    r'|imports?\s+(\w+)\s+from\s+([\w./]+)'                       # prose style (groups 5-6)
    r'|require\(\s*["\']'                                          # CommonJS require (groups 7-8)
      r'((?:src|lib|app|server|client|packages|modules)/[\w/.-]+)'
      r'["\']\s*\)(?:\.(\w+))?'
    r'|import\(\s*["\']'                                           # Dynamic import() (groups 9-10)
      r'((?:src|lib|app|server|client|packages|modules)/[\w/.-]+)'
      r'["\']\s*\)(?:\.then\(\s*\w+\s*=>\s*\w+\.(\w+))?'
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


def normalize_milestone_dirs(
    project_root: Path,
    requirements_dir: str = ".agent-team",
) -> int:
    """Normalize milestone directory structure.

    The orchestrator may create ``milestone-N/`` directories directly under
    the requirements directory instead of under the ``milestones/`` sub-directory.
    This function detects such "orphan" directories and copies their contents
    into the canonical ``milestones/milestone-N/`` location.

    Parameters
    ----------
    project_root:
        Root directory of the project.
    requirements_dir:
        Name of the requirements directory (default ``.agent-team``).

    Returns
    -------
    int
        Number of directories normalized (copied to canonical location).
    """
    req_dir = project_root / requirements_dir
    if not req_dir.is_dir():
        return 0

    milestones_dir = req_dir / "milestones"
    normalized = 0

    _milestone_pattern = re.compile(r"^milestone-\w+$")

    try:
        entries = list(req_dir.iterdir())
    except OSError:
        return 0

    for entry in entries:
        if not entry.is_dir():
            continue
        if not _milestone_pattern.match(entry.name):
            continue
        # Skip the "milestones" directory itself
        if entry.name == "milestones":
            continue

        target = milestones_dir / entry.name
        if not target.exists():
            milestones_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copytree(str(entry), str(target))
                normalized += 1
            except (OSError, shutil.Error):
                pass  # Best-effort copy
        else:
            # Merge: copy files that don't already exist in target
            try:
                for src_file in entry.rglob("*"):
                    if src_file.is_file():
                        rel = src_file.relative_to(entry)
                        dest_file = target / rel
                        if not dest_file.exists():
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(src_file), str(dest_file))
                            normalized += 1
            except (OSError, shutil.Error):
                pass  # Best-effort merge

    return normalized


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
            g = match.groups()
            # TS/JS style: group(1)=symbol, group(2)=path
            if g[0] and g[1]:
                refs.append((g[0], g[1]))
            # Python style: group(3)=module_path, group(4)=symbol
            elif g[2] and g[3]:
                refs.append((g[3], g[2]))
            # Prose style: group(5)=symbol, group(6)=path
            elif g[4] and g[5]:
                refs.append((g[4], g[5]))
            # CommonJS require: group(7)=path, group(8)=symbol (optional)
            elif g[6]:
                symbol = g[7] if g[7] else ""
                refs.append((symbol, g[6]))
            # Dynamic import(): group(9)=path, group(10)=symbol (optional)
            elif g[8]:
                symbol = g[9] if g[9] else ""
                refs.append((symbol, g[8]))
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

    def check_milestone_health(
        self,
        milestone_id: str,
        min_convergence_ratio: float = 0.9,
        degraded_threshold: float = 0.5,
    ) -> ConvergenceReport:
        """Check the convergence health of a single milestone.

        Reads ``milestones/{milestone_id}/REQUIREMENTS.md``, counts
        checked vs unchecked items, and parses ``review_cycles`` markers.

        Parameters
        ----------
        milestone_id : str
            The milestone directory name (e.g. ``"milestone-1"``).
        min_convergence_ratio : float
            Ratio at or above which health is considered ``"healthy"``.
            Defaults to ``0.9`` for backward compatibility; callers with
            access to :class:`ConvergenceConfig` should pass
            ``config.convergence.min_convergence_ratio``.
        degraded_threshold : float
            Ratio at or above which health is ``"degraded"`` (vs ``"failed"``),
            when the review fleet has been deployed.  Defaults to ``0.5``.

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

        # Determine health status using configurable thresholds
        if total == 0:
            health = "unknown"
        elif ratio >= min_convergence_ratio:
            health = "healthy"
        elif cycles > 0 and ratio >= degraded_threshold:
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
