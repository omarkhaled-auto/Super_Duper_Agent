"""Per-phase tracking documents for agent-team.

Provides generation, parsing, and template logic for three tracking documents:

1. **E2E_COVERAGE_MATRIX.md** — Maps requirements to E2E tests for completeness
2. **FIX_CYCLE_LOG.md** — Tracks fix attempts across all fix loops
3. **MILESTONE_HANDOFF.md** — Documents interfaces between milestones in PRD+ mode

Each document follows the pattern: start unchecked -> agents mark as they work ->
next agent reads before starting -> can't declare "done" with unchecked items.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .e2e_testing import AppTypeInfo


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class E2ECoverageStats:
    """Statistics parsed from an E2E_COVERAGE_MATRIX.md document."""

    total_items: int = 0
    tests_written: int = 0
    tests_passed: int = 0
    coverage_ratio: float = 0.0
    pass_ratio: float = 0.0


@dataclass
class FixCycleStats:
    """Statistics parsed from a FIX_CYCLE_LOG.md document."""

    total_cycles: int = 0
    cycles_by_phase: dict[str, int] = field(default_factory=dict)
    last_phase_resolved: bool = False


@dataclass
class MilestoneHandoffEntry:
    """A single milestone's entry parsed from MILESTONE_HANDOFF.md."""

    milestone_id: str = ""
    milestone_title: str = ""
    status: str = ""
    interfaces: list[dict] = field(default_factory=list)
    wiring_complete: int = 0
    wiring_total: int = 0


# ---------------------------------------------------------------------------
# Constants — Templates and prompt snippets
# ---------------------------------------------------------------------------

E2E_COVERAGE_MATRIX_TEMPLATE = """\
# E2E Coverage Matrix

> Auto-generated from REQUIREMENTS.md. Agents update checkboxes as tests are written and executed.

{framework_header}

## Backend API Coverage

| Req ID | Endpoint | Method | Roles | Test File | Test Written | Test Passed |
|--------|----------|--------|-------|-----------|:------------:|:-----------:|
{api_rows}

## Frontend Route Coverage

| Route | Component | Key Workflows | Test File | Tested | Passed |
|-------|-----------|---------------|-----------|:------:|:------:|
{route_rows}

## Cross-Role Workflows

| Workflow | Steps | Roles Involved | Tested | Passed |
|----------|-------|----------------|:------:|:------:|
{workflow_rows}

## Coverage: {written}/{total} written ({written_pct}%) | {passed}/{written_for_pass} passing ({pass_pct}%)
"""

FIX_CYCLE_LOG_INSTRUCTIONS = """\
[FIX CYCLE MEMORY — MANDATORY]

Before attempting ANY fix:
1. Read {requirements_dir}/FIX_CYCLE_LOG.md (if it exists)
2. Study ALL previous cycles for this phase — understand what was tried and why it failed
3. DO NOT repeat a previously attempted strategy that didn't work
4. If 3+ cycles have been attempted with no progress, consider a fundamentally different approach

After completing your fix:
5. Append to FIX_CYCLE_LOG.md with:
   - Root cause identified
   - Files modified (with line numbers)
   - Strategy used (how this differs from previous attempts)
   - Result (which failures fixed, which remain)
"""

MILESTONE_HANDOFF_INSTRUCTIONS = """\
[MILESTONE HANDOFF — MANDATORY]

BEFORE writing ANY code in this milestone:
1. Read {requirements_dir}/MILESTONE_HANDOFF.md
2. Study the "Exposed Interfaces" and "Enum/Status Values" tables from ALL predecessor milestones
3. Use EXACT endpoint paths, methods, request bodies, response shapes, AND status/enum values from the handoff
4. Do NOT guess API contracts — they are documented in the handoff

BEFORE completing this milestone:
5. Update MILESTONE_HANDOFF.md — add YOUR milestone's section with:
   - Every endpoint you created/modified (with exact path, method, auth, request/response shapes)
   - Database state (tables/columns created)
   - Enum/status values: for EVERY entity with a status/type/enum field, list ALL valid values,
     the DB storage type, and the exact API string representation
   - Environment variables introduced
   - Known limitations for future milestones
6. If this milestone consumes predecessor interfaces, mark ALL consumed endpoints as [x] in your
   consumption checklist. Any unmarked items = unwired services = AUTOMATIC REVIEW FAILURE.

NEVER scaffold with mock data when the handoff document shows the real endpoint exists.
"""

_FIX_CYCLE_LOG_HEADER = """\
# Fix Cycle Log

This document tracks every fix attempt across all fix loops.
Each fix agent MUST read this log before attempting a fix.
DO NOT repeat a previously attempted strategy.

---
"""


# ---------------------------------------------------------------------------
# Requirement extraction helpers (best-effort regex)
# ---------------------------------------------------------------------------

# Matches requirement IDs: REQ-001, SVC-002, WIRE-003, TECH-004
_RE_REQ_ID = re.compile(
    r"\b((?:REQ|SVC|WIRE|TECH)-\d+)\b",
)

# Matches HTTP methods with paths: GET /api/tenders, POST /auth/login
_RE_HTTP_ENDPOINT = re.compile(
    r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s,)]+)",
    re.IGNORECASE,
)

# Matches frontend routes: /dashboard, /login, /tenders/:id
_RE_FRONTEND_ROUTE = re.compile(
    r"(?:route|page|navigate|path|url)\s*[=:]\s*['\"]?(/[a-zA-Z0-9_/:-]+)",
    re.IGNORECASE,
)
# Also catch routes mentioned inline like "the /dashboard page"
_RE_INLINE_ROUTE = re.compile(
    r"(?:the|to|at|on)\s+(/(?:dashboard|login|register|signup|home|settings|profile|"
    r"admin|users?|tenders?|projects?|tasks?|reports?|analytics|portal|search|help|"
    r"about|contact|notifications?|messages?|billing|checkout|cart|orders?)[a-zA-Z0-9_/:-]*)",
    re.IGNORECASE,
)

# Matches role mentions
_RE_ROLE = re.compile(
    r"\b(admin|administrator|user|reviewer|approver|editor|viewer|manager|"
    r"bidder|supplier|vendor|operator|moderator|superadmin|guest)\b",
    re.IGNORECASE,
)

# Matches workflow patterns: multi-step, multi-role, "A creates -> B approves"
_RE_WORKFLOW = re.compile(
    r"(?:"
    r"(?:create|submit|send|initiate|start)\s*(?:→|->|then|and then)\s*(?:review|approve|reject|verify|complete|confirm)"
    r"|multi[- ]?(?:step|role|stage)"
    r"|workflow|flow\s+of|sequence\s+of"
    r"|(?:User|Role)\s+[A-Z]\s+\w+.*(?:User|Role)\s+[A-Z]\s+\w+"
    r")",
    re.IGNORECASE,
)


def _extract_api_requirements(content: str) -> list[dict]:
    """Extract REQ/SVC items that mention endpoints (GET/POST/PUT/DELETE/PATCH + /path)."""
    results: list[dict] = []
    seen_endpoints: set[str] = set()

    # Split by lines and process requirement blocks
    lines = content.split("\n")
    current_req_id = ""
    current_text = ""

    for line in lines:
        # Check for requirement ID
        req_match = _RE_REQ_ID.search(line)
        if req_match:
            # Process previous requirement if it had endpoints
            if current_req_id:
                _extract_endpoints_from_block(current_req_id, current_text, results, seen_endpoints)
            current_req_id = req_match.group(1)
            current_text = line
        elif current_req_id:
            # Continue accumulating text for current requirement
            if line.strip().startswith("-") or line.strip().startswith("*") or line.strip():
                current_text += " " + line
            else:
                # Empty line — process and reset
                _extract_endpoints_from_block(current_req_id, current_text, results, seen_endpoints)
                current_req_id = ""
                current_text = ""

    # Process final requirement
    if current_req_id:
        _extract_endpoints_from_block(current_req_id, current_text, results, seen_endpoints)

    # Also find standalone endpoints not under a requirement ID
    for m in _RE_HTTP_ENDPOINT.finditer(content):
        method = m.group(1).upper()
        path = m.group(2).rstrip(".,;:)")
        key = f"{method} {path}"
        if key not in seen_endpoints:
            seen_endpoints.add(key)
            # Try to find the nearest req ID
            start = max(0, m.start() - 500)
            context = content[start:m.start()]
            req_match = None
            for rm in _RE_REQ_ID.finditer(context):
                req_match = rm  # last match before this endpoint
            req_id = req_match.group(1) if req_match else ""
            roles = _extract_roles_from_text(content[m.start():m.start() + 200])
            results.append({
                "req_id": req_id,
                "endpoint": path,
                "method": method,
                "roles": roles,
                "text": key,
            })

    return results


def _extract_endpoints_from_block(
    req_id: str,
    text: str,
    results: list[dict],
    seen: set[str],
) -> None:
    """Extract HTTP endpoints from a requirement text block."""
    for m in _RE_HTTP_ENDPOINT.finditer(text):
        method = m.group(1).upper()
        path = m.group(2).rstrip(".,;:)")
        key = f"{method} {path}"
        if key not in seen:
            seen.add(key)
            roles = _extract_roles_from_text(text)
            results.append({
                "req_id": req_id,
                "endpoint": path,
                "method": method,
                "roles": roles,
                "text": text.strip()[:120],
            })


def _extract_roles_from_text(text: str) -> str:
    """Extract role names from text, deduplicated and comma-separated."""
    roles = set()
    for m in _RE_ROLE.finditer(text):
        roles.add(m.group(1).lower())
    return ", ".join(sorted(roles)) if roles else ""


def _extract_route_requirements(content: str) -> list[dict]:
    """Extract requirements that mention frontend routes (/path) or page components."""
    results: list[dict] = []
    seen_routes: set[str] = set()

    # Explicit route definitions
    for m in _RE_FRONTEND_ROUTE.finditer(content):
        route = m.group(1).rstrip(".,;:)")
        if route not in seen_routes:
            seen_routes.add(route)
            # Find surrounding context for component and workflows
            start = max(0, m.start() - 200)
            end = min(len(content), m.end() + 200)
            context = content[start:end]
            results.append({
                "route": route,
                "component": _guess_component_name(route),
                "workflows": _guess_workflows(context),
            })

    # Inline route mentions
    for m in _RE_INLINE_ROUTE.finditer(content):
        route = m.group(1).rstrip(".,;:)")
        if route not in seen_routes:
            seen_routes.add(route)
            start = max(0, m.start() - 200)
            end = min(len(content), m.end() + 200)
            context = content[start:end]
            results.append({
                "route": route,
                "component": _guess_component_name(route),
                "workflows": _guess_workflows(context),
            })

    return results


def _guess_component_name(route: str) -> str:
    """Guess a component name from a route path."""
    # /tenders/:id -> TenderDetails, /dashboard -> Dashboard
    parts = [p for p in route.strip("/").split("/") if p and not p.startswith(":")]
    if not parts:
        return "Page"
    name = parts[-1].replace("-", " ").replace("_", " ").title().replace(" ", "")
    if name.endswith("s") and len(name) > 3:
        return name + "Page"
    return name + "Page"


def _guess_workflows(context: str) -> str:
    """Guess key workflows from surrounding context text."""
    workflows = []
    if re.search(r"\b(?:create|add|new)\b", context, re.IGNORECASE):
        workflows.append("Create")
    if re.search(r"\b(?:edit|update|modify)\b", context, re.IGNORECASE):
        workflows.append("Edit")
    if re.search(r"\b(?:delete|remove)\b", context, re.IGNORECASE):
        workflows.append("Delete")
    if re.search(r"\b(?:view|list|display|show)\b", context, re.IGNORECASE):
        workflows.append("View")
    if re.search(r"\b(?:search|filter|find)\b", context, re.IGNORECASE):
        workflows.append("Search")
    return ", ".join(workflows) if workflows else "View"


def _extract_workflow_requirements(content: str) -> list[dict]:
    """Extract requirements describing multi-step or multi-role workflows."""
    results: list[dict] = []
    seen: set[str] = set()

    for m in _RE_WORKFLOW.finditer(content):
        # Get surrounding context
        start = max(0, m.start() - 300)
        end = min(len(content), m.end() + 300)
        context = content[start:end]

        # Find the nearest requirement line
        lines = context.split("\n")
        workflow_line = ""
        for line in lines:
            if m.group(0).lower() in line.lower():
                workflow_line = line.strip()[:150]
                break
        if not workflow_line:
            workflow_line = m.group(0).strip()[:150]

        if workflow_line not in seen:
            seen.add(workflow_line)
            roles = _extract_roles_from_text(context)
            # Try to identify steps
            steps = _count_workflow_steps(context)
            results.append({
                "workflow": workflow_line,
                "steps": steps,
                "roles": roles,
            })

    return results


def _count_workflow_steps(text: str) -> str:
    """Count or describe workflow steps from text."""
    # Count arrow-separated steps: A -> B -> C
    arrows = text.count("→") + text.count("->")
    if arrows >= 1:
        return f"{arrows + 1} steps"
    # Count numbered steps
    numbered = re.findall(r"(?:step\s*)?(\d+)[.):]\s", text, re.IGNORECASE)
    if numbered:
        return f"{len(numbered)} steps"
    return "multi-step"


# ---------------------------------------------------------------------------
# Document 1: E2E Coverage Matrix
# ---------------------------------------------------------------------------

def generate_e2e_coverage_matrix(
    requirements_content: str,
    app_info: "AppTypeInfo | None" = None,
    route_files: list[str] | None = None,
) -> str:
    """Generate E2E_COVERAGE_MATRIX.md from REQUIREMENTS.md content.

    Extracts API endpoints, frontend routes, and cross-role workflows from the
    requirements and builds checklist tables. All checkboxes start unchecked.

    Parameters
    ----------
    requirements_content : str
        Raw text of REQUIREMENTS.md.
    app_info : AppTypeInfo | None
        Optional detected app type for framework header.
    route_files : list[str] | None
        Optional list of route file paths for reference.

    Returns
    -------
    str
        Complete markdown content for E2E_COVERAGE_MATRIX.md.
    """
    api_reqs = _extract_api_requirements(requirements_content)
    route_reqs = _extract_route_requirements(requirements_content)
    workflow_reqs = _extract_workflow_requirements(requirements_content)

    # Build framework header
    framework_header = ""
    if app_info:
        parts = []
        if app_info.backend_framework:
            parts.append(f"Backend: {app_info.backend_framework}")
        if app_info.frontend_framework:
            parts.append(f"Frontend: {app_info.frontend_framework}")
        if app_info.language:
            parts.append(f"Language: {app_info.language}")
        if parts:
            framework_header = f"> **Stack:** {' | '.join(parts)}"

    # Build API rows
    if api_reqs:
        api_rows = "\n".join(
            f"| {r['req_id']} | {r['endpoint']} | {r['method']} | {r['roles']} | | [ ] | [ ] |"
            for r in api_reqs
        )
    else:
        api_rows = "| — | No API endpoints detected | — | — | — | — | — |"

    # Build route rows
    if route_reqs:
        route_rows = "\n".join(
            f"| {r['route']} | {r['component']} | {r['workflows']} | | [ ] | [ ] |"
            for r in route_reqs
        )
    else:
        route_rows = "| — | No frontend routes detected | — | — | — | — |"

    # Build workflow rows
    if workflow_reqs:
        workflow_rows = "\n".join(
            f"| {r['workflow']} | {r['steps']} | {r['roles']} | [ ] | [ ] |"
            for r in workflow_reqs
        )
    else:
        workflow_rows = "| — | No cross-role workflows detected | — | — | — |"

    # Count totals (only real items, not placeholders)
    total = 0
    if api_reqs:
        total += len(api_reqs)
    if route_reqs:
        total += len(route_reqs)
    if workflow_reqs:
        total += len(workflow_reqs)

    return E2E_COVERAGE_MATRIX_TEMPLATE.format(
        framework_header=framework_header,
        api_rows=api_rows,
        route_rows=route_rows,
        workflow_rows=workflow_rows,
        written=0,
        total=total,
        written_pct=0,
        passed=0,
        written_for_pass=0,
        pass_pct=0,
    )


def parse_e2e_coverage_matrix(content: str) -> E2ECoverageStats:
    """Parse E2E_COVERAGE_MATRIX.md into coverage statistics.

    Counts checked ``[x]`` checkboxes in "Test Written"/"Tested" and
    "Test Passed"/"Passed" columns across all three tables.

    Parameters
    ----------
    content : str
        Raw text of E2E_COVERAGE_MATRIX.md.

    Returns
    -------
    E2ECoverageStats
        Parsed statistics.
    """
    if not content or not content.strip():
        return E2ECoverageStats()

    stats = E2ECoverageStats()

    # Parse table rows — each row is a pipe-delimited line
    table_lines = [
        line for line in content.split("\n")
        if line.strip().startswith("|") and "---" not in line
        and not line.strip().startswith("| Req ID")
        and not line.strip().startswith("| Route")
        and not line.strip().startswith("| Workflow")
        and not line.strip().startswith("| —")
    ]

    for line in table_lines:
        cells = [c.strip() for c in line.split("|")]
        # Filter empty cells from leading/trailing pipes
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue

        # Check if any cell contains [N/A] — skip counting
        if any("[N/A]" in c or "[n/a]" in c for c in cells):
            continue

        # Count total items (rows with checkboxes)
        has_checkbox = any("[x]" in c.lower() or "[ ]" in c for c in cells)
        if not has_checkbox:
            continue

        stats.total_items += 1

        # Backend API table: 7 columns — Test Written is col 6, Test Passed is col 7
        # Frontend Route table: 6 columns — Tested is col 5, Passed is col 6
        # Workflow table: 5 columns — Tested is col 4, Passed is col 5
        # General: second-to-last checkbox = written, last checkbox = passed

        checkbox_cells = [
            i for i, c in enumerate(cells)
            if "[x]" in c.lower() or "[ ]" in c
        ]

        if len(checkbox_cells) >= 2:
            written_idx = checkbox_cells[0]
            passed_idx = checkbox_cells[1]
            if "[x]" in cells[written_idx].lower():
                stats.tests_written += 1
            if "[x]" in cells[passed_idx].lower():
                stats.tests_passed += 1
        elif len(checkbox_cells) == 1:
            if "[x]" in cells[checkbox_cells[0]].lower():
                stats.tests_written += 1

    # Compute ratios
    if stats.total_items > 0:
        stats.coverage_ratio = stats.tests_written / stats.total_items
    if stats.tests_written > 0:
        stats.pass_ratio = stats.tests_passed / stats.tests_written

    return stats


# ---------------------------------------------------------------------------
# Document 2: Fix Cycle Log
# ---------------------------------------------------------------------------

def initialize_fix_cycle_log(requirements_dir: str) -> Path:
    """Create FIX_CYCLE_LOG.md with header if it doesn't exist. Return path.

    Parameters
    ----------
    requirements_dir : str
        Directory to create/find the log file in.

    Returns
    -------
    Path
        Absolute path to the FIX_CYCLE_LOG.md file.
    """
    dir_path = Path(requirements_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    log_path = dir_path / "FIX_CYCLE_LOG.md"

    if not log_path.is_file():
        log_path.write_text(_FIX_CYCLE_LOG_HEADER, encoding="utf-8")

    return log_path


def build_fix_cycle_entry(
    phase: str,
    cycle_number: int,
    failures: list[str],
    previous_cycles: int = 0,
) -> str:
    """Build a markdown entry for a fix cycle.

    The fix agent is expected to append the "After fixing" section
    with actual results.

    Parameters
    ----------
    phase : str
        Phase name (e.g., "E2E Backend", "Mock Data", "UI Compliance").
    cycle_number : int
        The current cycle number (1-based).
    failures : list[str]
        List of failure descriptions to fix.
    previous_cycles : int
        Number of previous cycles in this phase.

    Returns
    -------
    str
        Markdown entry for this fix cycle.
    """
    failures_text = "\n".join(
        f"   {i}. {f}" for i, f in enumerate(failures, 1)
    ) if failures else "   (none specified)"

    return f"""\
## {phase} — Cycle {cycle_number}

**Failures to fix:**
{failures_text}

**Previous cycles in this phase:** {previous_cycles}

**Instructions for this cycle:**
- Review the failures above
- If previous cycles exist, read them below — DO NOT repeat their strategies
- Diagnose root cause, apply fix, record what you did

**After fixing, append to this section:**
- Root cause identified: {{describe}}
- Files modified: {{list with line numbers}}
- Strategy used: {{describe approach}}
- Result: {{which failures are fixed, which remain}}
"""


def parse_fix_cycle_log(content: str) -> FixCycleStats:
    """Parse FIX_CYCLE_LOG.md into fix cycle statistics.

    Parameters
    ----------
    content : str
        Raw text of FIX_CYCLE_LOG.md.

    Returns
    -------
    FixCycleStats
        Parsed statistics grouped by phase.
    """
    if not content or not content.strip():
        return FixCycleStats()

    stats = FixCycleStats()

    # Match cycle headers: ## Phase Name — Cycle N
    cycle_re = re.compile(r"^##\s+(.+?)\s*—\s*Cycle\s+(\d+)", re.MULTILINE)

    last_phase = ""
    last_resolved = False

    for m in cycle_re.finditer(content):
        phase = m.group(1).strip()
        stats.total_cycles += 1
        stats.cycles_by_phase[phase] = stats.cycles_by_phase.get(phase, 0) + 1
        last_phase = phase

        # Check if this cycle resolved (look for "Result:" section after this match)
        end_pos = m.end()
        next_section = content.find("## ", end_pos + 1)
        if next_section == -1:
            cycle_text = content[end_pos:]
        else:
            cycle_text = content[end_pos:next_section]

        # Check for resolution indicators
        if re.search(r"Result:.*(?:all\s+fixed|0\s+remain|none\s+remain|resolved)", cycle_text, re.IGNORECASE):
            last_resolved = True
        else:
            last_resolved = False

    stats.last_phase_resolved = last_resolved
    return stats


# ---------------------------------------------------------------------------
# Document 3: Milestone Handoff
# ---------------------------------------------------------------------------

def generate_milestone_handoff_entry(
    milestone_id: str,
    milestone_title: str,
    status: str = "COMPLETE",
) -> str:
    """Generate a MILESTONE_HANDOFF.md section for one milestone.

    The milestone agent is expected to fill in the tables with actual
    endpoint details, database state, etc.

    Parameters
    ----------
    milestone_id : str
        Milestone identifier (e.g., "milestone-1").
    milestone_title : str
        Human-readable title.
    status : str
        Status string (default "COMPLETE").

    Returns
    -------
    str
        Markdown section for this milestone.
    """
    return f"""\
## {milestone_id}: {milestone_title} — {status}

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
<!-- Agent: Fill this table with EVERY endpoint this milestone created or modified -->

### Database State After This Milestone
<!-- Agent: List all tables/collections created or modified, with column names and types -->

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
<!-- Agent: For EVERY entity with a status/type/enum field, list ALL valid values -->
<!-- Include the exact string used in DB, the exact string in API responses, and valid state transitions -->

### Environment Variables
<!-- Agent: List all env vars this milestone requires or introduces -->

### Files Created/Modified
<!-- Agent: List key files with brief descriptions -->

### Known Limitations
<!-- Agent: Note anything NOT yet implemented that later milestones should know about -->
"""


def generate_consumption_checklist(
    milestone_id: str,
    milestone_title: str,
    predecessor_interfaces: list[dict],
) -> str:
    """Generate a consumption checklist for a milestone.

    Lists all predecessor interfaces so the milestone agent can mark
    each as wired ``[x]`` or unwired ``[ ]``.

    Parameters
    ----------
    milestone_id : str
        Current milestone identifier.
    milestone_title : str
        Current milestone title.
    predecessor_interfaces : list[dict]
        List of interface dicts with keys: source_milestone, endpoint, method.

    Returns
    -------
    str
        Markdown consumption checklist.
    """
    if not predecessor_interfaces:
        return f"""\
### {milestone_id}: {milestone_title} — Consuming From Predecessors

No predecessor interfaces to consume.

**Wiring: 0/0 complete (N/A)**
"""

    rows = []
    for iface in predecessor_interfaces:
        source = iface.get("source_milestone", "")
        endpoint = iface.get("endpoint", "")
        method = iface.get("method", "")
        service = iface.get("frontend_service", "")
        rows.append(f"| {source} | {endpoint} | {method} | {service} | [ ] |")

    rows_text = "\n".join(rows)
    total = len(predecessor_interfaces)

    return f"""\
### {milestone_id}: {milestone_title} — Consuming From Predecessors
| Source Milestone | Endpoint | Method | Frontend Service | Wired? |
|-----------------|----------|--------|-----------------|:------:|
{rows_text}

**Wiring: 0/{total} complete (0%)**
"""


def parse_milestone_handoff(content: str) -> list[MilestoneHandoffEntry]:
    """Parse MILESTONE_HANDOFF.md into structured entries per milestone.

    Parameters
    ----------
    content : str
        Raw text of MILESTONE_HANDOFF.md.

    Returns
    -------
    list[MilestoneHandoffEntry]
        One entry per milestone section found.
    """
    if not content or not content.strip():
        return []

    entries: list[MilestoneHandoffEntry] = []
    seen_ids: set[str] = set()

    # Match milestone headers: ## milestone-id: Title — STATUS
    header_re = re.compile(
        r"^##\s+([\w-]+):\s+(.+?)\s*—\s*(\w+)",
        re.MULTILINE,
    )

    for m in header_re.finditer(content):
        mid = m.group(1).strip()
        title = m.group(2).strip()
        status = m.group(3).strip()

        # Skip duplicates (resume case)
        if mid in seen_ids:
            continue
        seen_ids.add(mid)

        # Extract section content until next ## header
        start = m.end()
        next_header = content.find("\n## ", start)
        if next_header == -1:
            section = content[start:]
        else:
            section = content[start:next_header]

        # Parse interfaces table
        interfaces = _parse_interfaces_table(section)

        # Compute wiring from consumption checklist (if present)
        wired, total = _count_wiring_in_section(content, mid)

        entries.append(MilestoneHandoffEntry(
            milestone_id=mid,
            milestone_title=title,
            status=status,
            interfaces=interfaces,
            wiring_complete=wired,
            wiring_total=total,
        ))

    return entries


def _parse_interfaces_table(section: str) -> list[dict]:
    """Parse the Exposed Interfaces table from a milestone section."""
    interfaces: list[dict] = []

    # Find lines that look like table rows (pipe-delimited, not header/separator)
    in_interfaces = False
    for line in section.split("\n"):
        stripped = line.strip()
        if "### Exposed Interfaces" in stripped or "Exposed Interfaces" in stripped:
            in_interfaces = True
            continue
        if stripped.startswith("### ") and in_interfaces:
            break  # Next subsection
        if not in_interfaces:
            continue
        if not stripped.startswith("|"):
            continue
        if "---" in stripped:
            continue
        if "Endpoint" in stripped and "Method" in stripped:
            continue  # Header row
        if "Agent:" in stripped or "<!--" in stripped:
            continue

        cells = [c.strip() for c in stripped.split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            interfaces.append({
                "endpoint": cells[0] if len(cells) > 0 else "",
                "method": cells[1] if len(cells) > 1 else "",
                "auth_required": cells[2] if len(cells) > 2 else "",
                "request_body": cells[3] if len(cells) > 3 else "",
                "response_shape": cells[4] if len(cells) > 4 else "",
            })

    return interfaces


def parse_handoff_interfaces(content: str, milestone_id: str) -> list[dict]:
    """Extract the Exposed Interfaces table for a specific milestone.

    Parameters
    ----------
    content : str
        Raw text of MILESTONE_HANDOFF.md.
    milestone_id : str
        The milestone to extract interfaces for.

    Returns
    -------
    list[dict]
        List of interface dicts with keys: source_milestone, endpoint, method.
    """
    if not content or not milestone_id:
        return []

    # Find the milestone section
    header_re = re.compile(
        rf"^##\s+{re.escape(milestone_id)}:\s+.+?—\s*\w+",
        re.MULTILINE,
    )
    match = header_re.search(content)
    if not match:
        return []

    start = match.end()
    next_header = content.find("\n## ", start)
    if next_header == -1:
        section = content[start:]
    else:
        section = content[start:next_header]

    raw_interfaces = _parse_interfaces_table(section)

    # Add source_milestone to each interface
    return [
        {
            "source_milestone": milestone_id,
            "endpoint": iface.get("endpoint", ""),
            "method": iface.get("method", ""),
            "frontend_service": "",
        }
        for iface in raw_interfaces
    ]


def _count_wiring_in_section(content: str, milestone_id: str) -> tuple[int, int]:
    """Count wiring checkboxes in consumption checklist for a milestone."""
    # Find the consumption checklist section for this milestone
    pattern = re.compile(
        rf"###\s+{re.escape(milestone_id)}:.*?Consuming From Predecessors",
        re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return (0, 0)

    start = match.end()
    # Find end of this subsection
    next_section = content.find("\n### ", start)
    next_h2 = content.find("\n## ", start)
    end = len(content)
    if next_section != -1:
        end = min(end, next_section)
    if next_h2 != -1:
        end = min(end, next_h2)

    section = content[start:end]

    wired = len(re.findall(r"\[x\]", section, re.IGNORECASE))
    unwired = len(re.findall(r"\[ \]", section))
    total = wired + unwired

    return (wired, total)


def compute_wiring_completeness(content: str, milestone_id: str) -> tuple[int, int]:
    """Count checked vs total in consumption checklist for a milestone.

    Parameters
    ----------
    content : str
        Raw text of MILESTONE_HANDOFF.md.
    milestone_id : str
        The milestone to check wiring for.

    Returns
    -------
    tuple[int, int]
        (wired_count, total_count).
    """
    return _count_wiring_in_section(content, milestone_id)


# ---------------------------------------------------------------------------
# Handoff Completeness Validation (v13.1 — FINDING-029)
# ---------------------------------------------------------------------------

_HANDOFF_KEY_SECTIONS = ("Exposed Interfaces", "Database State")

_HANDOFF_SKIP_PATTERNS = frozenset({
    "<!--", "|-", "| Endpoint", "| Method", "| Entity", "| Field",
    "### ", "| Source", "Agent:",
})


def _is_content_line(line: str) -> bool:
    """Return True if *line* carries actual data (not a template placeholder)."""
    stripped = line.strip()
    if not stripped:
        return False
    for pat in _HANDOFF_SKIP_PATTERNS:
        if pat in stripped:
            return False
    # Table separator rows (|---|---|)
    if stripped.startswith("|") and set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
        return False
    return True


def validate_handoff_completeness(
    content: str,
    milestone_id: str,
) -> tuple[bool, list[str]]:
    """Check whether a milestone's handoff section has been filled beyond the template.

    Parameters
    ----------
    content : str
        Full text of MILESTONE_HANDOFF.md.
    milestone_id : str
        The milestone to validate.

    Returns
    -------
    tuple[bool, list[str]]
        ``(is_complete, unfilled_section_names)``.
        *is_complete* is True when at least one key section
        (Exposed Interfaces **or** Database State) contains real data.
    """
    if not content or not milestone_id:
        return False, list(_HANDOFF_KEY_SECTIONS)

    # Locate the milestone section
    header_re = re.compile(
        rf"^##\s+{re.escape(milestone_id)}:\s+.+",
        re.MULTILINE,
    )
    match = header_re.search(content)
    if not match:
        return False, list(_HANDOFF_KEY_SECTIONS)

    start = match.end()
    next_h2 = content.find("\n## ", start)
    section = content[start:] if next_h2 == -1 else content[start:next_h2]

    # Split into subsections by ### headers
    subsection_re = re.compile(r"^###\s+(.+)", re.MULTILINE)
    subsections: dict[str, str] = {}
    matches = list(subsection_re.finditer(section))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        sub_start = m.end()
        sub_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        subsections[title] = section[sub_start:sub_end]

    unfilled: list[str] = []
    key_filled = 0
    for key in _HANDOFF_KEY_SECTIONS:
        # Find matching subsection (partial match — "Exposed Interfaces" may have suffix)
        found_text = ""
        for sub_title, sub_body in subsections.items():
            if key in sub_title:
                found_text = sub_body
                break
        content_lines = [ln for ln in found_text.split("\n") if _is_content_line(ln)]
        if content_lines:
            key_filled += 1
        else:
            unfilled.append(key)

    return key_filled > 0, unfilled


def extract_predecessor_handoff_content(
    content: str,
    predecessor_ids: list[str],
    max_chars: int = 8000,
) -> str:
    """Extract Exposed Interfaces and Enum/Status tables for predecessor milestones.

    Returns a compact Markdown string suitable for injection into a milestone
    execution prompt.  Truncates at *max_chars* to stay within token budget.

    Parameters
    ----------
    content : str
        Full text of MILESTONE_HANDOFF.md.
    predecessor_ids : list[str]
        Milestone IDs whose handoff sections to extract.
    max_chars : int
        Maximum total characters for the output.

    Returns
    -------
    str
        Markdown with predecessor interface and enum data, or empty string.
    """
    if not content or not predecessor_ids:
        return ""

    _EXTRACT_SECTIONS = ("Exposed Interfaces", "Enum/Status Values")
    parts: list[str] = []
    total_len = 0

    for mid in predecessor_ids:
        header_re = re.compile(
            rf"^##\s+{re.escape(mid)}:\s+(.+)",
            re.MULTILINE,
        )
        match = header_re.search(content)
        if not match:
            continue

        start = match.end()
        next_h2 = content.find("\n## ", start)
        section = content[start:] if next_h2 == -1 else content[start:next_h2]

        # Extract target subsections
        subsection_re = re.compile(r"^(###\s+.+)", re.MULTILINE)
        sub_matches = list(subsection_re.finditer(section))

        extracted: list[str] = []
        for i, sm in enumerate(sub_matches):
            title_line = sm.group(1).strip()
            if not any(s in title_line for s in _EXTRACT_SECTIONS):
                continue
            sub_start = sm.start()
            sub_end = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(section)
            sub_text = section[sub_start:sub_end].strip()
            # Only include if it has actual data (not just template comments)
            if any(_is_content_line(ln) for ln in sub_text.split("\n") if not ln.strip().startswith("###")):
                extracted.append(sub_text)

        if extracted:
            header_line = match.group(0).strip()
            block = f"**{header_line}**\n\n" + "\n\n".join(extracted)
            if total_len + len(block) > max_chars:
                remaining = max_chars - total_len
                if remaining > 200:  # Only add if meaningful space left
                    parts.append(block[:remaining] + "\n...(truncated)")
                break
            parts.append(block)
            total_len += len(block)

    return "\n\n---\n\n".join(parts)
