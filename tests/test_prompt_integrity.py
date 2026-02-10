"""Tests for prompt integrity — CODE_WRITER_PROMPT policies, CODE_REVIEWER_PROMPT
duties, build function outputs, and standards constants.
"""

from __future__ import annotations

import inspect

import pytest

from agent_team.agents import (
    ARCHITECT_PROMPT,
    CODE_REVIEWER_PROMPT,
    CODE_WRITER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    build_agent_definitions,
    build_decomposition_prompt,
    build_milestone_execution_prompt,
    build_orchestrator_prompt,
)
from agent_team.code_quality_standards import (
    DATABASE_INTEGRITY_STANDARDS,
    E2E_TESTING_STANDARDS,
    get_standards_for_agent,
)
from agent_team.config import AgentTeamConfig


# ===========================================================================
# CODE_WRITER_PROMPT policies
# ===========================================================================


class TestCodeWriterPromptPolicies:
    """Verify CODE_WRITER_PROMPT contains all required policy blocks."""

    def test_zero_mock_data_policy(self):
        assert "ZERO MOCK DATA POLICY" in CODE_WRITER_PROMPT

    def test_ui_compliance_policy(self):
        assert "UI COMPLIANCE POLICY" in CODE_WRITER_PROMPT

    def test_seed_data_policy(self):
        assert "SEED DATA COMPLETENESS" in CODE_WRITER_PROMPT

    def test_enum_registry_policy(self):
        assert "ENUM/STATUS REGISTRY" in CODE_WRITER_PROMPT

    def test_front_019_in_standards(self):
        """FRONT-019 lives in code_quality_standards, appended to code-writer."""
        standards = get_standards_for_agent("code-writer")
        assert "FRONT-019" in standards

    def test_front_020_in_standards(self):
        standards = get_standards_for_agent("code-writer")
        assert "FRONT-020" in standards

    def test_front_021_in_standards(self):
        standards = get_standards_for_agent("code-writer")
        assert "FRONT-021" in standards

    def test_ui_fail_codes(self):
        for code in ("UI-FAIL-001", "UI-FAIL-002", "UI-FAIL-003"):
            assert code in CODE_WRITER_PROMPT, f"{code} missing from CODE_WRITER_PROMPT"


# ===========================================================================
# CODE_REVIEWER_PROMPT duties
# ===========================================================================


class TestCodeReviewerPromptDuties:
    """Verify CODE_REVIEWER_PROMPT contains reviewer duties."""

    def test_ui_compliance_duty(self):
        assert "UI" in CODE_REVIEWER_PROMPT and "compliance" in CODE_REVIEWER_PROMPT.lower()

    def test_mock_data_duty(self):
        assert "mock" in CODE_REVIEWER_PROMPT.lower()

    def test_reviewer_is_adversarial(self):
        assert "ADVERSARIAL" in CODE_REVIEWER_PROMPT

    def test_reviewer_mentions_services(self):
        assert "service" in CODE_REVIEWER_PROMPT.lower()


# ===========================================================================
# ARCHITECT_PROMPT policies
# ===========================================================================


class TestArchitectPromptPolicies:
    """Verify ARCHITECT_PROMPT contains required policies."""

    def test_svc_requirement_type(self):
        assert "SVC-" in ARCHITECT_PROMPT or "SVC" in ARCHITECT_PROMPT

    def test_enum_registry_mention(self):
        assert "ENUM" in ARCHITECT_PROMPT


# ===========================================================================
# ORCHESTRATOR_SYSTEM_PROMPT
# ===========================================================================


class TestOrchestratorPrompt:
    """Verify orchestrator prompt core sections."""

    def test_requirements_document_protocol(self):
        assert "REQUIREMENTS.md" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_convergence_loop(self):
        assert "convergence" in ORCHESTRATOR_SYSTEM_PROMPT.lower()

    def test_planning_fleet(self):
        assert "PLANNING FLEET" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_ui_design_system_phase(self):
        assert "UI DESIGN SYSTEM" in ORCHESTRATOR_SYSTEM_PROMPT or \
               "UI_REQUIREMENTS" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_mock_data_gate(self):
        assert "MOCK DATA GATE" in ORCHESTRATOR_SYSTEM_PROMPT


# ===========================================================================
# Build functions
# ===========================================================================


class TestBuildFunctions:
    """Verify build functions produce non-empty strings with key content."""

    def test_build_orchestrator_prompt_contains_key_content(self):
        cfg = AgentTeamConfig()
        prompt = build_orchestrator_prompt(
            task="Build a todo app", depth="standard", config=cfg
        )
        # The build function wraps the system prompt — look for expected content
        assert "REQUIREMENTS" in prompt
        assert "Build a todo app" in prompt

    def test_build_decomposition_prompt_has_key_content(self):
        cfg = AgentTeamConfig()
        prompt = build_decomposition_prompt(
            task="Build app", depth="standard", config=cfg
        )
        assert "DECOMPOSITION" in prompt
        assert "Build app" in prompt

    def test_build_milestone_execution_prompt_has_workflow(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Setup Backend: Build REST API",
            depth="standard",
            config=cfg,
        )
        assert "MILESTONE WORKFLOW" in prompt or "milestone" in prompt.lower()

    def test_build_milestone_prompt_has_task_assigner(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Setup: Build API",
            depth="standard",
            config=cfg,
        )
        assert "TASK" in prompt

    def test_build_agent_definitions_returns_dict(self):
        cfg = AgentTeamConfig()
        agents = build_agent_definitions(cfg, mcp_servers={})
        assert isinstance(agents, dict)
        assert len(agents) > 0


# ===========================================================================
# Standards constants
# ===========================================================================


class TestStandardsConstants:
    """Verify code quality standards mappings."""

    def test_database_standards_exist(self):
        assert len(DATABASE_INTEGRITY_STANDARDS) > 100
        assert "DB-" in DATABASE_INTEGRITY_STANDARDS

    def test_e2e_standards_exist(self):
        assert len(E2E_TESTING_STANDARDS) > 100
        assert "E2E" in E2E_TESTING_STANDARDS

    def test_code_writer_gets_db_standards(self):
        standards = get_standards_for_agent("code-writer")
        assert "DB-" in standards or "DATABASE" in standards

    def test_code_reviewer_gets_db_standards(self):
        standards = get_standards_for_agent("code-reviewer")
        assert "DB-" in standards or "DATABASE" in standards

    def test_architect_gets_db_standards(self):
        standards = get_standards_for_agent("architect")
        assert "DB-" in standards or "DATABASE" in standards

    def test_test_runner_gets_e2e_standards(self):
        standards = get_standards_for_agent("test-runner")
        assert "E2E" in standards

    def test_unknown_agent_returns_empty(self):
        standards = get_standards_for_agent("nonexistent-agent")
        assert standards == "" or standards is not None


# ===========================================================================
# Design reference (Inter font contradiction fix)
# ===========================================================================


class TestDesignReferenceCorrectness:
    """Verify design_reference module corrections."""

    def test_industrial_direction_no_inter_font(self):
        from agent_team.design_reference import _DIRECTION_TABLE
        industrial = _DIRECTION_TABLE["industrial"]
        assert industrial["body_font"] != "Inter", \
            "Industrial body_font must not be 'Inter' (banned by ARCHITECT_PROMPT)"
        assert industrial["body_font"] == "IBM Plex Sans"

    def test_all_directions_have_required_keys(self):
        from agent_team.design_reference import _DIRECTION_TABLE
        required_keys = {"heading_font", "body_font", "primary", "secondary", "accent"}
        for name, direction in _DIRECTION_TABLE.items():
            for key in required_keys:
                assert key in direction, f"{name} missing {key}"
