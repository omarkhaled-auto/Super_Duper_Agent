"""Audit-Team Review System for Agent Team.

Provides a 6-auditor parallel review architecture that replaces the single
reviewer pattern.  Each auditor specializes in one domain:

1. **Requirements auditor** — checks every REQ-xxx / DESIGN-xxx against code
2. **Technical auditor** — checks TECH-xxx patterns, conventions, quality
3. **Interface auditor** — checks WIRE-xxx, SVC-xxx, INT-xxx contracts
4. **Test auditor** — checks test coverage, runs tests, verifies counts
5. **Library auditor** — checks third-party API usage via Context7
6. **PRD fidelity auditor** — cross-references original PRD against REQUIREMENTS.md files

Findings are scored and triaged, then fix agents are dispatched for
issues CRITICAL through the configured severity gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AuditFinding:
    """A single audit finding from one of the 6 auditors."""

    auditor: str          # "requirements" | "technical" | "interface" | "test" | "library" | "prd_fidelity"
    severity: str         # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
    requirement_id: str   # REQ-001, TECH-002, SVC-003, etc.  May be "" for cross-cutting.
    verdict: str          # "PASS" | "FAIL" | "PARTIAL"
    description: str
    file_path: str        # Relative path to the offending file
    line_number: int      # 0 if not applicable
    evidence: str         # Code snippet or reasoning


@dataclass
class AuditTeamReport:
    """Aggregated report from all auditors after scoring."""

    findings: list[AuditFinding] = field(default_factory=list)
    total_pass: int = 0
    total_fail: int = 0
    total_partial: int = 0
    overall_score: float = 0.0   # 0.0–1.0, pass / (pass + fail + partial)
    health: str = "unknown"      # "passed" | "needs-fixes" | "critical"
    fix_rounds_used: int = 0
    auditors_deployed: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Severity ranking
# ---------------------------------------------------------------------------

_SEVERITY_ORDER: dict[str, int] = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "INFO": 1,
}

VALID_SEVERITIES = frozenset(_SEVERITY_ORDER.keys())
VALID_VERDICTS = frozenset({"PASS", "FAIL", "PARTIAL"})
VALID_AUDITORS = frozenset({
    "requirements", "technical", "interface", "test", "library", "prd_fidelity",
})


def severity_rank(severity: str) -> int:
    """Return numeric rank for a severity string (higher = more severe)."""
    return _SEVERITY_ORDER.get(severity.upper(), 0)


# ---------------------------------------------------------------------------
# Auditor prompt constants
# ---------------------------------------------------------------------------

REQUIREMENTS_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — REQUIREMENTS AUDITOR]

You are the REQUIREMENTS AUDITOR in the audit-team review system.  Your ONLY
job is to verify that every functional requirement (REQ-xxx) and design
requirement (DESIGN-xxx) in REQUIREMENTS.md is fully and correctly implemented
in the codebase.

## Input
Read {requirements_path} and identify ALL REQ-xxx and DESIGN-xxx items.

## Verification Process
For EACH requirement:
1. Read the requirement description carefully
2. Search the codebase for the implementation (use Glob/Grep/Read)
3. Verify the implementation is COMPLETE (not partial, not stubbed)
4. Verify the implementation is CORRECT (matches the requirement exactly)
5. Record a finding: PASS, FAIL, or PARTIAL with evidence

## Output
Write your findings to {output_path} using this EXACT format for each finding:

## FINDING-NNN
- **Requirement**: REQ-001
- **Verdict**: PASS | FAIL | PARTIAL
- **Severity**: CRITICAL | HIGH | MEDIUM | LOW | INFO
- **File**: path/to/file.ts:42
- **Description**: What you found
- **Evidence**: Code snippet or reasoning

## Severity Guidelines
- CRITICAL: Feature completely missing or broken
- HIGH: Feature partially implemented, key functionality missing
- MEDIUM: Feature works but has quality issues or edge cases
- LOW: Minor issues, cosmetic problems
- INFO: Observations, suggestions (not actionable)

Be THOROUGH. Check EVERY requirement. Missing a real issue is worse than a false positive.
"""

TECHNICAL_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — TECHNICAL AUDITOR]

You are the TECHNICAL AUDITOR in the audit-team review system.  Your ONLY
job is to verify that every technical requirement (TECH-xxx) in REQUIREMENTS.md
is correctly implemented, and that the code follows the project's conventions.

## Input
Read {requirements_path} and identify ALL TECH-xxx items.

## Verification Process
For EACH technical requirement:
1. Read the requirement description
2. Search the codebase for compliance
3. Check: correct patterns used, proper typing, error handling, conventions followed
4. Record a finding

Also check for cross-cutting technical quality:
- No hardcoded secrets or credentials
- Proper error handling (no empty catch blocks)
- Type safety (no `any` in TypeScript unless justified)
- Consistent naming conventions
- No deprecated API usage

## Output
Write findings to {output_path} using the FINDING-NNN format (same as requirements auditor).

## Severity Guidelines
- CRITICAL: Security vulnerability, data loss risk
- HIGH: Wrong pattern used, type unsafety affecting data flow
- MEDIUM: Convention violation, missing error handling
- LOW: Style inconsistency, minor pattern deviation
- INFO: Suggestion for improvement
"""

INTERFACE_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — INTERFACE AUDITOR]

You are the INTERFACE AUDITOR in the audit-team review system.  Your ONLY
job is to verify that every wiring requirement (WIRE-xxx), service-to-API
wiring (SVC-xxx), and integration requirement (INT-xxx) is correctly
implemented.

## Input
Read {requirements_path} and identify ALL WIRE-xxx, SVC-xxx, and INT-xxx items.

## Verification Process
For EACH wiring/integration requirement:
1. Read the requirement — it specifies source, target, and mechanism
2. Verify the SOURCE file exists and exports/provides what it should
3. Verify the TARGET file imports/consumes it correctly
4. Verify the MECHANISM works (import resolves, route is registered, component renders, etc.)

For SVC-xxx items specifically:
1. Open the frontend service file
2. Verify EVERY method makes a REAL HTTP call (HttpClient, fetch, axios)
3. REJECT if ANY method contains: of(), delay(), mockData, fakeData, hardcoded arrays
4. Verify URL paths match actual backend endpoints
5. Verify response DTO shapes match

Also perform ORPHAN DETECTION:
- Find new files/exports/components that exist but aren't imported anywhere
- Flag unregistered routes, unmounted components, unused services

## Output
Write findings to {output_path} using the FINDING-NNN format.

## Severity Guidelines
- CRITICAL: Broken wiring (runtime error), mock data in production service
- HIGH: Missing integration, orphaned component, wrong endpoint URL
- MEDIUM: DTO shape mismatch, missing error handling on API call
- LOW: Redundant import, unused export
- INFO: Wiring observation
"""

TEST_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — TEST AUDITOR]

You are the TEST AUDITOR in the audit-team review system.  Your ONLY
job is to verify test coverage, test quality, and that tests actually pass.

## Input
Read {requirements_path} for any TEST-xxx items and minimum test count requirements.

## Verification Process
1. Find all test files in the project (*.test.*, *.spec.*, tests/, __tests__/)
2. Count total tests
3. If a minimum test count is specified, verify it is met
4. Run the test suite if a test command is detectable (npm test, pytest, dotnet test)
5. Check test quality:
   - Tests actually assert something (not just "expect(true).toBe(true)")
   - Tests cover the main functionality described in requirements
   - No skipped/disabled tests without justification
   - Integration tests exist for API endpoints
6. Record findings for each issue

## Output
Write findings to {output_path} using the FINDING-NNN format.

Include a summary section:
## SUMMARY
- Total test files: N
- Total test cases: N
- Test command: <command>
- Test result: PASS/FAIL (N passed, M failed)
- Coverage: <percentage if available>

## Severity Guidelines
- CRITICAL: Tests fail, zero tests for a feature, test suite doesn't run
- HIGH: Major feature untested, test count below minimum
- MEDIUM: Test quality issues (weak assertions, missing edge cases)
- LOW: Minor test improvements needed
- INFO: Test coverage observations
"""

LIBRARY_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — LIBRARY/MCP AUDITOR]

You are the LIBRARY AUDITOR in the audit-team review system.  Your ONLY
job is to verify that all third-party library API usage is correct by
checking against current documentation.

## Input
Read {requirements_path} for any library version requirements or constraints.
Also read the codebase to identify all third-party libraries being used.
Focus on the MAIN libraries (frameworks, ORMs, HTTP clients, auth libraries).

## Verification Process
For each key library:
1. Use mcp__context7__resolve-library-id to find the library in Context7
2. Use mcp__context7__query-docs to look up the specific APIs being used
3. Compare the documentation against actual usage in the code
4. Check for:
   - Deprecated API calls
   - Wrong method signatures (argument order, types)
   - Missing required configuration
   - Using old patterns when newer ones are recommended
   - Version mismatches (package.json version vs API usage)

## Output
Write findings to {output_path} using the FINDING-NNN format.

## Severity Guidelines
- CRITICAL: Using API that doesn't exist in installed version (runtime error)
- HIGH: Deprecated API that will break in next major version
- MEDIUM: Wrong but functional API usage (suboptimal pattern)
- LOW: Could use newer API but current one works
- INFO: Library version observation

IMPORTANT: Only flag issues you can VERIFY against documentation. Do not
guess — if Context7 doesn't have the library, note it and move on.
"""

PRD_FIDELITY_AUDITOR_PROMPT = r"""[PHASE: AUDIT-TEAM — PRD FIDELITY AUDITOR]

You are the PRD FIDELITY AUDITOR in the audit-team review system.  Your ONLY
job is to verify that the ORIGINAL PRD (Product Requirements Document) is
faithfully and completely captured in the milestone REQUIREMENTS.md files.

This is a TRACEABILITY audit: you compare the source-of-truth PRD against the
derived REQUIREMENTS.md specifications to detect requirements that were dropped,
distorted, or invented during decomposition.

## Input

### Original PRD
{prd_text}

### Milestone REQUIREMENTS.md Files
Read ALL REQUIREMENTS.md files found under {requirements_dir}/.
This includes the top-level REQUIREMENTS.md and any milestone-specific files
(e.g., milestones/MS-1/REQUIREMENTS.md, milestones/MS-2/REQUIREMENTS.md, etc.).

## Verification Process

Compare the original PRD against all milestone REQUIREMENTS.md files.
For each REQ-xxx, TECH-xxx, WIRE-xxx, SVC-xxx, TEST-xxx, SEC-xxx in the PRD:

1. Find the corresponding entry in a milestone REQUIREMENTS.md
2. Verify the acceptance criteria match (quantitative values, counts, file names,
   function names, field names, API endpoints, data types, constraints)
3. Classify the result:

### Classification Categories

**DROPPED** — A PRD requirement exists but has NO corresponding entry in any
REQUIREMENTS.md file. The requirement was lost during decomposition.
- Verdict: FAIL
- Search for: section headings, numbered items, bullet points, acceptance
  criteria, user stories, functional requirements, non-functional requirements

**DISTORTED** — A PRD requirement exists in a REQUIREMENTS.md but the acceptance
criteria, quantities, constraints, or behavior description has been changed.
- Verdict: PARTIAL
- Check for: different counts/thresholds, renamed fields/functions, relaxed
  constraints, missing edge cases, changed data types, altered API contracts

**ORPHANED** — A REQUIREMENTS.md item exists but does NOT trace back to any
section or requirement in the original PRD. It was invented during decomposition.
- Verdict: FAIL
- Note: Some ORPHANED items may be legitimate technical implementation details
  (e.g., TECH-xxx for error handling patterns). Use judgment — only flag items
  that represent FUNCTIONAL requirements not grounded in the PRD.

## Output
Write your findings to {output_path} using this EXACT format for each finding:

## FINDING-NNN
- **Requirement**: <the requirement ID from PRD or REQUIREMENTS.md>
- **Verdict**: PASS | FAIL | PARTIAL
- **Severity**: CRITICAL | HIGH | MEDIUM | LOW | INFO
- **File**: <path to the REQUIREMENTS.md file where this was found or expected>
- **Description**: [DROPPED|DISTORTED|ORPHANED] <what happened>
- **Evidence**: PRD says: "<exact PRD text>" | REQUIREMENTS.md says: "<exact text>" (or "NOT FOUND")

## Severity Guidelines
- CRITICAL: Entire PRD section missing from all REQUIREMENTS.md files (multiple requirements DROPPED)
- HIGH: Individual PRD requirement DROPPED — no corresponding entry in any REQUIREMENTS.md
- MEDIUM: PRD requirement DISTORTED — acceptance criteria changed, thresholds altered, fields renamed
- LOW: Minor wording difference that does not change functional meaning
- INFO: ORPHANED item that is a reasonable technical addition, or PRD requirement correctly captured (PASS)

## Important Rules
1. Be EXHAUSTIVE — check EVERY quantitative claim in the PRD (counts, sizes, timeouts,
   field names, function signatures, API endpoints, database columns)
2. For each PRD section, report at least one finding (PASS if correctly captured)
3. Quote the EXACT text from both documents in your evidence
4. Do NOT compare PRD against code — that is the job of other auditors.
   You ONLY compare PRD text against REQUIREMENTS.md text.
5. Functional requirements that appear in the PRD but not in any REQUIREMENTS.md
   are the MOST important findings — these represent silent requirement drops.
"""

# NOTE: AUDIT_SCORER_PROMPT is reserved for future LLM-based scoring/dedup.
# Currently, scoring is done in Python via score_audit_findings().
# This prompt is NOT used in the pipeline but is kept for potential upgrade
# where an LLM handles dedup of ambiguous findings across auditors.
AUDIT_SCORER_PROMPT = r"""[PHASE: AUDIT-TEAM — SCORER]

You are the AUDIT SCORER.  Your job is to read ALL auditor reports and produce
a unified, prioritized report.

## Input
Read all audit report files in {audit_dir}/:
- requirements_audit.md
- technical_audit.md
- interface_audit.md
- test_audit.md
- library_audit.md

## Process
1. Collect ALL findings from all reports
2. Deduplicate: if two auditors found the same issue, keep the higher severity
3. Sort by severity: CRITICAL → HIGH → MEDIUM → LOW → INFO
4. Count: total PASS, total FAIL, total PARTIAL
5. Calculate score: PASS / (PASS + FAIL + PARTIAL)
6. Determine health:
   - "passed": score >= {pass_threshold} and no CRITICAL findings
   - "needs-fixes": has CRITICAL or HIGH findings
   - "critical": score < 0.5 or > 3 CRITICAL findings

## Output
Write the unified report to {output_path} using this format:

# Audit Team Report

## Score: X.XX / 1.00 — [HEALTH]

## Critical Issues (fix immediately)
[list findings]

## High Priority Issues
[list findings]

## Medium Priority Issues
[list findings]

## Low Priority / Info
[list findings]

## Summary
- Total findings: N
- PASS: N | FAIL: N | PARTIAL: N
- Auditors deployed: [list]
- Score: X.XX
- Health: [status]
"""

AUDIT_FIX_PROMPT = r"""[PHASE: AUDIT-TEAM — FIX DISPATCH]

The audit team found issues that need fixing.  Below are the findings
grouped by file scope.  Fix ALL issues in the files assigned to you.

## Findings to Fix

{findings_block}

## Rules
1. Read each finding carefully — understand what is expected vs what exists
2. Fix the EXACT issue described (don't over-engineer)
3. For CRITICAL/HIGH: verify the fix resolves the core issue
4. For MEDIUM: address the quality concern
5. Do NOT modify files outside your assigned scope
6. After fixing, verify your changes don't break anything else

{fix_cycle_log_section}
"""


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------

_RE_FINDING_HEADER = re.compile(
    r"^##\s+FINDING-(\d+)\b.*$", re.MULTILINE,
)
_RE_FIELD = re.compile(
    r"^-\s+\*\*(\w+)\*\*:\s*(.+)$", re.MULTILINE,
)
# Multi-line evidence: everything after `- **Evidence**:` until next field or section
_RE_EVIDENCE_BLOCK = re.compile(
    r"-\s+\*\*Evidence\*\*:\s*(.*?)(?=^-\s+\*\*|\Z|^##)",
    re.MULTILINE | re.DOTALL,
)

# Maximum findings per auditor to prevent token explosion
_MAX_FINDINGS = 100


def parse_audit_findings(
    content: str,
    auditor: str,
) -> list[AuditFinding]:
    """Parse a markdown audit report into AuditFinding objects.

    Expects the FINDING-NNN format with **Field**: value lines.
    Caps at ``_MAX_FINDINGS`` to avoid token explosion with large codebases.
    """
    findings: list[AuditFinding] = []

    # Split content by FINDING-NNN headers
    headers = list(_RE_FINDING_HEADER.finditer(content))
    for i, header_match in enumerate(headers):
        if len(findings) >= _MAX_FINDINGS:
            break

        start = header_match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        section = content[start:end]

        # Parse fields from the section
        fields: dict[str, str] = {}
        for field_match in _RE_FIELD.finditer(section):
            key = field_match.group(1).lower().strip()
            value = field_match.group(2).strip()
            fields[key] = value

        # Extract multi-line evidence (overrides single-line capture)
        evidence_match = _RE_EVIDENCE_BLOCK.search(section)
        if evidence_match:
            evidence_text = evidence_match.group(1).strip()
            if evidence_text:
                fields["evidence"] = evidence_text

        # Extract file:line
        file_path = ""
        line_number = 0
        file_str = fields.get("file", "")
        if ":" in file_str:
            parts = file_str.rsplit(":", 1)
            file_path = parts[0]
            try:
                line_number = int(parts[1])
            except (ValueError, IndexError):
                file_path = file_str
        else:
            file_path = file_str

        severity = fields.get("severity", "INFO").upper()
        if severity not in VALID_SEVERITIES:
            severity = "INFO"

        verdict = fields.get("verdict", "FAIL").upper()
        if verdict not in VALID_VERDICTS:
            verdict = "FAIL"

        findings.append(AuditFinding(
            auditor=auditor,
            severity=severity,
            requirement_id=fields.get("requirement", ""),
            verdict=verdict,
            description=fields.get("description", ""),
            file_path=file_path,
            line_number=line_number,
            evidence=fields.get("evidence", ""),
        ))

    return findings


def parse_all_audit_reports(
    audit_dir: str,
) -> list[AuditFinding]:
    """Parse all auditor report files in the audit directory.

    Returns a combined list of findings from all auditors.
    """
    from pathlib import Path

    all_findings: list[AuditFinding] = []
    dir_path = Path(audit_dir)

    auditor_files = {
        "requirements": "requirements_audit.md",
        "technical": "technical_audit.md",
        "interface": "interface_audit.md",
        "test": "test_audit.md",
        "library": "library_audit.md",
        "prd_fidelity": "prd_fidelity_audit.md",
    }

    for auditor_name, filename in auditor_files.items():
        filepath = dir_path / filename
        if filepath.is_file():
            try:
                content = filepath.read_text(encoding="utf-8")
                findings = parse_audit_findings(content, auditor_name)
                all_findings.extend(findings)
            except (OSError, UnicodeDecodeError):
                pass

    return all_findings


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_audit_findings(
    findings: list[AuditFinding],
    pass_threshold: float = 0.9,
    auditors_deployed: list[str] | None = None,
) -> AuditTeamReport:
    """Score and aggregate audit findings into an AuditTeamReport.

    Deduplicates findings with the same requirement_id + file_path,
    keeping the higher severity.
    """
    # Deduplicate: same requirement_id + file_path → keep highest severity.
    # For cross-cutting findings (empty requirement_id), include a description
    # fragment in the key to avoid collapsing unrelated issues on the same file.
    seen: dict[tuple[str, ...], AuditFinding] = {}
    for f in findings:
        if f.requirement_id:
            key: tuple[str, ...] = (f.requirement_id, f.file_path)
        else:
            key = (f.requirement_id, f.file_path, f.description[:80])
        if key in seen:
            if severity_rank(f.severity) > severity_rank(seen[key].severity):
                seen[key] = f
        else:
            seen[key] = f

    deduped = list(seen.values())

    # Count verdicts
    total_pass = sum(1 for f in deduped if f.verdict == "PASS")
    total_fail = sum(1 for f in deduped if f.verdict == "FAIL")
    total_partial = sum(1 for f in deduped if f.verdict == "PARTIAL")
    total = total_pass + total_fail + total_partial

    # Calculate score
    overall_score = total_pass / total if total > 0 else 1.0

    # Count critical findings
    critical_count = sum(1 for f in deduped if f.severity == "CRITICAL")

    # Determine health
    if total == 0 and auditors_deployed:
        health = "unknown"
    elif overall_score >= pass_threshold and critical_count == 0:
        health = "passed"
    elif critical_count > 3 or overall_score < 0.5:
        health = "critical"
    else:
        health = "needs-fixes"

    # Sort findings by severity (highest first)
    deduped.sort(key=lambda f: severity_rank(f.severity), reverse=True)

    return AuditTeamReport(
        findings=deduped,
        total_pass=total_pass,
        total_fail=total_fail,
        total_partial=total_partial,
        overall_score=overall_score,
        health=health,
        auditors_deployed=auditors_deployed or [],
    )


# ---------------------------------------------------------------------------
# Fix dispatch helpers
# ---------------------------------------------------------------------------

def filter_findings_for_fix(
    findings: list[AuditFinding],
    severity_gate: str = "MEDIUM",
) -> list[AuditFinding]:
    """Filter findings to those that need fixing (>= severity_gate, non-PASS)."""
    gate_rank = severity_rank(severity_gate)
    return [
        f for f in findings
        if f.verdict != "PASS"
        and severity_rank(f.severity) >= gate_rank
    ]


def group_findings_by_file(
    findings: list[AuditFinding],
) -> dict[str, list[AuditFinding]]:
    """Group findings by file path for non-conflicting fix dispatch."""
    groups: dict[str, list[AuditFinding]] = {}
    for f in findings:
        key = f.file_path or "_general"
        if key not in groups:
            groups[key] = []
        groups[key].append(f)
    return groups


def build_audit_fix_prompt(
    findings: list[AuditFinding],
    fix_cycle_log: str = "",
) -> str:
    """Build a fix prompt from a list of findings for a fix agent."""
    lines: list[str] = []
    for f in findings:
        lines.append(f"### [{f.severity}] {f.requirement_id or 'Cross-cutting'}")
        lines.append(f"- **File**: {f.file_path}:{f.line_number}")
        lines.append(f"- **Verdict**: {f.verdict}")
        lines.append(f"- **Description**: {f.description}")
        if f.evidence:
            lines.append(f"- **Evidence**: {f.evidence}")
        lines.append("")

    findings_block = "\n".join(lines)
    fix_cycle_section = ""
    if fix_cycle_log:
        fix_cycle_section = (
            "\n## Previous Fix Attempts\n"
            f"{fix_cycle_log}\n"
            "Do NOT repeat strategies that already failed.\n"
        )

    return AUDIT_FIX_PROMPT.format(
        findings_block=findings_block,
        fix_cycle_log_section=fix_cycle_section,
    )


def get_auditor_prompt(
    auditor_name: str,
    requirements_path: str,
    output_path: str,
    *,
    prd_text: str = "",
    requirements_dir: str = "",
) -> str:
    """Return the prompt for a specific auditor, formatted with paths.

    Parameters
    ----------
    auditor_name : str
        One of the VALID_AUDITORS names.
    requirements_path : str
        Path to the REQUIREMENTS.md file (used by most auditors).
    output_path : str
        Path where the auditor should write its findings.
    prd_text : str
        Original PRD text (only used by ``prd_fidelity`` auditor).
    requirements_dir : str
        Top-level requirements directory (only used by ``prd_fidelity`` auditor).
    """
    if auditor_name == "prd_fidelity":
        return PRD_FIDELITY_AUDITOR_PROMPT.format(
            prd_text=prd_text,
            requirements_dir=requirements_dir,
            output_path=output_path,
        )

    prompts = {
        "requirements": REQUIREMENTS_AUDITOR_PROMPT,
        "technical": TECHNICAL_AUDITOR_PROMPT,
        "interface": INTERFACE_AUDITOR_PROMPT,
        "test": TEST_AUDITOR_PROMPT,
        "library": LIBRARY_AUDITOR_PROMPT,
    }
    template = prompts.get(auditor_name)
    if not template:
        raise ValueError(f"Unknown auditor: {auditor_name}")
    return template.format(
        requirements_path=requirements_path,
        output_path=output_path,
    )


def get_scorer_prompt(
    audit_dir: str,
    output_path: str,
    pass_threshold: float = 0.9,
) -> str:
    """Return the scorer prompt, formatted with paths."""
    return AUDIT_SCORER_PROMPT.format(
        audit_dir=audit_dir,
        output_path=output_path,
        pass_threshold=pass_threshold,
    )


def get_active_auditors(
    config: Any,
    depth: str = "standard",
    *,
    has_prd: bool = False,
) -> list[str]:
    """Return the list of auditor names to deploy based on config and depth.

    Depth gating:
    - quick: [] (disabled)
    - standard: requirements, technical, test
    - thorough/exhaustive: all 5 core auditors + prd_fidelity (if PRD available)

    The ``prd_fidelity`` auditor is only included when ``has_prd`` is True
    (a PRD file path is available) AND the auditor is enabled in config.
    It is gated to thorough/exhaustive depth like the interface and library auditors.
    """
    if not config.audit_team.enabled:
        return []

    if depth == "quick":
        return []

    auditors: list[str] = []
    mapping = {
        "requirements": config.audit_team.requirements_auditor,
        "technical": config.audit_team.technical_auditor,
        "interface": config.audit_team.interface_auditor,
        "test": config.audit_team.test_auditor,
        "library": config.audit_team.library_auditor,
    }

    if depth == "standard":
        # Standard: only requirements, technical, test
        for name in ("requirements", "technical", "test"):
            if mapping.get(name, True):
                auditors.append(name)
    else:
        # Thorough / exhaustive: all enabled auditors
        for name, enabled in mapping.items():
            if enabled:
                auditors.append(name)

        # PRD fidelity auditor: only when PRD is available and auditor is enabled
        if has_prd and config.audit_team.prd_fidelity_auditor:
            auditors.append("prd_fidelity")

    return auditors
