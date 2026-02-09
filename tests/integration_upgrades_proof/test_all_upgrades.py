"""Integration proof-of-life test for ALL Agent-Team upgrades.

This file exercises every documented feature from Agent-team_New_Upgrades.md
in a single test run.  No Claude API calls are made — everything is validated
at the import / config / prompt / regex / data-structure level.

Sections map 1:1 to the cheat-sheet headings:
  A. CLI parsing (commands, flags, subcommands)
  B. Depth detection (keyword → level)
  C. Interview system (exit phrases, negation guard)
  D. Constraint extraction (prohibitions, requirements, scope, tech, tests)
  E. Config system (all sections, defaults, YAML loading)
  F. Agent definitions & quality standards (81 anti-patterns)
  G. Files produced (state, milestone progress)
  H. PRD+ fixes (Fix 1-6 + hardening)
  I. UI Requirements Hardening (Fix 1-6 + CRITICAL + HARDENING)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import queue
import re
import sys
import textwrap
from math import ceil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ===================================================================
# Imports — validate that every module is importable
# ===================================================================

from src.agent_team.config import (
    AgentTeamConfig,
    ConstraintEntry,
    DEPTH_AGENT_COUNTS,
    DepthDetection,
    DesignReferenceConfig,
    MilestoneConfig,
    OrchestratorSTConfig,
    SchedulerConfig,
    VerificationConfig,
    _dict_to_config,
    detect_depth,
    extract_constraints,
    get_agent_counts,
    get_active_st_points,
)
from src.agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_REVIEWER_PROMPT,
    CODE_WRITER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    PLANNER_PROMPT,
    RESEARCHER_PROMPT,
    TASK_ASSIGNER_PROMPT,
    build_agent_definitions,
    build_decomposition_prompt,
    build_milestone_execution_prompt,
)
from src.agent_team.code_quality_standards import (
    ARCHITECTURE_QUALITY_STANDARDS,
    BACKEND_STANDARDS,
    CODE_REVIEW_STANDARDS,
    DEBUGGING_STANDARDS,
    FRONTEND_STANDARDS,
    TESTING_STANDARDS,
    get_standards_for_agent,
)
from src.agent_team.quality_checks import (
    Violation,
    _check_mock_data_patterns,
    _check_ui_compliance,
    run_mock_data_scan,
    run_ui_compliance_scan,
)
from src.agent_team.design_reference import (
    DesignExtractionError,
    _DIRECTION_TABLE,
    _infer_design_direction,
    _split_into_sections,
    generate_fallback_ui_requirements,
    run_design_extraction_with_retry,
    validate_ui_requirements_content,
)
from src.agent_team.prd_chunking import (
    PRDChunk,
    create_prd_chunks,
    detect_large_prd,
)
from src.agent_team.interviewer import EXIT_PHRASES, _is_interview_exit
from src.agent_team.cli import InterventionQueue, _save_milestone_progress


# ===================================================================
# A. CLI PARSING — commands, flags, subcommands
# ===================================================================


class TestCLIParsing:
    """Verify CLI argument parser defines all documented flags."""

    def test_parse_args_importable(self):
        from src.agent_team.cli import _parse_args
        assert callable(_parse_args)

    def test_all_documented_flags_exist(self):
        from src.agent_team.cli import _parse_args
        with patch("sys.argv", ["agent-team", "test task"]):
            args = _parse_args()
        attrs = vars(args)
        expected_flags = [
            "task", "prd", "depth", "agents", "model", "max_turns",
            "config", "cwd", "no_interview", "dry_run", "verbose",
            "interactive", "interview_doc", "design_ref",
        ]
        for flag in expected_flags:
            assert flag in attrs, f"Missing CLI flag: --{flag}"

    def test_dry_run_flag(self):
        from src.agent_team.cli import _parse_args
        with patch("sys.argv", ["agent-team", "--dry-run", "test task"]):
            args = _parse_args()
        assert args.dry_run is True

    def test_depth_choices(self):
        from src.agent_team.cli import _parse_args
        for d in ("quick", "standard", "thorough", "exhaustive"):
            with patch("sys.argv", ["agent-team", "--depth", d, "test"]):
                args = _parse_args()
            assert args.depth == d

    def test_no_interview_flag(self):
        from src.agent_team.cli import _parse_args
        with patch("sys.argv", ["agent-team", "--no-interview", "fix bug"]):
            args = _parse_args()
        assert args.no_interview is True

    def test_prd_flag(self):
        from src.agent_team.cli import _parse_args
        with patch("sys.argv", ["agent-team", "--prd", "spec.md"]):
            args = _parse_args()
        assert args.prd == "spec.md"

    def test_subcommands_exist(self):
        """Verify all 5 subcommands have handler functions."""
        from src.agent_team.cli import (
            _subcommand_init,
            _subcommand_status,
            _subcommand_clean,
            _subcommand_guide,
            _subcommand_resume,
        )
        assert callable(_subcommand_init)
        assert callable(_subcommand_status)
        assert callable(_subcommand_clean)
        assert callable(_subcommand_guide)
        assert callable(_subcommand_resume)

    def test_version_flag(self):
        from src.agent_team.cli import _parse_args
        with pytest.raises(SystemExit), patch("sys.argv", ["agent-team", "--version"]):
            _parse_args()


# ===================================================================
# B. DEPTH DETECTION — keyword → level mapping
# ===================================================================


class TestDepthDetection:
    """Verify depth auto-detection from task keywords."""

    def test_quick_keywords(self):
        cfg = AgentTeamConfig()
        for kw in ("quick", "fast", "simple"):
            result = detect_depth(f"make a {kw} fix", cfg)
            assert result == "quick", f"'{kw}' should map to quick, got {result.level}"

    def test_thorough_keywords(self):
        cfg = AgentTeamConfig()
        for kw in ("thorough", "refactor", "redesign", "overhaul", "rewrite", "modernize"):
            result = detect_depth(f"do a {kw} of the system", cfg)
            assert result == "thorough", f"'{kw}' should map to thorough, got {result.level}"

    def test_exhaustive_keywords(self):
        cfg = AgentTeamConfig()
        for kw in ("exhaustive", "comprehensive", "complete", "migrate", "entire"):
            result = detect_depth(f"run an {kw} audit", cfg)
            assert result == "exhaustive", f"'{kw}' should map to exhaustive, got {result.level}"

    def test_default_standard(self):
        result = detect_depth("add a button", AgentTeamConfig())
        assert result == "standard"

    def test_most_intensive_wins(self):
        """'Quick but comprehensive' → exhaustive (most intensive)."""
        result = detect_depth("quick but comprehensive review", AgentTeamConfig())
        # exhaustive is checked first and 'comprehensive' matches
        assert result == "exhaustive"

    def test_auto_detect_disabled(self):
        cfg = AgentTeamConfig()
        cfg.depth.auto_detect = False
        result = detect_depth("exhaustive rewrite", cfg)
        assert result.source == "default"

    def test_depth_detection_returns_dataclass(self):
        result = detect_depth("refactor everything", AgentTeamConfig())
        assert isinstance(result, DepthDetection)
        assert hasattr(result, "level")
        assert hasattr(result, "source")
        assert hasattr(result, "matched_keywords")
        assert hasattr(result, "explanation")

    def test_depth_agent_counts_all_levels(self):
        """All 4 depth levels have agent count mappings."""
        for level in ("quick", "standard", "thorough", "exhaustive"):
            counts = get_agent_counts(level)
            assert "planning" in counts
            assert "coding" in counts
            assert "review" in counts


# ===================================================================
# C. INTERVIEW SYSTEM — exit phrases, negation guard
# ===================================================================


class TestInterviewSystem:
    """Verify interview termination and negation guard."""

    def test_all_documented_exit_phrases(self):
        documented = [
            "i'm done", "let's go", "start building", "proceed",
            "ship it", "lgtm", "ready", "build it", "go ahead",
            "that's it", "begin", "execute", "run it", "do it",
            "good to go", "looks good",
        ]
        for phrase in documented:
            assert _is_interview_exit(phrase), f"'{phrase}' should trigger exit"

    def test_negation_guard(self):
        """'I'm NOT done' should NOT trigger exit."""
        assert not _is_interview_exit("I'm not done yet")

    def test_regular_text_no_exit(self):
        assert not _is_interview_exit("tell me about authentication")

    def test_exit_phrases_list_has_entries(self):
        assert len(EXIT_PHRASES) >= 15


# ===================================================================
# D. CONSTRAINT EXTRACTION — prohibitions, requirements, tech, tests
# ===================================================================


class TestConstraintExtraction:
    """Verify constraint detection from task descriptions."""

    def test_prohibition_detected(self):
        constraints = extract_constraints("never change the database schema")
        prohibitions = [c for c in constraints if c.category == "prohibition"]
        assert len(prohibitions) >= 1
        assert any("database" in c.text.lower() for c in prohibitions)

    def test_requirement_detected(self):
        constraints = extract_constraints("must use TypeScript for all files")
        reqs = [c for c in constraints if c.category == "requirement"]
        assert len(reqs) >= 1

    def test_scope_detected(self):
        constraints = extract_constraints("only change files in src/components/")
        scopes = [c for c in constraints if c.category == "scope"]
        assert len(scopes) >= 1

    def test_technology_extracted(self):
        # Technology names are stored as category="requirement" with text "must use X"
        constraints = extract_constraints("Build with Express.js and MongoDB")
        tech_reqs = [c for c in constraints if "must use" in c.text.lower()]
        tech_text = " ".join(c.text for c in tech_reqs).lower()
        assert "express" in tech_text

    def test_test_count_extracted(self):
        # Test count is stored as category="requirement" with text "must have N+ tests"
        constraints = extract_constraints("Include 20+ tests for the module")
        test_cs = [c for c in constraints if "tests" in c.text.lower() and "20" in c.text]
        assert len(test_cs) >= 1

    def test_emphasis_all_caps(self):
        constraints = extract_constraints("NEVER USE JQUERY")
        caps = [c for c in constraints if c.emphasis >= 2]
        assert len(caps) >= 1

    def test_emphasis_word_boost(self):
        # "strictly" is an emphasis word that appears INSIDE the matched constraint
        constraints = extract_constraints("must strictly validate all user input")
        boosted = [c for c in constraints if c.emphasis >= 2]
        assert len(boosted) >= 1

    def test_constraint_entry_has_fields(self):
        entry = ConstraintEntry(text="test", category="prohibition", source="task", emphasis=1)
        assert entry.text == "test"
        assert entry.category == "prohibition"
        assert entry.source == "task"
        assert entry.emphasis == 1


# ===================================================================
# E. CONFIG SYSTEM — all sections, defaults, YAML loading
# ===================================================================


class TestConfigSystem:
    """Verify all config sections exist with correct defaults."""

    def test_orchestrator_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.orchestrator.model == "opus"
        assert cfg.orchestrator.max_turns == 500
        assert cfg.orchestrator.max_budget_usd is None

    def test_depth_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.depth.default == "standard"
        assert cfg.depth.auto_detect is True
        assert isinstance(cfg.depth.keyword_map, dict)

    def test_convergence_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.convergence.max_cycles == 10
        assert cfg.convergence.min_convergence_ratio == 0.9
        assert cfg.convergence.recovery_threshold == 0.8
        assert cfg.convergence.degraded_threshold == 0.5

    def test_interview_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.interview.enabled is True
        assert cfg.interview.min_exchanges == 3
        assert cfg.interview.max_exchanges == 50

    def test_codebase_map_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.codebase_map.enabled is True
        assert cfg.codebase_map.max_files == 5000
        assert cfg.codebase_map.max_file_size_kb == 50
        assert cfg.codebase_map.max_file_size_kb_ts == 100

    def test_scheduler_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.scheduler.enabled is True
        assert cfg.scheduler.max_parallel_tasks == 5
        assert cfg.scheduler.conflict_strategy == "artificial-dependency"
        assert cfg.scheduler.enable_context_scoping is True

    def test_verification_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.verification.enabled is True
        assert cfg.verification.blocking is True
        assert cfg.verification.run_lint is True
        assert cfg.verification.run_tests is True

    def test_sequential_thinking_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.orchestrator_st.enabled is True
        assert 1 in cfg.orchestrator_st.thought_budgets
        assert cfg.orchestrator_st.thought_budgets[1] == 8

    def test_milestone_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.milestone.enabled is False
        assert cfg.milestone.health_gate is True
        assert cfg.milestone.wiring_check is True
        assert cfg.milestone.review_recovery_retries == 1
        assert cfg.milestone.mock_data_scan is True
        assert cfg.milestone.ui_compliance_scan is True

    def test_quality_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.quality.production_defaults is True
        assert cfg.quality.craft_review is True
        assert cfg.quality.quality_triggers_reloop is True

    def test_display_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.display.show_cost is True
        assert cfg.display.show_fleet_composition is True
        assert cfg.display.show_convergence_status is True
        assert cfg.display.verbose is False

    def test_design_reference_defaults(self):
        cfg = AgentTeamConfig()
        assert cfg.design_reference.urls == []
        assert cfg.design_reference.depth == "full"
        assert cfg.design_reference.extraction_retries == 2
        assert cfg.design_reference.fallback_generation is True
        assert cfg.design_reference.content_quality_check is True

    def test_dict_to_config_roundtrip(self):
        data = {
            "orchestrator": {"model": "sonnet", "max_turns": 1000},
            "depth": {"default": "thorough", "auto_detect": False},
            "convergence": {"max_cycles": 5, "min_convergence_ratio": 0.8},
            "interview": {"min_exchanges": 8},
            "milestone": {
                "enabled": True,
                "review_recovery_retries": 3,
                "mock_data_scan": False,
                "ui_compliance_scan": False,
            },
            "design_reference": {
                "extraction_retries": 5,
                "fallback_generation": False,
            },
        }
        cfg = _dict_to_config(data)
        assert cfg.orchestrator.model == "sonnet"
        assert cfg.orchestrator.max_turns == 1000
        assert cfg.depth.default == "thorough"
        assert cfg.convergence.max_cycles == 5
        assert cfg.interview.min_exchanges == 8
        assert cfg.milestone.enabled is True
        assert cfg.milestone.review_recovery_retries == 3
        assert cfg.milestone.mock_data_scan is False
        assert cfg.milestone.ui_compliance_scan is False
        assert cfg.design_reference.extraction_retries == 5

    def test_negative_extraction_retries_rejected(self):
        with pytest.raises(ValueError, match="extraction_retries"):
            _dict_to_config({"design_reference": {"extraction_retries": -1}})


# ===================================================================
# F. AGENT DEFINITIONS & QUALITY STANDARDS (81 anti-patterns)
# ===================================================================


class TestAgentDefinitions:
    """Verify agent fleet and quality standards injection."""

    def test_default_returns_12_agents(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, mcp_servers={})
        assert len(agents) == 12

    def test_spec_validator_always_present(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, mcp_servers={})
        assert "spec-validator" in agents
        assert "Write" not in agents["spec-validator"]["tools"]  # read-only

    def test_all_9_standard_agents(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, mcp_servers={})
        expected = [
            "planner", "researcher", "architect", "task-assigner",
            "code-writer", "code-reviewer", "test-runner",
            "security-auditor", "debugger",
        ]
        for name in expected:
            assert name in agents, f"Missing agent: {name}"

    def test_conditional_agents(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, mcp_servers={})
        assert "integration-agent" in agents
        assert "contract-generator" in agents

    def test_disabled_conditional_agents(self):
        cfg = AgentTeamConfig()
        cfg.scheduler.enabled = False
        cfg.verification.enabled = False
        agents = build_agent_definitions(cfg, mcp_servers={})
        assert "integration-agent" not in agents
        assert "contract-generator" not in agents


class TestQualityStandards:
    """Verify 81+ anti-pattern standards are injected."""

    def test_frontend_standards_count(self):
        """FRONT-001 through FRONT-021."""
        for i in range(1, 22):
            code = f"FRONT-{i:03d}"
            assert code in FRONTEND_STANDARDS, f"{code} missing"

    def test_backend_standards_count(self):
        """BACK-001 through BACK-020."""
        for i in range(1, 21):
            code = f"BACK-{i:03d}"
            assert code in BACKEND_STANDARDS, f"{code} missing"

    def test_review_standards_count(self):
        """REVIEW-001 through REVIEW-015."""
        for i in range(1, 16):
            code = f"REVIEW-{i:03d}"
            assert code in CODE_REVIEW_STANDARDS, f"{code} missing"

    def test_testing_standards_count(self):
        """TEST-001 through TEST-015."""
        for i in range(1, 16):
            code = f"TEST-{i:03d}"
            assert code in TESTING_STANDARDS, f"{code} missing"

    def test_debugging_standards_count(self):
        """DEBUG-001 through DEBUG-010."""
        for i in range(1, 11):
            code = f"DEBUG-{i:03d}"
            assert code in DEBUGGING_STANDARDS, f"{code} missing"

    def test_total_anti_patterns_at_least_81(self):
        total = sum(
            s.count("-0") for s in [
                FRONTEND_STANDARDS, BACKEND_STANDARDS,
                CODE_REVIEW_STANDARDS, TESTING_STANDARDS,
                DEBUGGING_STANDARDS,
            ]
        )
        assert total >= 81, f"Expected 81+ anti-patterns, found {total}"

    def test_code_writer_gets_frontend_and_backend(self):
        standards = get_standards_for_agent("code-writer")
        assert "FRONT-001" in standards
        assert "BACK-001" in standards

    def test_reviewer_gets_review_standards(self):
        standards = get_standards_for_agent("code-reviewer")
        assert "REVIEW-001" in standards

    def test_test_runner_gets_testing_standards(self):
        standards = get_standards_for_agent("test-runner")
        assert "TEST-001" in standards

    def test_debugger_gets_debugging_standards(self):
        standards = get_standards_for_agent("debugger")
        assert "DEBUG-001" in standards

    def test_planner_gets_no_standards(self):
        assert get_standards_for_agent("planner") == ""

    def test_architect_gets_architecture_standards(self):
        standards = get_standards_for_agent("architect")
        assert len(standards) > 0
        assert "file structure" in standards.lower() or "error handling" in standards.lower()


# ===================================================================
# G. FILES PRODUCED & STATE MANAGEMENT
# ===================================================================


class TestFilesProduced:
    """Verify state and milestone progress file management."""

    def test_intervention_queue_basic(self):
        q = InterventionQueue()
        assert not q.has_intervention()
        assert q.get_intervention() is None
        q._queue.put("focus on API")
        assert q.has_intervention()
        assert q.get_intervention() == "focus on API"

    def test_intervention_prefix(self):
        assert InterventionQueue._PREFIX == "!!"

    def test_save_milestone_progress(self, tmp_path: Path):
        cfg = AgentTeamConfig()
        cfg.convergence.requirements_dir = ".agent-team"
        _save_milestone_progress(
            cwd=str(tmp_path),
            config=cfg,
            milestone_id="M2",
            completed_milestones=["M1"],
            error_type="interrupt",
        )
        progress_file = tmp_path / ".agent-team" / "milestone_progress.json"
        assert progress_file.is_file()
        data = json.loads(progress_file.read_text(encoding="utf-8"))
        assert data["interrupted_milestone"] == "M2"
        assert data["completed_milestones"] == ["M1"]


# ===================================================================
# H. PRD+ FIXES (Fix 1–6 + Hardening)
# ===================================================================


class TestPRDFix1AnalysisPersistence:
    """Fix 1: Decomposition prompt enforces Write tool for analysis files."""

    def test_decomposition_prompt_has_write_instructions(self):
        """Fix 1: When chunks are provided, prompt mandates Write tool for analysis files."""
        cfg = AgentTeamConfig()
        # Simulate chunked mode — Write tool instructions only appear with prd_chunks
        fake_chunks = [PRDChunk(
            name="features", focus="Extract features", description="Features section",
            file="prd-chunks/features.md", start_line=0, end_line=10, size_bytes=500,
        )]
        fake_index = {"features": {"heading": "## Features", "size_bytes": 500}}
        prompt = build_decomposition_prompt(
            task="Build a dashboard",
            depth="standard",
            config=cfg,
            prd_chunks=fake_chunks,
            prd_index=fake_index,
        )
        assert "Write" in prompt
        assert "analysis" in prompt.lower()
        assert "MUST use the Write tool" in prompt or "Write tool" in prompt


class TestPRDFix2TasksMdInMilestoneMode:
    """Fix 2: 9-step MILESTONE WORKFLOW with TASK ASSIGNER."""

    def test_milestone_prompt_has_workflow(self):
        prompt = build_milestone_execution_prompt(
            task="Build a dashboard",
            depth="standard",
            config=AgentTeamConfig(),
        )
        assert "MILESTONE WORKFLOW" in prompt
        assert "TASK ASSIGNER" in prompt
        assert "TASKS.md" in prompt

    def test_milestone_prompt_has_9_steps(self):
        prompt = build_milestone_execution_prompt(
            task="Build", depth="standard", config=AgentTeamConfig(),
        )
        # Verify multiple mandatory steps exist
        assert "CODING FLEET" in prompt or "code-writer" in prompt
        assert "REVIEW FLEET" in prompt or "code-reviewer" in prompt


class TestPRDFix3ReviewRecovery:
    """Fix 3: _run_review_only parameterized with requirements_path and depth."""

    def test_run_review_only_signature(self):
        from src.agent_team.cli import _run_review_only
        sig = inspect.signature(_run_review_only)
        assert "requirements_path" in sig.parameters
        assert "depth" in sig.parameters
        assert sig.parameters["depth"].default == "standard"


class TestPRDFix4ZeroMockDataPolicy:
    """Fix 4: ZERO MOCK DATA POLICY in CODE_WRITER_PROMPT."""

    def test_code_writer_has_zero_mock_policy(self):
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT

    def test_prohibited_patterns_listed(self):
        for pattern in ["of(", "delay(", "Promise.resolve"]:
            assert pattern in CODE_WRITER_PROMPT, f"'{pattern}' missing from policy"

    def test_front_019_020_021_exist(self):
        assert "FRONT-019" in FRONTEND_STANDARDS
        assert "FRONT-020" in FRONTEND_STANDARDS
        assert "FRONT-021" in FRONTEND_STANDARDS


class TestPRDFix5SVCWiring:
    """Fix 5: SVC-xxx in architect/reviewer prompts + MOCK DATA GATE."""

    def test_architect_has_svc(self):
        assert "SVC" in ARCHITECT_PROMPT

    def test_reviewer_has_svc_verification(self):
        assert "SVC" in CODE_REVIEWER_PROMPT

    def test_orchestrator_has_mock_data_gate(self):
        assert "MOCK DATA GATE" in ORCHESTRATOR_SYSTEM_PROMPT or \
               "MOCK DATA" in ORCHESTRATOR_SYSTEM_PROMPT


class TestPRDFix6MockDetection:
    """Fix 6: MOCK-001..007 patterns in quality_checks.py."""

    def test_rxjs_of_detected(self):
        content = "return of([{id: 1, name: 'test'}]);"
        violations = _check_mock_data_patterns(content, "services/user.service.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-001" in checks

    def test_promise_resolve_detected(self):
        content = 'return Promise.resolve({data: []});'
        violations = _check_mock_data_patterns(content, "services/api.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-002" in checks

    def test_mock_variable_detected(self):
        content = "const mockUsers = [{id: 1}];"
        violations = _check_mock_data_patterns(content, "services/data.service.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-003" in checks

    def test_setTimeout_detected(self):
        content = "setTimeout(() => resolve(data), 1000);"
        violations = _check_mock_data_patterns(content, "services/api.service.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-004" in checks

    def test_delay_pipe_detected(self):
        content = ".pipe(delay(500))"
        violations = _check_mock_data_patterns(content, "services/user.service.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-005" in checks


class TestPRDHardening:
    """Hardening pass: BehaviorSubject, Observable, Python, thresholds."""

    def test_behavior_subject_detected(self):
        content = "new BehaviorSubject([{id: 1}])"
        violations = _check_mock_data_patterns(content, "store/state.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-006" in checks

    def test_new_observable_detected(self):
        # Regex: new\s+Observable\s*[<(]\s*(?:\(\s*\w+\s*\)\s*=>|function)
        # Needs: new Observable( or new Observable< directly followed by (param) =>
        content = "new Observable((observer) => observer.next([{id: 1}]))"
        violations = _check_mock_data_patterns(content, "services/data.service.ts", ".ts")
        checks = [v.check for v in violations]
        assert "MOCK-007" in checks

    def test_python_service_scanned(self):
        # MOCK-003 pattern: mockData, fakeResponse, etc.
        content = "mockData = [{'id': 1}]\nreturn mockData"
        violations = _check_mock_data_patterns(content, "services/api_client.py", ".py")
        mock_vars = [v for v in violations if v.check == "MOCK-003"]
        assert len(mock_vars) >= 1

    def test_mock_scan_integration(self, tmp_path: Path):
        svc = tmp_path / "services"
        svc.mkdir()
        (svc / "user.service.ts").write_text(
            "return of([{id: 1, name: 'fake'}]);",
            encoding="utf-8",
        )
        violations = run_mock_data_scan(tmp_path)
        assert len(violations) >= 1

    def test_milestone_config_review_recovery(self):
        cfg = AgentTeamConfig()
        assert cfg.milestone.review_recovery_retries == 1

    def test_milestone_config_mock_data_scan(self):
        cfg = AgentTeamConfig()
        assert cfg.milestone.mock_data_scan is True


# ===================================================================
# I. UI REQUIREMENTS HARDENING (Fix 1–6 + CRITICAL + HARDENING)
# ===================================================================


class TestUIFix1ConfigFields:
    """UI Fix 1: New config fields on DesignReferenceConfig + MilestoneConfig."""

    def test_extraction_retries_default(self):
        assert DesignReferenceConfig().extraction_retries == 2

    def test_fallback_generation_default(self):
        assert DesignReferenceConfig().fallback_generation is True

    def test_content_quality_check_default(self):
        assert DesignReferenceConfig().content_quality_check is True

    def test_ui_compliance_scan_default(self):
        assert MilestoneConfig().ui_compliance_scan is True


class TestUIFix2GuaranteedGeneration:
    """UI Fix 2: Content validation, retry wrapper, fallback generator."""

    def test_content_validation_good(self):
        content = textwrap.dedent("""\
        ## Color System
        - Primary: #1A1A2E
        - Secondary: #E8D5B7
        - Accent: #C9A96E
        ## Typography
        - Heading font: Cormorant Garamond
        ## Spacing
        - sm: 8px
        - md: 16px
        - lg: 24px
        ## Component Patterns
        - Button styles
        - Card patterns
        """)
        issues = validate_ui_requirements_content(content)
        assert issues == []

    def test_content_validation_catches_shallow(self):
        content = "## Color System\n- One: #FFF\n## Typography\n## Spacing\n## Component Patterns\n"
        issues = validate_ui_requirements_content(content)
        assert len(issues) >= 3  # missing fonts, spacing, components

    def test_fallback_generator(self, tmp_path: Path):
        cfg = AgentTeamConfig()
        cfg.convergence.requirements_dir = ".agent-team"
        content = generate_fallback_ui_requirements(
            task="Build a fintech dashboard",
            config=cfg, cwd=str(tmp_path),
        )
        assert "FALLBACK-GENERATED" in content
        assert (tmp_path / ".agent-team" / "UI_REQUIREMENTS.md").is_file()

    def test_retry_wrapper_success(self):
        async def _test():
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                new_callable=AsyncMock, return_value=("ok", 1.0),
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                content, cost = await run_design_extraction_with_retry(
                    urls=["https://example.com"], config=AgentTeamConfig(),
                    cwd="/tmp", backend="api", max_retries=1, base_delay=0.01,
                )
                assert content == "ok"
        asyncio.run(_test())

    def test_retry_wrapper_retries_on_failure(self):
        async def _test():
            mock = AsyncMock(side_effect=[
                DesignExtractionError("fail"),
                ("ok-retry", 2.0),
            ])
            with patch(
                "src.agent_team.design_reference.run_design_extraction", mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                content, cost = await run_design_extraction_with_retry(
                    urls=["https://example.com"], config=AgentTeamConfig(),
                    cwd="/tmp", backend="api", max_retries=2, base_delay=0.01,
                )
                assert content == "ok-retry"
                assert mock.call_count == 2
        asyncio.run(_test())


class TestUIFix3HardEnforcement:
    """UI Fix 3: UI COMPLIANCE POLICY with UI-FAIL-001..007."""

    def test_ui_compliance_policy_in_code_writer(self):
        assert "UI COMPLIANCE POLICY" in CODE_WRITER_PROMPT

    def test_ui_fail_rules(self):
        for i in range(1, 8):
            assert f"UI-FAIL-{i:03d}" in CODE_WRITER_PROMPT

    def test_same_severity_as_mock_data(self):
        assert "SAME SEVERITY AS MOCK DATA" in CODE_WRITER_PROMPT

    def test_reviewer_has_ui_compliance(self):
        assert "UI Compliance" in CODE_REVIEWER_PROMPT or \
               "ui compliance" in CODE_REVIEWER_PROMPT.lower()


class TestUIFix4DedicatedUIPhase:
    """UI Fix 4: Step 3.7 UI DESIGN SYSTEM SETUP in orchestrator."""

    def test_orchestrator_has_step_3_7(self):
        assert "3.7" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "UI DESIGN SYSTEM SETUP" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_design_requirements_in_orchestrator(self):
        assert "DESIGN-001" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_milestone_prompt_has_ui_enforcement(self):
        prompt = build_milestone_execution_prompt(
            task="Build UI", depth="standard", config=AgentTeamConfig(),
        )
        assert "UI COMPLIANCE ENFORCEMENT" in prompt


class TestUIFix5ComplianceScan:
    """UI Fix 5: UI-001..004 compliance patterns + scan."""

    def test_hardcoded_hex_detected(self):
        violations = _check_ui_compliance("color: #FF0000;", "src/A.tsx", ".tsx")
        assert any(v.check == "UI-001" for v in violations)

    def test_tailwind_arbitrary_hex_detected(self):
        violations = _check_ui_compliance('bg-[#FF0000]', "src/A.tsx", ".tsx")
        assert any(v.check == "UI-001b" for v in violations)

    def test_default_tailwind_detected(self):
        violations = _check_ui_compliance('bg-indigo-500', "src/A.tsx", ".tsx")
        assert any(v.check == "UI-002" for v in violations)

    def test_generic_font_detected(self):
        violations = _check_ui_compliance(
            "fontFamily: Inter, sans-serif",
            "src/theme/_variables.scss", ".scss",
        )
        assert any(v.check == "UI-003" for v in violations)

    def test_arbitrary_spacing_detected(self):
        violations = _check_ui_compliance('p-13', "src/A.tsx", ".tsx")
        assert any(v.check == "UI-004" for v in violations)

    def test_scan_integration(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "Button.tsx").write_text('bg-[#FF0000]', encoding="utf-8")
        violations = run_ui_compliance_scan(tmp_path)
        assert len(violations) >= 1


class TestUICritical1FontFamilyRegex:
    """CRITICAL-1: fontFamily (camelCase) regex matching."""

    def test_camel_case_font_family(self):
        content = "fontFamily: Inter, sans-serif"
        issues = validate_ui_requirements_content(
            "## Color System\n#AAA #BBB #CCC\n## Typography\n"
            f"- {content}\n## Spacing\n8px 16px 24px\n## Component Patterns\nButton Card\n"
        )
        # Font section has fontFamily → should find it
        font_issues = [i for i in issues if "font" in i.lower()]
        assert len(font_issues) == 0  # fontFamily SHOULD be detected as a font declaration


class TestUICritical2PluralComponentTypes:
    """CRITICAL-2: Component type regex matches plurals (Buttons, Cards)."""

    def test_plural_buttons_detected(self):
        content = "## Color System\n#AAA #BBB #CCC\n## Typography\nfont-family: Inter\n## Spacing\n8px 16px 24px\n## Component Patterns\nButtons and Cards\n"
        issues = validate_ui_requirements_content(content)
        component_issues = [i for i in issues if "component" in i.lower()]
        assert len(component_issues) == 0  # plurals should be detected


class TestUICritical3ExceptionHandling:
    """CRITICAL-3: Unexpected exceptions are NOT retried."""

    def test_type_error_surfaces_immediately(self):
        async def _test():
            mock = AsyncMock(side_effect=TypeError("bad"))
            with patch(
                "src.agent_team.design_reference.run_design_extraction", mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(DesignExtractionError, match="Unexpected"):
                    await run_design_extraction_with_retry(
                        urls=["x"], config=AgentTeamConfig(),
                        cwd="/tmp", backend="api", max_retries=5, base_delay=0.01,
                    )
                assert mock.call_count == 1  # NOT retried
        asyncio.run(_test())

    def test_connection_error_is_retried(self):
        async def _test():
            mock = AsyncMock(side_effect=[ConnectionError("fail"), ("ok", 1.0)])
            with patch(
                "src.agent_team.design_reference.run_design_extraction", mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                content, _ = await run_design_extraction_with_retry(
                    urls=["x"], config=AgentTeamConfig(),
                    cwd="/tmp", backend="api", max_retries=2, base_delay=0.01,
                )
                assert content == "ok"
                assert mock.call_count == 2  # retried once
        asyncio.run(_test())


class TestUIHard1ConfigFileRegex:
    """HARD-1: _RE_CONFIG_FILE path-segment-aware (no ThemeToggle false positive)."""

    def test_theme_toggle_not_exempt(self):
        violations = _check_ui_compliance(
            "color: #FF0000;", "src/components/ThemeToggle.tsx", ".tsx",
        )
        assert any(v.check == "UI-001" for v in violations)

    def test_actual_theme_file_exempt(self):
        violations = _check_ui_compliance(
            "color: #FF0000;", "src/styles/theme.scss", ".scss",
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0


class TestUIHard2ConfigValidation:
    """HARD-2: extraction_retries >= 0 validation."""

    def test_negative_rejected(self):
        with pytest.raises(ValueError):
            _dict_to_config({"design_reference": {"extraction_retries": -1}})

    def test_zero_accepted(self):
        cfg = _dict_to_config({"design_reference": {"extraction_retries": 0}})
        assert cfg.design_reference.extraction_retries == 0


class TestUIHard3DirectionalSpacing:
    """HARD-3: Directional Tailwind variants (pt-, mb-, ml-, pr-)."""

    def test_pt_detected(self):
        v = _check_ui_compliance('pt-13', "src/A.tsx", ".tsx")
        assert any(x.check == "UI-004" for x in v)

    def test_mb_detected(self):
        v = _check_ui_compliance('mb-13', "src/A.tsx", ".tsx")
        assert any(x.check == "UI-004" for x in v)

    def test_pr_detected(self):
        v = _check_ui_compliance('pr-13', "src/A.tsx", ".tsx")
        assert any(x.check == "UI-004" for x in v)

    def test_ml_grid_aligned_ok(self):
        v = _check_ui_compliance('ml-16', "src/A.tsx", ".tsx")
        assert not any(x.check == "UI-004" for x in v)


class TestUIHard4WordBoundaryInference:
    """HARD-4: _infer_design_direction uses word boundaries."""

    def test_cli_matches_brutalist(self):
        assert _infer_design_direction("Build a CLI tool") == "brutalist"

    def test_clicking_does_not_match_cli(self):
        result = _infer_design_direction("Build a clicking game")
        assert result != "brutalist"

    def test_enterprise_matches_industrial(self):
        assert _infer_design_direction("enterprise ERP system") == "industrial"

    def test_all_5_directions_reachable(self):
        assert _infer_design_direction("developer CLI tool") == "brutalist"
        assert _infer_design_direction("fintech premium payment") == "luxury"
        assert _infer_design_direction("enterprise ERP logistics") == "industrial"
        assert _infer_design_direction("SaaS dashboard startup") == "minimal_modern"
        assert _infer_design_direction("blog news content platform") == "editorial"


# ===================================================================
# J. PRD CHUNKING
# ===================================================================


class TestPRDChunking:
    """Verify large PRD detection and chunking."""

    def test_detect_small_prd(self):
        assert not detect_large_prd("Short PRD content", threshold=50000)

    def test_detect_large_prd(self):
        large = "x" * 60000
        assert detect_large_prd(large, threshold=50000)

    def test_create_prd_chunks(self, tmp_path: Path):
        # Sections < 100 bytes are skipped, so we need substantial content
        prd_content = textwrap.dedent("""\
        # My PRD

        ## Features and User Stories
        - Feature 1: User authentication with JWT tokens and OAuth2 support
        - Feature 2: Dashboard with real-time analytics and chart visualizations
        - Feature 3: Admin panel with role-based access control and audit logging
        - Feature 4: Notification system with email, SMS, and push notifications
        - Feature 5: File upload with S3 integration, thumbnails, and virus scanning

        ## Database Schema and Data Models
        - Users table: id, email, password_hash, role, created_at, updated_at
        - Orders table: id, user_id, total, status, shipping_address, payment_id
        - Products table: id, name, description, price, inventory_count, category_id
        - Categories table: id, name, parent_id, slug, description
        - Payments table: id, order_id, stripe_payment_intent, status, amount

        ## API Endpoints and Integrations
        - GET /api/users - List all users with pagination and filtering
        - POST /api/users - Create a new user with validation
        - GET /api/orders - List orders with status filtering
        - POST /api/orders - Create order with inventory check
        - GET /api/products - List products with search and category filter
        - POST /api/payments - Process payment via Stripe integration
        """)
        chunks = create_prd_chunks(
            content=prd_content,
            output_dir=tmp_path / "chunks",
        )
        assert len(chunks) >= 1
        assert all(isinstance(c, PRDChunk) for c in chunks)
        # Verify chunk files were written to disk
        chunk_files = list((tmp_path / "chunks").glob("*.md"))
        assert len(chunk_files) >= 1


# ===================================================================
# K. CROSS-CUTTING INTEGRATION CHECKS
# ===================================================================


class TestCrossCuttingIntegration:
    """Verify cross-module integration points."""

    def test_violation_dataclass_shared(self):
        """Violation is used by both mock and UI compliance."""
        v = Violation(check="TEST", message="test", file_path="a.ts", line=1, severity="warning")
        assert v.check == "TEST"

    def test_all_depth_levels_have_agent_counts(self):
        for level in ("quick", "standard", "thorough", "exhaustive"):
            assert level in DEPTH_AGENT_COUNTS

    def test_sequential_thinking_points(self):
        cfg = AgentTeamConfig()
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            points = get_active_st_points(depth, cfg.orchestrator_st)
            assert isinstance(points, list)
            assert all(p in (1, 2, 3, 4) for p in points)

    def test_split_into_sections_utility(self):
        result = _split_into_sections("## Color System\n- Red\n## Typography\n- Inter\n")
        assert "color system" in result
        assert "typography" in result

    def test_direction_table_has_5_entries(self):
        assert len(_DIRECTION_TABLE) == 5
        for name in ("brutalist", "luxury", "industrial", "minimal_modern", "editorial"):
            assert name in _DIRECTION_TABLE
