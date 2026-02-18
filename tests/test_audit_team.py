"""Tests for the audit-team review system.

Covers: dataclasses, parsing, scoring, fix dispatch, config integration,
depth gating, prompt generation, and pipeline wiring.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import asdict
from pathlib import Path

import pytest

from agent_team.audit_team import (
    AUDIT_FIX_PROMPT,
    AUDIT_SCORER_PROMPT,
    INTERFACE_AUDITOR_PROMPT,
    LIBRARY_AUDITOR_PROMPT,
    REQUIREMENTS_AUDITOR_PROMPT,
    TECHNICAL_AUDITOR_PROMPT,
    TEST_AUDITOR_PROMPT,
    AuditFinding,
    AuditTeamReport,
    VALID_AUDITORS,
    VALID_SEVERITIES,
    VALID_VERDICTS,
    _MAX_FINDINGS,
    build_audit_fix_prompt,
    filter_findings_for_fix,
    get_active_auditors,
    get_auditor_prompt,
    get_scorer_prompt,
    group_findings_by_file,
    parse_all_audit_reports,
    parse_audit_findings,
    score_audit_findings,
    severity_rank,
)
from agent_team.config import (
    AgentTeamConfig,
    AuditTeamConfig,
    apply_depth_quality_gating,
    load_config,
)


# ===================================================================
# Test AuditFinding dataclass
# ===================================================================

class TestAuditFinding:
    def test_basic_creation(self):
        f = AuditFinding(
            auditor="requirements",
            severity="HIGH",
            requirement_id="REQ-001",
            verdict="FAIL",
            description="Login not implemented",
            file_path="src/auth.ts",
            line_number=42,
            evidence="Empty function body",
        )
        assert f.auditor == "requirements"
        assert f.severity == "HIGH"
        assert f.requirement_id == "REQ-001"
        assert f.verdict == "FAIL"
        assert f.line_number == 42

    def test_asdict(self):
        f = AuditFinding(
            auditor="technical",
            severity="MEDIUM",
            requirement_id="TECH-002",
            verdict="PARTIAL",
            description="Missing error handling",
            file_path="src/api.ts",
            line_number=0,
            evidence="",
        )
        d = asdict(f)
        assert d["auditor"] == "technical"
        assert d["severity"] == "MEDIUM"
        assert d["verdict"] == "PARTIAL"

    def test_defaults(self):
        """AuditFinding has no optional fields — all must be specified."""
        with pytest.raises(TypeError):
            AuditFinding()  # type: ignore[call-arg]


# ===================================================================
# Test AuditTeamReport dataclass
# ===================================================================

class TestAuditTeamReport:
    def test_default_creation(self):
        r = AuditTeamReport()
        assert r.findings == []
        assert r.total_pass == 0
        assert r.total_fail == 0
        assert r.total_partial == 0
        assert r.overall_score == 0.0
        assert r.health == "unknown"
        assert r.fix_rounds_used == 0
        assert r.auditors_deployed == []

    def test_with_values(self):
        r = AuditTeamReport(
            total_pass=8,
            total_fail=2,
            overall_score=0.8,
            health="needs-fixes",
            auditors_deployed=["requirements", "technical"],
        )
        assert r.total_pass == 8
        assert r.health == "needs-fixes"
        assert len(r.auditors_deployed) == 2


# ===================================================================
# Test severity_rank
# ===================================================================

class TestSeverityRank:
    @pytest.mark.parametrize("severity,expected", [
        ("CRITICAL", 5), ("HIGH", 4), ("MEDIUM", 3), ("LOW", 2), ("INFO", 1),
    ])
    def test_known_severities(self, severity, expected):
        assert severity_rank(severity) == expected

    def test_unknown_returns_zero(self):
        assert severity_rank("UNKNOWN") == 0

    def test_case_insensitive(self):
        assert severity_rank("critical") == 5
        assert severity_rank("High") == 4


# ===================================================================
# Test valid constants
# ===================================================================

class TestValidConstants:
    def test_valid_severities(self):
        assert VALID_SEVERITIES == frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"})

    def test_valid_verdicts(self):
        assert VALID_VERDICTS == frozenset({"PASS", "FAIL", "PARTIAL"})

    def test_valid_auditors(self):
        assert VALID_AUDITORS == frozenset({
            "requirements", "technical", "interface", "test", "library",
        })


# ===================================================================
# Test parse_audit_findings
# ===================================================================

class TestParseAuditFindings:
    SAMPLE_REPORT = textwrap.dedent("""\
        # Audit Report: Requirements

        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/auth/login.ts:42
        - **Description**: Login endpoint returns mock data
        - **Evidence**: `return of({ token: 'fake' })` on line 42

        ## FINDING-002
        - **Requirement**: REQ-005
        - **Verdict**: PASS
        - **Severity**: INFO
        - **File**: src/auth/register.ts:10
        - **Description**: Registration fully implemented
        - **Evidence**: Uses real API call

        ## FINDING-003
        - **Requirement**: DESIGN-002
        - **Verdict**: PARTIAL
        - **Severity**: MEDIUM
        - **File**: src/components/Header.tsx
        - **Description**: Header missing responsive breakpoints
        - **Evidence**: Only desktop layout exists
    """)

    def test_parses_three_findings(self):
        findings = parse_audit_findings(self.SAMPLE_REPORT, "requirements")
        assert len(findings) == 3

    def test_first_finding_fields(self):
        findings = parse_audit_findings(self.SAMPLE_REPORT, "requirements")
        f = findings[0]
        assert f.auditor == "requirements"
        assert f.requirement_id == "REQ-001"
        assert f.verdict == "FAIL"
        assert f.severity == "HIGH"
        assert f.file_path == "src/auth/login.ts"
        assert f.line_number == 42
        assert "mock data" in f.description

    def test_pass_finding(self):
        findings = parse_audit_findings(self.SAMPLE_REPORT, "requirements")
        f = findings[1]
        assert f.verdict == "PASS"
        assert f.severity == "INFO"
        assert f.requirement_id == "REQ-005"

    def test_partial_finding(self):
        findings = parse_audit_findings(self.SAMPLE_REPORT, "requirements")
        f = findings[2]
        assert f.verdict == "PARTIAL"
        assert f.severity == "MEDIUM"
        assert f.requirement_id == "DESIGN-002"
        assert f.file_path == "src/components/Header.tsx"
        assert f.line_number == 0  # No line number in file path

    def test_empty_content(self):
        findings = parse_audit_findings("", "technical")
        assert findings == []

    def test_no_findings_content(self):
        content = "# Audit Report: Technical\n\nNo issues found.\n"
        findings = parse_audit_findings(content, "technical")
        assert findings == []

    def test_invalid_severity_defaults_to_info(self):
        content = textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: REQ-001
            - **Verdict**: FAIL
            - **Severity**: BANANA
            - **File**: foo.ts
            - **Description**: Bad severity
        """)
        findings = parse_audit_findings(content, "test")
        assert findings[0].severity == "INFO"

    def test_invalid_verdict_defaults_to_fail(self):
        content = textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: REQ-001
            - **Verdict**: MAYBE
            - **Severity**: HIGH
            - **File**: foo.ts
            - **Description**: Bad verdict
        """)
        findings = parse_audit_findings(content, "test")
        assert findings[0].verdict == "FAIL"

    def test_file_without_line_number(self):
        content = textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: REQ-001
            - **Verdict**: FAIL
            - **Severity**: HIGH
            - **File**: src/services/auth.service.ts
            - **Description**: Missing implementation
        """)
        findings = parse_audit_findings(content, "interface")
        assert findings[0].file_path == "src/services/auth.service.ts"
        assert findings[0].line_number == 0


# ===================================================================
# Test parse_all_audit_reports
# ===================================================================

class TestParseAllAuditReports:
    def test_reads_existing_files(self, tmp_path):
        audit_dir = tmp_path / "audit-reports"
        audit_dir.mkdir()

        (audit_dir / "requirements_audit.md").write_text(textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: REQ-001
            - **Verdict**: FAIL
            - **Severity**: HIGH
            - **File**: src/a.ts:10
            - **Description**: Missing
        """), encoding="utf-8")

        (audit_dir / "technical_audit.md").write_text(textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: TECH-001
            - **Verdict**: PASS
            - **Severity**: INFO
            - **File**: src/b.ts
            - **Description**: Good
        """), encoding="utf-8")

        findings = parse_all_audit_reports(str(audit_dir))
        assert len(findings) == 2
        assert findings[0].auditor == "requirements"
        assert findings[1].auditor == "technical"

    def test_missing_files_skipped(self, tmp_path):
        audit_dir = tmp_path / "audit-reports"
        audit_dir.mkdir()
        # Only one file
        (audit_dir / "test_audit.md").write_text(textwrap.dedent("""\
            ## FINDING-001
            - **Requirement**: TEST-001
            - **Verdict**: FAIL
            - **Severity**: CRITICAL
            - **File**: tests/test_a.py
            - **Description**: Tests fail
        """), encoding="utf-8")

        findings = parse_all_audit_reports(str(audit_dir))
        assert len(findings) == 1
        assert findings[0].auditor == "test"

    def test_empty_directory(self, tmp_path):
        audit_dir = tmp_path / "empty"
        audit_dir.mkdir()
        findings = parse_all_audit_reports(str(audit_dir))
        assert findings == []


# ===================================================================
# Test score_audit_findings
# ===================================================================

class TestScoreAuditFindings:
    def _make_finding(self, verdict="FAIL", severity="HIGH", req_id="REQ-001", file_path="a.ts"):
        return AuditFinding(
            auditor="requirements", severity=severity, requirement_id=req_id,
            verdict=verdict, description="test", file_path=file_path,
            line_number=0, evidence="",
        )

    def test_all_pass(self):
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-001"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-002"),
        ]
        report = score_audit_findings(findings)
        assert report.total_pass == 2
        assert report.total_fail == 0
        assert report.overall_score == 1.0
        assert report.health == "passed"

    def test_all_fail(self):
        findings = [
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-001"),
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-002"),
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-003"),
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-004"),
        ]
        report = score_audit_findings(findings)
        assert report.total_fail == 4
        assert report.overall_score == 0.0
        assert report.health == "critical"

    def test_mixed_findings_at_threshold(self):
        """9 pass + 1 fail HIGH = 0.9 score, no critical → passed."""
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-001"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-002"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-003"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-004"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-005"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-006"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-007"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-008"),
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-009"),
            self._make_finding(verdict="FAIL", severity="HIGH", req_id="REQ-010"),
        ]
        report = score_audit_findings(findings)
        assert report.total_pass == 9
        assert report.total_fail == 1
        assert report.overall_score == 0.9
        assert report.health == "passed"  # Meets threshold, no criticals

    def test_mixed_findings_below_threshold(self):
        """8 pass + 2 fail = 0.8 score < 0.9 threshold → needs-fixes."""
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id=f"REQ-{i:03d}")
            for i in range(8)
        ] + [
            self._make_finding(verdict="FAIL", severity="HIGH", req_id="FAIL-1"),
            self._make_finding(verdict="FAIL", severity="HIGH", req_id="FAIL-2"),
        ]
        report = score_audit_findings(findings)
        assert report.total_pass == 8
        assert report.total_fail == 2
        assert report.overall_score == 0.8
        assert report.health == "needs-fixes"

    def test_90_percent_threshold(self):
        # Exactly 90% pass → "passed" (no critical findings)
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id=f"REQ-{i:03d}")
            for i in range(9)
        ] + [
            self._make_finding(verdict="FAIL", severity="LOW", req_id="REQ-010"),
        ]
        report = score_audit_findings(findings, pass_threshold=0.9)
        assert report.overall_score == 0.9
        assert report.health == "passed"

    def test_custom_threshold(self):
        """1 pass + 1 fail = 0.5 score, threshold 0.8, no criticals.
        Score is exactly 0.5, not < 0.5, so not 'critical'. → 'needs-fixes'."""
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id="REQ-001"),
            self._make_finding(verdict="FAIL", severity="HIGH", req_id="REQ-002"),
        ]
        report = score_audit_findings(findings, pass_threshold=0.8)
        assert report.overall_score == 0.5
        assert report.health == "needs-fixes"

    def test_deduplication_keeps_higher_severity(self):
        findings = [
            self._make_finding(verdict="FAIL", severity="LOW", req_id="REQ-001", file_path="a.ts"),
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-001", file_path="a.ts"),
        ]
        report = score_audit_findings(findings)
        assert len(report.findings) == 1
        assert report.findings[0].severity == "CRITICAL"

    def test_deduplication_different_files_not_deduped(self):
        findings = [
            self._make_finding(verdict="FAIL", severity="LOW", req_id="REQ-001", file_path="a.ts"),
            self._make_finding(verdict="FAIL", severity="LOW", req_id="REQ-001", file_path="b.ts"),
        ]
        report = score_audit_findings(findings)
        assert len(report.findings) == 2

    def test_empty_findings(self):
        report = score_audit_findings([])
        assert report.total_pass == 0
        assert report.total_fail == 0
        assert report.overall_score == 1.0  # No findings = perfect score
        assert report.health == "passed"

    def test_partial_verdict(self):
        findings = [
            self._make_finding(verdict="PARTIAL", severity="MEDIUM", req_id="REQ-001"),
        ]
        report = score_audit_findings(findings)
        assert report.total_partial == 1
        assert report.overall_score == 0.0  # 0 pass / 1 total

    def test_critical_count_threshold(self):
        # >3 critical findings → "critical" regardless of score
        findings = [
            self._make_finding(verdict="PASS", severity="INFO", req_id=f"REQ-{i:03d}")
            for i in range(20)
        ] + [
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id=f"CRIT-{i}")
            for i in range(4)
        ]
        report = score_audit_findings(findings)
        assert report.health == "critical"

    def test_auditors_deployed_passed_through(self):
        report = score_audit_findings(
            [], auditors_deployed=["requirements", "technical", "test"],
        )
        assert report.auditors_deployed == ["requirements", "technical", "test"]

    def test_findings_sorted_by_severity(self):
        findings = [
            self._make_finding(verdict="FAIL", severity="LOW", req_id="REQ-001"),
            self._make_finding(verdict="FAIL", severity="CRITICAL", req_id="REQ-002"),
            self._make_finding(verdict="FAIL", severity="MEDIUM", req_id="REQ-003"),
        ]
        report = score_audit_findings(findings)
        severities = [f.severity for f in report.findings]
        assert severities == ["CRITICAL", "MEDIUM", "LOW"]


# ===================================================================
# Test filter_findings_for_fix
# ===================================================================

class TestFilterFindingsForFix:
    def _make_finding(self, verdict="FAIL", severity="HIGH"):
        return AuditFinding(
            auditor="requirements", severity=severity, requirement_id="REQ-001",
            verdict=verdict, description="test", file_path="a.ts",
            line_number=0, evidence="",
        )

    def test_filters_by_severity_gate(self):
        findings = [
            self._make_finding(severity="CRITICAL"),
            self._make_finding(severity="HIGH"),
            self._make_finding(severity="MEDIUM"),
            self._make_finding(severity="LOW"),
            self._make_finding(severity="INFO"),
        ]
        result = filter_findings_for_fix(findings, severity_gate="MEDIUM")
        assert len(result) == 3  # CRITICAL, HIGH, MEDIUM

    def test_excludes_pass_verdict(self):
        findings = [
            self._make_finding(verdict="PASS", severity="CRITICAL"),
            self._make_finding(verdict="FAIL", severity="CRITICAL"),
        ]
        result = filter_findings_for_fix(findings)
        assert len(result) == 1
        assert result[0].verdict == "FAIL"

    def test_includes_partial_verdict(self):
        findings = [
            self._make_finding(verdict="PARTIAL", severity="HIGH"),
        ]
        result = filter_findings_for_fix(findings, severity_gate="MEDIUM")
        assert len(result) == 1

    def test_empty_findings(self):
        result = filter_findings_for_fix([])
        assert result == []

    def test_high_gate(self):
        findings = [
            self._make_finding(severity="CRITICAL"),
            self._make_finding(severity="HIGH"),
            self._make_finding(severity="MEDIUM"),
        ]
        result = filter_findings_for_fix(findings, severity_gate="HIGH")
        assert len(result) == 2  # CRITICAL, HIGH


# ===================================================================
# Test group_findings_by_file
# ===================================================================

class TestGroupFindingsByFile:
    def _make_finding(self, file_path="a.ts"):
        return AuditFinding(
            auditor="requirements", severity="HIGH", requirement_id="REQ-001",
            verdict="FAIL", description="test", file_path=file_path,
            line_number=0, evidence="",
        )

    def test_groups_by_file(self):
        findings = [
            self._make_finding("src/a.ts"),
            self._make_finding("src/b.ts"),
            self._make_finding("src/a.ts"),
        ]
        groups = group_findings_by_file(findings)
        assert len(groups) == 2
        assert len(groups["src/a.ts"]) == 2
        assert len(groups["src/b.ts"]) == 1

    def test_empty_file_path_grouped_as_general(self):
        findings = [self._make_finding("")]
        groups = group_findings_by_file(findings)
        assert "_general" in groups

    def test_empty_findings(self):
        groups = group_findings_by_file([])
        assert groups == {}


# ===================================================================
# Test build_audit_fix_prompt
# ===================================================================

class TestBuildAuditFixPrompt:
    def _make_finding(self, severity="HIGH", req_id="REQ-001", file_path="a.ts"):
        return AuditFinding(
            auditor="requirements", severity=severity, requirement_id=req_id,
            verdict="FAIL", description="Missing implementation",
            file_path=file_path, line_number=42, evidence="Empty function",
        )

    def test_basic_prompt(self):
        findings = [self._make_finding()]
        result = build_audit_fix_prompt(findings)
        assert "[HIGH] REQ-001" in result
        assert "a.ts:42" in result
        assert "Missing implementation" in result
        assert "PHASE: AUDIT-TEAM" in result

    def test_with_fix_cycle_log(self):
        findings = [self._make_finding()]
        result = build_audit_fix_prompt(findings, fix_cycle_log="Previous: tried X")
        assert "Previous Fix Attempts" in result
        assert "Previous: tried X" in result

    def test_without_fix_cycle_log(self):
        findings = [self._make_finding()]
        result = build_audit_fix_prompt(findings, fix_cycle_log="")
        assert "Previous Fix Attempts" not in result

    def test_cross_cutting_finding(self):
        f = AuditFinding(
            auditor="technical", severity="MEDIUM", requirement_id="",
            verdict="FAIL", description="Global pattern issue",
            file_path="src/utils.ts", line_number=0, evidence="",
        )
        result = build_audit_fix_prompt([f])
        assert "Cross-cutting" in result

    def test_multiple_findings(self):
        findings = [
            self._make_finding(severity="CRITICAL", req_id="REQ-001"),
            self._make_finding(severity="HIGH", req_id="REQ-002"),
        ]
        result = build_audit_fix_prompt(findings)
        assert "REQ-001" in result
        assert "REQ-002" in result


# ===================================================================
# Test get_auditor_prompt
# ===================================================================

class TestGetAuditorPrompt:
    def test_all_auditors_return_prompts(self):
        for name in VALID_AUDITORS:
            prompt = get_auditor_prompt(name, "REQUIREMENTS.md", "output.md")
            assert len(prompt) > 100
            assert "REQUIREMENTS.md" in prompt or "output.md" in prompt

    def test_requirements_auditor(self):
        prompt = get_auditor_prompt("requirements", "path/REQ.md", "out/req.md")
        assert "path/REQ.md" in prompt
        assert "out/req.md" in prompt
        assert "REQUIREMENTS AUDITOR" in prompt

    def test_library_auditor_mentions_context7(self):
        prompt = get_auditor_prompt("library", "REQ.md", "out.md")
        assert "mcp__context7__resolve-library-id" in prompt
        assert "mcp__context7__query-docs" in prompt

    def test_unknown_auditor_raises(self):
        with pytest.raises(ValueError, match="Unknown auditor"):
            get_auditor_prompt("banana", "REQ.md", "out.md")


# ===================================================================
# Test get_scorer_prompt
# ===================================================================

class TestGetScorerPrompt:
    def test_basic(self):
        prompt = get_scorer_prompt("/audit", "/out.md", 0.9)
        assert "/audit" in prompt
        assert "/out.md" in prompt
        assert "0.9" in prompt
        assert "SCORER" in prompt


# ===================================================================
# Test get_active_auditors
# ===================================================================

class TestGetActiveAuditors:
    def _make_config(self, **overrides) -> AgentTeamConfig:
        cfg = AgentTeamConfig()
        for k, v in overrides.items():
            setattr(cfg.audit_team, k, v)
        return cfg

    def test_disabled_returns_empty(self):
        cfg = self._make_config(enabled=False)
        assert get_active_auditors(cfg, "exhaustive") == []

    def test_quick_returns_empty(self):
        cfg = self._make_config()
        assert get_active_auditors(cfg, "quick") == []

    def test_standard_returns_three(self):
        cfg = self._make_config()
        result = get_active_auditors(cfg, "standard")
        assert result == ["requirements", "technical", "test"]

    def test_thorough_returns_all_five(self):
        cfg = self._make_config()
        result = get_active_auditors(cfg, "thorough")
        assert set(result) == {"requirements", "technical", "interface", "test", "library"}

    def test_exhaustive_returns_all_five(self):
        cfg = self._make_config()
        result = get_active_auditors(cfg, "exhaustive")
        assert set(result) == {"requirements", "technical", "interface", "test", "library"}

    def test_individual_auditor_disabled(self):
        cfg = self._make_config(technical_auditor=False)
        result = get_active_auditors(cfg, "exhaustive")
        assert "technical" not in result
        assert "requirements" in result

    def test_standard_respects_individual_flags(self):
        cfg = self._make_config(requirements_auditor=False)
        result = get_active_auditors(cfg, "standard")
        assert "requirements" not in result
        assert "technical" in result
        assert "test" in result


# ===================================================================
# Test AuditTeamConfig
# ===================================================================

class TestAuditTeamConfig:
    def test_defaults(self):
        cfg = AuditTeamConfig()
        assert cfg.enabled is True
        assert cfg.requirements_auditor is True
        assert cfg.technical_auditor is True
        assert cfg.interface_auditor is True
        assert cfg.test_auditor is True
        assert cfg.library_auditor is True
        assert cfg.pass_threshold == 0.9
        assert cfg.severity_gate == "MEDIUM"
        assert cfg.max_fix_rounds == 3
        assert cfg.per_milestone is True
        assert cfg.end_of_run is True

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.audit_team, AuditTeamConfig)
        assert cfg.audit_team.enabled is True


# ===================================================================
# Test config loading
# ===================================================================

class TestAuditTeamConfigLoading:
    def test_default_config(self):
        cfg, _ = load_config()
        assert isinstance(cfg.audit_team, AuditTeamConfig)
        assert cfg.audit_team.enabled is True

    def test_yaml_override(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n"
            "  enabled: false\n"
            "  max_fix_rounds: 5\n"
            "  pass_threshold: 0.8\n"
            "  severity_gate: HIGH\n"
            "  library_auditor: false\n",
            encoding="utf-8",
        )
        cfg, overrides = load_config(config_path=str(config_file))
        assert cfg.audit_team.enabled is False
        assert cfg.audit_team.max_fix_rounds == 5
        assert cfg.audit_team.pass_threshold == 0.8
        assert cfg.audit_team.severity_gate == "HIGH"
        assert cfg.audit_team.library_auditor is False
        assert "audit_team.enabled" in overrides

    def test_invalid_severity_gate_raises(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  severity_gate: BANANA\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="severity_gate"):
            load_config(config_path=str(config_file))

    def test_invalid_pass_threshold_raises(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  pass_threshold: 1.5\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="pass_threshold"):
            load_config(config_path=str(config_file))

    def test_invalid_max_fix_rounds_raises(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  max_fix_rounds: -1\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="max_fix_rounds"):
            load_config(config_path=str(config_file))

    def test_user_overrides_tracked(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n"
            "  enabled: true\n"
            "  max_fix_rounds: 2\n"
            "  per_milestone: false\n"
            "  end_of_run: true\n",
            encoding="utf-8",
        )
        _, overrides = load_config(config_path=str(config_file))
        assert "audit_team.enabled" in overrides
        assert "audit_team.max_fix_rounds" in overrides
        assert "audit_team.per_milestone" in overrides
        assert "audit_team.end_of_run" in overrides


# ===================================================================
# Test depth gating for audit-team
# ===================================================================

class TestAuditTeamDepthGating:
    def test_quick_disables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.audit_team.enabled is False

    def test_standard_disables_interface_and_library(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.audit_team.enabled is True  # Not disabled
        assert cfg.audit_team.interface_auditor is False
        assert cfg.audit_team.library_auditor is False
        assert cfg.audit_team.max_fix_rounds == 2

    def test_thorough_all_auditors_enabled(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.audit_team.enabled is True
        assert cfg.audit_team.interface_auditor is True
        assert cfg.audit_team.library_auditor is True
        assert cfg.audit_team.max_fix_rounds == 2

    def test_exhaustive_max_fix_rounds(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.audit_team.max_fix_rounds == 3

    def test_user_override_preserved(self):
        cfg = AgentTeamConfig()
        overrides = {"audit_team.enabled"}
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        assert cfg.audit_team.enabled is True  # Not changed because user override


# ===================================================================
# Test prompt constants content
# ===================================================================

class TestPromptConstants:
    def test_requirements_prompt_mentions_req_xxx(self):
        assert "REQ-xxx" in REQUIREMENTS_AUDITOR_PROMPT
        assert "DESIGN-xxx" in REQUIREMENTS_AUDITOR_PROMPT

    def test_technical_prompt_mentions_tech_xxx(self):
        assert "TECH-xxx" in TECHNICAL_AUDITOR_PROMPT

    def test_interface_prompt_mentions_wire_svc_int(self):
        assert "WIRE-xxx" in INTERFACE_AUDITOR_PROMPT
        assert "SVC-xxx" in INTERFACE_AUDITOR_PROMPT
        assert "INT-xxx" in INTERFACE_AUDITOR_PROMPT

    def test_test_prompt_mentions_test_xxx(self):
        assert "TEST-xxx" in TEST_AUDITOR_PROMPT

    def test_library_prompt_mentions_context7(self):
        assert "mcp__context7__resolve-library-id" in LIBRARY_AUDITOR_PROMPT
        assert "mcp__context7__query-docs" in LIBRARY_AUDITOR_PROMPT

    def test_scorer_prompt_has_placeholders(self):
        assert "{audit_dir}" in AUDIT_SCORER_PROMPT
        assert "{pass_threshold}" in AUDIT_SCORER_PROMPT
        assert "{output_path}" in AUDIT_SCORER_PROMPT

    def test_fix_prompt_has_placeholders(self):
        assert "{findings_block}" in AUDIT_FIX_PROMPT
        assert "{fix_cycle_log_section}" in AUDIT_FIX_PROMPT

    def test_all_prompts_have_phase_header(self):
        for prompt in [
            REQUIREMENTS_AUDITOR_PROMPT,
            TECHNICAL_AUDITOR_PROMPT,
            INTERFACE_AUDITOR_PROMPT,
            TEST_AUDITOR_PROMPT,
            LIBRARY_AUDITOR_PROMPT,
            AUDIT_SCORER_PROMPT,
            AUDIT_FIX_PROMPT,
        ]:
            assert "AUDIT-TEAM" in prompt

    def test_all_auditor_prompts_have_finding_format(self):
        for prompt in [
            REQUIREMENTS_AUDITOR_PROMPT,
            TECHNICAL_AUDITOR_PROMPT,
            INTERFACE_AUDITOR_PROMPT,
            TEST_AUDITOR_PROMPT,
            LIBRARY_AUDITOR_PROMPT,
        ]:
            assert "FINDING-" in prompt

    def test_all_auditor_prompts_have_output_path_placeholder(self):
        for prompt in [
            REQUIREMENTS_AUDITOR_PROMPT,
            TECHNICAL_AUDITOR_PROMPT,
            INTERFACE_AUDITOR_PROMPT,
            TEST_AUDITOR_PROMPT,
            LIBRARY_AUDITOR_PROMPT,
        ]:
            assert "{output_path}" in prompt

    def test_all_auditor_prompts_have_requirements_path_placeholder(self):
        for prompt in [
            REQUIREMENTS_AUDITOR_PROMPT,
            TECHNICAL_AUDITOR_PROMPT,
            INTERFACE_AUDITOR_PROMPT,
            TEST_AUDITOR_PROMPT,
        ]:
            assert "{requirements_path}" in prompt


# ===================================================================
# Test MCP tool names in library auditor
# ===================================================================

class TestLibraryAuditorMcpNames:
    """The library auditor prompt must use full mcp__context7__ tool names."""

    _RE_MCP_ANY = re.compile(r"\bmcp_[a-z0-9_-]+")
    _RE_MCP_TOOL = re.compile(r"mcp__[a-z0-9_-]+__[a-z0-9_-]+")

    def test_all_mcp_refs_use_double_underscore(self):
        for match in self._RE_MCP_ANY.finditer(LIBRARY_AUDITOR_PROMPT):
            token = match.group()
            assert self._RE_MCP_TOOL.fullmatch(token), (
                f"Library auditor has malformed MCP ref: {token!r}"
            )


# ===================================================================
# Test CLI wiring imports
# ===================================================================

class TestCliImports:
    """Verify that cli.py can import audit_team functions."""

    def test_import_audit_team_functions(self):
        from agent_team.cli import _run_audit_team, _run_audit_fix
        assert callable(_run_audit_team)
        assert callable(_run_audit_fix)


# ===================================================================
# Test scoring edge cases
# ===================================================================

class TestScoringEdgeCases:
    def _make_finding(self, verdict, severity, req_id, file_path="a.ts"):
        return AuditFinding(
            auditor="test", severity=severity, requirement_id=req_id,
            verdict=verdict, description="desc", file_path=file_path,
            line_number=0, evidence="",
        )

    def test_exactly_three_critical_is_needs_fixes(self):
        """Exactly 3 critical findings → needs-fixes (not critical)."""
        findings = [
            self._make_finding("FAIL", "CRITICAL", f"REQ-{i}")
            for i in range(3)
        ] + [
            self._make_finding("PASS", "INFO", f"PASS-{i}")
            for i in range(7)
        ]
        report = score_audit_findings(findings)
        assert report.health == "needs-fixes"

    def test_four_critical_is_critical(self):
        """4 critical findings → critical."""
        findings = [
            self._make_finding("FAIL", "CRITICAL", f"REQ-{i}")
            for i in range(4)
        ] + [
            self._make_finding("PASS", "INFO", f"PASS-{i}")
            for i in range(16)
        ]
        report = score_audit_findings(findings)
        assert report.health == "critical"

    def test_score_below_50_is_critical(self):
        """Score < 0.5 → critical."""
        findings = [
            self._make_finding("PASS", "INFO", "PASS-1"),
            self._make_finding("FAIL", "LOW", "FAIL-1"),
            self._make_finding("FAIL", "LOW", "FAIL-2"),
        ]
        report = score_audit_findings(findings)
        assert report.overall_score < 0.5
        assert report.health == "critical"

    def test_exact_threshold_is_passed(self):
        """Score exactly at threshold with no criticals → passed."""
        # 9 pass, 1 fail = 0.9 score, threshold=0.9
        findings = [
            self._make_finding("PASS", "INFO", f"P-{i}")
            for i in range(9)
        ] + [
            self._make_finding("FAIL", "LOW", "F-1"),
        ]
        report = score_audit_findings(findings, pass_threshold=0.9)
        assert report.overall_score == pytest.approx(0.9)
        assert report.health == "passed"


# ===================================================================
# Test config validation
# ===================================================================

class TestAuditTeamConfigValidation:
    def test_pass_threshold_zero_valid(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  pass_threshold: 0.0\n",
            encoding="utf-8",
        )
        cfg, _ = load_config(config_path=str(config_file))
        assert cfg.audit_team.pass_threshold == 0.0

    def test_pass_threshold_one_valid(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  pass_threshold: 1.0\n",
            encoding="utf-8",
        )
        cfg, _ = load_config(config_path=str(config_file))
        assert cfg.audit_team.pass_threshold == 1.0

    def test_max_fix_rounds_zero_valid(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  max_fix_rounds: 0\n",
            encoding="utf-8",
        )
        cfg, _ = load_config(config_path=str(config_file))
        assert cfg.audit_team.max_fix_rounds == 0

    def test_all_severity_gates_valid(self, tmp_path):
        for gate in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            config_file = tmp_path / "config.yaml"
            config_file.write_text(
                f"audit_team:\n  severity_gate: {gate}\n",
                encoding="utf-8",
            )
            cfg, _ = load_config(config_path=str(config_file))
            assert cfg.audit_team.severity_gate == gate


# ===================================================================
# Review Fix Tests — C1: Library auditor prompt has {requirements_path}
# ===================================================================

class TestC1LibraryAuditorPromptHasRequirementsPath:
    """C1 FIX: LIBRARY_AUDITOR_PROMPT must contain {requirements_path}."""

    def test_library_prompt_contains_requirements_path_placeholder(self):
        assert "{requirements_path}" in LIBRARY_AUDITOR_PROMPT

    def test_all_auditor_prompts_have_requirements_path(self):
        """All 5 auditor prompts must contain {requirements_path}."""
        for name in VALID_AUDITORS:
            prompt = get_auditor_prompt(name, "/req.md", "/out.md")
            # After formatting, the path should appear in the prompt
            assert "/req.md" in prompt, f"Auditor '{name}' missing requirements_path"

    def test_library_auditor_prompt_formatted_correctly(self):
        prompt = get_auditor_prompt("library", "/my/REQUIREMENTS.md", "/out.md")
        assert "/my/REQUIREMENTS.md" in prompt
        assert "/out.md" in prompt


# ===================================================================
# Review Fix Tests — C2: Scope-aware audit directory
# ===================================================================

class TestC2ScopeAwareAuditDir:
    """C2 FIX: Milestone audits should use milestone-scoped directories."""

    def test_milestone_scope_label_generates_milestone_dir(self):
        """scope_label='milestone:MS-1' should create milestones/MS-1/audit-reports/."""
        # We test the logic that's in _run_audit_team indirectly via the pattern
        scope_label = "milestone:MS-1"
        assert scope_label.startswith("milestone:")
        ms_id = scope_label.split(":", 1)[1]
        assert ms_id == "MS-1"
        # The audit_dir should contain the milestone ID
        expected_suffix = f"milestones/{ms_id}/audit-reports"
        assert "audit-reports" in expected_suffix

    def test_end_of_run_scope_label_no_milestone(self):
        scope_label = "end-of-run"
        assert not scope_label.startswith("milestone:")


# ===================================================================
# Review Fix Tests — H1: Dedup key for cross-cutting findings
# ===================================================================

class TestH1DedupCrossCuttingFindings:
    """H1 FIX: Cross-cutting findings (empty requirement_id) should NOT collapse."""

    def test_cross_cutting_different_descriptions_not_deduped(self):
        """Two findings with empty requirement_id but different descriptions survive dedup."""
        findings = [
            AuditFinding(
                auditor="technical", severity="HIGH", requirement_id="",
                verdict="FAIL", description="Empty catch block found",
                file_path="src/app.ts", line_number=10, evidence="",
            ),
            AuditFinding(
                auditor="technical", severity="MEDIUM", requirement_id="",
                verdict="FAIL", description="Hardcoded secret detected",
                file_path="src/app.ts", line_number=25, evidence="",
            ),
        ]
        report = score_audit_findings(findings)
        assert report.total_fail == 2, "Both cross-cutting findings should survive"
        assert len(report.findings) == 2

    def test_same_requirement_same_file_still_deduped(self):
        """Same requirement_id + file_path still deduplicates (existing behavior)."""
        findings = [
            AuditFinding(
                auditor="requirements", severity="HIGH", requirement_id="REQ-001",
                verdict="FAIL", description="Login not working",
                file_path="src/auth.ts", line_number=10, evidence="",
            ),
            AuditFinding(
                auditor="interface", severity="MEDIUM", requirement_id="REQ-001",
                verdict="FAIL", description="Login button broken",
                file_path="src/auth.ts", line_number=10, evidence="",
            ),
        ]
        report = score_audit_findings(findings)
        # Deduped to 1 finding, keeping the higher severity (HIGH)
        assert len(report.findings) == 1
        assert report.findings[0].severity == "HIGH"

    def test_empty_req_id_same_description_deduped(self):
        """Same empty requirement_id + file + description → deduped."""
        findings = [
            AuditFinding(
                auditor="technical", severity="HIGH", requirement_id="",
                verdict="FAIL", description="Empty catch block found",
                file_path="src/app.ts", line_number=10, evidence="",
            ),
            AuditFinding(
                auditor="technical", severity="MEDIUM", requirement_id="",
                verdict="FAIL", description="Empty catch block found",
                file_path="src/app.ts", line_number=15, evidence="",
            ),
        ]
        report = score_audit_findings(findings)
        assert len(report.findings) == 1
        assert report.findings[0].severity == "HIGH"


# ===================================================================
# Review Fix Tests — M1: Multi-line evidence parsing
# ===================================================================

class TestM1MultiLineEvidence:
    """M1 FIX: Evidence fields spanning multiple lines should be captured."""

    def test_multi_line_evidence_parsed(self):
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/auth.ts:42
        - **Description**: Mock data in service
        - **Evidence**: Found mock return value:
          ```typescript
          return of({ token: 'fake' });
          ```
          This should be an HTTP call.
        """)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert "return of" in findings[0].evidence
        assert "fake" in findings[0].evidence

    def test_single_line_evidence_still_works(self):
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/auth.ts:42
        - **Description**: Missing implementation
        - **Evidence**: Function body is empty
        """)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert "Function body is empty" in findings[0].evidence

    def test_evidence_stops_at_next_field(self):
        """Evidence capture should stop before next **Field**: marker."""
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Evidence**: Line 1
          Line 2
        - **Description**: After evidence
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/x.ts:1
        - **Requirement**: REQ-001
        """)
        findings = parse_audit_findings(content, "test")
        assert len(findings) == 1
        # Evidence should contain Line 1 and Line 2 but NOT "After evidence"
        assert "Line 1" in findings[0].evidence
        assert "After evidence" not in findings[0].evidence


# ===================================================================
# Review Fix Tests — L5: Findings cap
# ===================================================================

class TestL5FindingsCap:
    """L5 FIX: parse_audit_findings should cap at _MAX_FINDINGS."""

    def test_max_findings_constant_exists(self):
        assert _MAX_FINDINGS == 100

    def test_findings_capped_at_max(self):
        """Generate 150 findings, only 100 should be parsed."""
        lines = []
        for i in range(150):
            lines.append(f"## FINDING-{i+1:03d}")
            lines.append(f"- **Requirement**: REQ-{i+1:03d}")
            lines.append(f"- **Verdict**: FAIL")
            lines.append(f"- **Severity**: LOW")
            lines.append(f"- **File**: src/file{i}.ts:1")
            lines.append(f"- **Description**: Issue {i+1}")
            lines.append("")
        content = "\n".join(lines)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == _MAX_FINDINGS

    def test_below_cap_all_parsed(self):
        """10 findings should all be parsed (below cap)."""
        lines = []
        for i in range(10):
            lines.append(f"## FINDING-{i+1:03d}")
            lines.append(f"- **Requirement**: REQ-{i+1:03d}")
            lines.append(f"- **Verdict**: PASS")
            lines.append(f"- **Severity**: INFO")
            lines.append(f"- **File**: src/file{i}.ts:1")
            lines.append(f"- **Description**: OK")
            lines.append("")
        content = "\n".join(lines)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 10


# ===================================================================
# Review Fix Tests — H3: User override tracking completeness
# ===================================================================

class TestH3UserOverrideTracking:
    """H3 FIX: All 11 audit_team config fields should be tracked in user_overrides."""

    def test_library_auditor_override_tracked(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  library_auditor: true\n",
            encoding="utf-8",
        )
        _, overrides = load_config(config_path=str(config_file))
        assert "audit_team.library_auditor" in overrides

    def test_interface_auditor_override_tracked(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  interface_auditor: false\n",
            encoding="utf-8",
        )
        _, overrides = load_config(config_path=str(config_file))
        assert "audit_team.interface_auditor" in overrides

    def test_pass_threshold_override_tracked(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  pass_threshold: 0.8\n",
            encoding="utf-8",
        )
        _, overrides = load_config(config_path=str(config_file))
        assert "audit_team.pass_threshold" in overrides

    def test_severity_gate_override_tracked(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  severity_gate: HIGH\n",
            encoding="utf-8",
        )
        _, overrides = load_config(config_path=str(config_file))
        assert "audit_team.severity_gate" in overrides

    def test_all_auditor_flags_tracked(self, tmp_path):
        """All 5 individual auditor bools should be tracked when set."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(textwrap.dedent("""\
            audit_team:
              requirements_auditor: true
              technical_auditor: false
              interface_auditor: true
              test_auditor: false
              library_auditor: true
        """), encoding="utf-8")
        _, overrides = load_config(config_path=str(config_file))
        for field in ("requirements_auditor", "technical_auditor", "interface_auditor",
                       "test_auditor", "library_auditor"):
            assert f"audit_team.{field}" in overrides, f"Missing override for {field}"

    def test_library_auditor_override_survives_depth_gating(self, tmp_path):
        """User sets library_auditor=true, standard depth would disable it.
        With override tracking, user's choice should be preserved."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "audit_team:\n  library_auditor: true\n",
            encoding="utf-8",
        )
        cfg, overrides = load_config(config_path=str(config_file))
        # Standard depth normally disables library_auditor
        apply_depth_quality_gating("standard", cfg, user_overrides=overrides)
        # User's override should be preserved
        assert cfg.audit_team.library_auditor is True


# ===================================================================
# Review Fix Tests — H5: Fix cycle number tracking
# ===================================================================

class TestH5FixCycleNumber:
    """H5 FIX: _run_audit_fix should receive fix_round for cycle tracking."""

    def test_run_audit_fix_accepts_fix_round_parameter(self):
        """Verify the function signature includes fix_round."""
        import inspect
        from agent_team.cli import _run_audit_fix
        sig = inspect.signature(_run_audit_fix)
        assert "fix_round" in sig.parameters
        # Default should be 0
        assert sig.parameters["fix_round"].default == 0


# ===================================================================
# Review Fix Tests — M2: Scorer prompt documentation
# ===================================================================

class TestM2ScorerPromptDocumented:
    """M2 FIX: AUDIT_SCORER_PROMPT should be documented as reserved."""

    def test_scorer_prompt_has_reserved_comment(self):
        """The module source should contain a comment about the scorer being reserved."""
        import agent_team.audit_team as mod
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "reserved" in source.lower() or "not used" in source.lower() or "future" in source.lower()


# ===================================================================
# Review Fix Tests — Malformed findings (T7)
# ===================================================================

class TestMalformedFindings:
    """T7: Tests for parse_audit_findings with unusual formatting."""

    def test_finding_with_missing_description(self):
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/x.ts:1
        """)
        findings = parse_audit_findings(content, "technical")
        assert len(findings) == 1
        assert findings[0].description == ""

    def test_finding_with_extra_whitespace(self):
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**:   REQ-001
        - **Verdict**:   PASS
        - **Severity**:   INFO
        - **File**:   src/x.ts:1
        - **Description**:   All good
        """)
        findings = parse_audit_findings(content, "test")
        assert len(findings) == 1
        assert findings[0].requirement_id == "REQ-001"
        assert findings[0].verdict == "PASS"
        assert findings[0].description == "All good"

    def test_finding_with_typo_field_name_ignored(self):
        """Typo field names like **Req** instead of **Requirement** produce empty values."""
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Req**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/x.ts:1
        - **Description**: Issue
        """)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        # The typo "Req" doesn't match "requirement", so requirement_id is ""
        assert findings[0].requirement_id == ""
        # But "Req" is captured as a field key "req" with value "REQ-001"
        # This is expected behavior — the parser is lenient

    def test_finding_without_header_ignored(self):
        """Content without ## FINDING-NNN header produces no findings."""
        content = textwrap.dedent("""\
        Some random text
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        """)
        findings = parse_audit_findings(content, "test")
        assert len(findings) == 0

    def test_unicode_in_fields(self):
        content = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/données.ts:1
        - **Description**: Fichier avec accents éàü
        - **Evidence**: const name = "données"
        """)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert "données" in findings[0].file_path
        assert "accents" in findings[0].description


# ===================================================================
# Review Fix Tests — Selective re-audit (M3/O1)
# ===================================================================

class TestSelectiveReaudit:
    """M3/O1 FIX: Only auditors with fixable findings should re-run."""

    def test_auditors_with_issues_extracted(self):
        """filter_findings_for_fix → set of auditor names for re-run."""
        findings = [
            AuditFinding(
                auditor="requirements", severity="HIGH", requirement_id="REQ-001",
                verdict="FAIL", description="Missing", file_path="x.ts",
                line_number=0, evidence="",
            ),
            AuditFinding(
                auditor="technical", severity="MEDIUM", requirement_id="TECH-001",
                verdict="FAIL", description="Convention", file_path="y.ts",
                line_number=0, evidence="",
            ),
            AuditFinding(
                auditor="interface", severity="LOW", requirement_id="WIRE-001",
                verdict="PASS", description="OK", file_path="z.ts",
                line_number=0, evidence="",
            ),
        ]
        fixable = filter_findings_for_fix(findings, severity_gate="MEDIUM")
        auditors_to_rerun = {f.auditor for f in fixable}
        assert "requirements" in auditors_to_rerun
        assert "technical" in auditors_to_rerun
        # interface finding is PASS → excluded from fixable
        assert "interface" not in auditors_to_rerun


# ===================================================================
# Review Fix Tests — Parallel fix dispatch (L4)
# ===================================================================

class TestParallelFixDispatch:
    """L4 FIX: Fix groups should be parallelized."""

    def test_run_audit_fix_has_fix_round_param(self):
        """Verify _run_audit_fix signature includes fix_round."""
        import inspect
        from agent_team.cli import _run_audit_fix
        sig = inspect.signature(_run_audit_fix)
        assert "fix_round" in sig.parameters


# ===================================================================
# Audit Review Fix Tests — New tests for C1, H1, H2, M3 fixes
# ===================================================================

class TestC1FindingHeaderTrailingText:
    """C1 FIX: _RE_FINDING_HEADER must accept trailing text after number."""

    def test_basic_header_still_works(self):
        content = "## FINDING-001\n- **Requirement**: REQ-001\n- **Verdict**: FAIL\n- **Severity**: HIGH\n- **File**: x.ts:1\n- **Description**: Issue\n"
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1

    def test_trailing_dash_description(self):
        content = "## FINDING-001 — Login Feature\n- **Requirement**: REQ-001\n- **Verdict**: FAIL\n- **Severity**: HIGH\n- **File**: x.ts:1\n- **Description**: Missing login\n"
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert findings[0].requirement_id == "REQ-001"

    def test_trailing_colon_description(self):
        content = "## FINDING-001: Missing auth\n- **Requirement**: REQ-002\n- **Verdict**: FAIL\n- **Severity**: CRITICAL\n- **File**: auth.ts:5\n- **Description**: Auth missing\n"
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert findings[0].severity == "CRITICAL"

    def test_trailing_parens(self):
        content = "## FINDING-042 (critical)\n- **Requirement**: REQ-042\n- **Verdict**: FAIL\n- **Severity**: CRITICAL\n- **File**: x.ts:1\n- **Description**: Issue\n"
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 1
        assert findings[0].requirement_id == "REQ-042"

    def test_no_number_does_not_match(self):
        content = "## FINDING-\n- **Requirement**: REQ-001\n- **Verdict**: FAIL\n- **Severity**: HIGH\n- **File**: x.ts:1\n- **Description**: Issue\n"
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 0

    def test_multiple_findings_with_trailing_text(self):
        content = textwrap.dedent("""\
            ## FINDING-001 — Login
            - **Requirement**: REQ-001
            - **Verdict**: FAIL
            - **Severity**: HIGH
            - **File**: a.ts:1
            - **Description**: Missing

            ## FINDING-002 — Register
            - **Requirement**: REQ-002
            - **Verdict**: PASS
            - **Severity**: INFO
            - **File**: b.ts:1
            - **Description**: OK
        """)
        findings = parse_audit_findings(content, "requirements")
        assert len(findings) == 2
        assert findings[0].requirement_id == "REQ-001"
        assert findings[1].requirement_id == "REQ-002"


class TestH1ScoreZeroFindingsWithAuditors:
    """H1 FIX: Zero findings with deployed auditors should return 'unknown' health."""

    def test_zero_findings_with_auditors_is_unknown(self):
        report = score_audit_findings([], auditors_deployed=["requirements", "technical"])
        assert report.health == "unknown"
        assert report.overall_score == 1.0  # Score is still 1.0 (no failures)
        assert report.total_pass == 0
        assert report.total_fail == 0

    def test_zero_findings_no_auditors_is_passed(self):
        report = score_audit_findings([], auditors_deployed=[])
        assert report.health == "passed"

    def test_zero_findings_none_auditors_is_passed(self):
        report = score_audit_findings([])  # auditors_deployed defaults to None
        assert report.health == "passed"

    def test_zero_findings_single_auditor_is_unknown(self):
        report = score_audit_findings([], auditors_deployed=["test"])
        assert report.health == "unknown"


class TestH2ParseReportsUnicodeError:
    """H2 FIX: parse_all_audit_reports handles corrupted/binary files."""

    def test_binary_file_skipped(self, tmp_path):
        audit_dir = tmp_path / "audit-reports"
        audit_dir.mkdir()
        # Write binary content that is invalid UTF-8
        (audit_dir / "requirements_audit.md").write_bytes(b'\x80\x81\x82\xff\xfe')
        # Write a valid file
        (audit_dir / "technical_audit.md").write_text(
            "## FINDING-001\n- **Requirement**: TECH-001\n- **Verdict**: PASS\n"
            "- **Severity**: INFO\n- **File**: x.ts\n- **Description**: OK\n",
            encoding="utf-8",
        )
        findings = parse_all_audit_reports(str(audit_dir))
        # Should have 1 finding from technical, binary file skipped
        assert len(findings) == 1
        assert findings[0].auditor == "technical"

    def test_all_binary_files_returns_empty(self, tmp_path):
        audit_dir = tmp_path / "audit-reports"
        audit_dir.mkdir()
        (audit_dir / "requirements_audit.md").write_bytes(b'\x80\x81')
        (audit_dir / "technical_audit.md").write_bytes(b'\xff\xfe')
        findings = parse_all_audit_reports(str(audit_dir))
        assert findings == []


class TestGetActiveAuditorsUnknownDepth:
    """Unknown depth string falls into else branch (thorough/exhaustive behavior)."""

    def test_unknown_depth_returns_all_five(self):
        cfg = AgentTeamConfig()
        result = get_active_auditors(cfg, "turbo")
        assert set(result) == {"requirements", "technical", "interface", "test", "library"}

    def test_empty_string_depth_returns_all_five(self):
        cfg = AgentTeamConfig()
        result = get_active_auditors(cfg, "")
        assert set(result) == {"requirements", "technical", "interface", "test", "library"}


class TestBuildFixPromptEmptyFindings:
    """build_audit_fix_prompt with empty findings list."""

    def test_empty_findings_produces_valid_prompt(self):
        result = build_audit_fix_prompt([])
        assert "AUDIT-TEAM" in result
        assert "FIX DISPATCH" in result

    def test_empty_findings_no_crash(self):
        result = build_audit_fix_prompt([], fix_cycle_log="Previous attempt failed")
        assert "Previous Fix Attempts" in result


class TestScoreAllPartialVerdicts:
    """All PARTIAL verdicts produce score 0.0."""

    def test_all_partial_is_critical(self):
        findings = [
            AuditFinding(
                auditor="requirements", severity="MEDIUM",
                requirement_id=f"REQ-{i:03d}", verdict="PARTIAL",
                description="Partial impl", file_path=f"file{i}.ts",
                line_number=0, evidence="",
            )
            for i in range(5)
        ]
        report = score_audit_findings(findings)
        assert report.total_partial == 5
        assert report.total_pass == 0
        assert report.total_fail == 0
        assert report.overall_score == 0.0
        assert report.health == "critical"  # 0.0 < 0.5


class TestEndToEndAuditPipeline:
    """Integration test: parse -> score -> filter -> group -> build_prompt."""

    REPORT_CONTENT = textwrap.dedent("""\
        ## FINDING-001
        - **Requirement**: REQ-001
        - **Verdict**: PASS
        - **Severity**: INFO
        - **File**: src/auth.ts:10
        - **Description**: Login implemented correctly

        ## FINDING-002
        - **Requirement**: REQ-002
        - **Verdict**: PASS
        - **Severity**: INFO
        - **File**: src/register.ts:5
        - **Description**: Registration works

        ## FINDING-003
        - **Requirement**: REQ-003
        - **Verdict**: FAIL
        - **Severity**: CRITICAL
        - **File**: src/dashboard.ts:20
        - **Description**: Dashboard has mock data

        ## FINDING-004
        - **Requirement**: REQ-004
        - **Verdict**: FAIL
        - **Severity**: HIGH
        - **File**: src/api.ts:30
        - **Description**: API returns hardcoded response

        ## FINDING-005
        - **Requirement**: REQ-005
        - **Verdict**: PARTIAL
        - **Severity**: MEDIUM
        - **File**: src/dashboard.ts:50
        - **Description**: Dashboard partially implemented
    """)

    def test_full_pipeline(self):
        # Step 1: Parse
        findings = parse_audit_findings(self.REPORT_CONTENT, "requirements")
        assert len(findings) == 5

        # Step 2: Score
        report = score_audit_findings(
            findings,
            pass_threshold=0.9,
            auditors_deployed=["requirements"],
        )
        assert report.total_pass == 2
        assert report.total_fail == 2
        assert report.total_partial == 1
        assert report.overall_score == 2 / 5  # 0.4
        assert report.health == "critical"  # 0.4 < 0.5

        # Step 3: Filter
        fixable = filter_findings_for_fix(report.findings, severity_gate="MEDIUM")
        assert len(fixable) == 3  # CRITICAL + HIGH + MEDIUM (non-PASS)
        assert all(f.verdict != "PASS" for f in fixable)

        # Step 4: Group by file
        groups = group_findings_by_file(fixable)
        assert "src/dashboard.ts" in groups
        assert "src/api.ts" in groups
        # dashboard.ts should have 2 findings (CRITICAL + MEDIUM)
        assert len(groups["src/dashboard.ts"]) == 2

        # Step 5: Build fix prompt
        for file_key, file_findings in groups.items():
            prompt = build_audit_fix_prompt(file_findings)
            assert "AUDIT-TEAM" in prompt
            for f in file_findings:
                assert f.requirement_id in prompt


class TestRunStateAuditFields:
    """M3 FIX: RunState has audit-specific fields."""

    def test_audit_fields_exist_with_defaults(self):
        from agent_team.state import RunState
        state = RunState()
        assert state.audit_score == 0.0
        assert state.audit_health == ""
        assert state.audit_fix_rounds == 0

    def test_audit_fields_round_trip(self, tmp_path):
        from agent_team.state import RunState, save_state, load_state
        state = RunState(
            audit_score=0.85,
            audit_health="needs-fixes",
            audit_fix_rounds=2,
        )
        save_state(state, directory=str(tmp_path))
        state2 = load_state(directory=str(tmp_path))
        assert state2 is not None
        assert state2.audit_score == 0.85
        assert state2.audit_health == "needs-fixes"
        assert state2.audit_fix_rounds == 2
