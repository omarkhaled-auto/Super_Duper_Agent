"""Tests for agent_team.sequential_thinking."""

from __future__ import annotations

import pytest

from agent_team.config import InvestigationConfig
from agent_team.sequential_thinking import (
    _ST_AGENT_PROFILES,
    _ST_HYPOTHESIS_LOOP,
    _ST_METHODOLOGY_BASE,
    _ST_REVISION_SUPPORT,
    build_sequential_thinking_protocol,
)


# ===================================================================
# Template string sanity checks
# ===================================================================

class TestTemplateStrings:
    def test_methodology_base_non_empty(self):
        assert len(_ST_METHODOLOGY_BASE) > 100

    def test_methodology_base_has_thought_format(self):
        assert "THOUGHT [N/" in _ST_METHODOLOGY_BASE

    def test_methodology_base_has_complexity_guidance(self):
        assert "Single-file" in _ST_METHODOLOGY_BASE or "single-file" in _ST_METHODOLOGY_BASE
        assert "Multi-file" in _ST_METHODOLOGY_BASE or "multi-file" in _ST_METHODOLOGY_BASE

    def test_methodology_base_has_max_thoughts_placeholder(self):
        assert "{max_thoughts}" in _ST_METHODOLOGY_BASE

    def test_methodology_base_requires_file_line_refs(self):
        assert "file:line" in _ST_METHODOLOGY_BASE

    def test_hypothesis_loop_non_empty(self):
        assert len(_ST_HYPOTHESIS_LOOP) > 100

    def test_hypothesis_loop_has_format(self):
        assert "HYPOTHESIS [H-N]" in _ST_HYPOTHESIS_LOOP

    def test_hypothesis_loop_has_verdict(self):
        assert "VERDICT:" in _ST_HYPOTHESIS_LOOP
        assert "CONFIRMED" in _ST_HYPOTHESIS_LOOP
        assert "REFUTED" in _ST_HYPOTHESIS_LOOP
        assert "INCONCLUSIVE" in _ST_HYPOTHESIS_LOOP

    def test_revision_support_non_empty(self):
        assert len(_ST_REVISION_SUPPORT) > 100

    def test_revision_support_has_revision_format(self):
        assert "REVISION [revising Thought N]" in _ST_REVISION_SUPPORT

    def test_revision_support_has_confidence_levels(self):
        assert "HIGH" in _ST_REVISION_SUPPORT
        assert "MEDIUM" in _ST_REVISION_SUPPORT
        assert "LOW" in _ST_REVISION_SUPPORT

    def test_agent_profiles_has_reviewer(self):
        assert "code-reviewer" in _ST_AGENT_PROFILES

    def test_agent_profiles_has_security(self):
        assert "security-auditor" in _ST_AGENT_PROFILES

    def test_agent_profiles_has_debugger(self):
        assert "debugger" in _ST_AGENT_PROFILES

    def test_agent_profiles_all_non_empty(self):
        for name, profile in _ST_AGENT_PROFILES.items():
            assert len(profile) > 50, f"{name} profile is too short"

    def test_agent_profiles_have_thought_estimates(self):
        for name, profile in _ST_AGENT_PROFILES.items():
            assert "thoughts" in profile.lower(), f"{name} profile missing thought estimates"

    def test_agent_profiles_have_hypothesis_patterns(self):
        for name, profile in _ST_AGENT_PROFILES.items():
            assert "hypothesis" in profile.lower() or "Hypothesis" in profile, \
                f"{name} profile missing hypothesis patterns"


# ===================================================================
# build_sequential_thinking_protocol() — basic behavior
# ===================================================================

class TestBuildProtocol:
    def test_returns_empty_when_disabled(self):
        config = InvestigationConfig(sequential_thinking=False)
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert result == ""

    def test_returns_empty_for_unlisted_agent(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("planner", config)
        assert result == ""

    def test_returns_empty_for_code_writer(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-writer", config)
        assert result == ""

    def test_returns_protocol_for_code_reviewer(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert len(result) > 100
        assert "SEQUENTIAL THINKING METHODOLOGY" in result

    def test_returns_protocol_for_security_auditor(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("security-auditor", config)
        assert len(result) > 100
        assert "SEQUENTIAL THINKING METHODOLOGY" in result

    def test_returns_protocol_for_debugger(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("debugger", config)
        assert len(result) > 100
        assert "SEQUENTIAL THINKING METHODOLOGY" in result

    def test_all_default_agents_get_protocol(self):
        config = InvestigationConfig()
        for agent in ["code-reviewer", "security-auditor", "debugger"]:
            result = build_sequential_thinking_protocol(agent, config)
            assert len(result) > 100, f"{agent} should get ST protocol"


# ===================================================================
# Thought budget (max_thoughts_per_item)
# ===================================================================

class TestThoughtBudget:
    def test_default_budget_in_protocol(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "15" in result  # default max_thoughts_per_item

    def test_custom_budget_in_protocol(self):
        config = InvestigationConfig(max_thoughts_per_item=10)
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "10" in result

    def test_minimum_budget_accepted(self):
        config = InvestigationConfig(max_thoughts_per_item=3)
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "SEQUENTIAL THINKING" in result


# ===================================================================
# Hypothesis loop inclusion/exclusion
# ===================================================================

class TestHypothesisLoop:
    def test_hypothesis_included_by_default(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "HYPOTHESIS [H-N]" in result
        assert "VERDICT:" in result

    def test_hypothesis_excluded_when_disabled(self):
        config = InvestigationConfig(enable_hypothesis_loop=False)
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "HYPOTHESIS [H-N]" not in result
        assert "VERDICT:" not in result

    def test_revision_always_included(self):
        config = InvestigationConfig(enable_hypothesis_loop=False)
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "REVISION" in result
        assert "Confidence" in result


# ===================================================================
# Per-agent profile content
# ===================================================================

class TestPerAgentProfiles:
    def test_reviewer_has_req_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "REQ-xxx" in result

    def test_reviewer_has_wire_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        assert "WIRE-xxx" in result

    def test_security_has_input_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("security-auditor", config)
        assert "Input validation" in result or "input" in result.lower()

    def test_security_has_auth_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("security-auditor", config)
        assert "Auth" in result

    def test_debugger_has_single_file_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("debugger", config)
        assert "Single-file" in result

    def test_debugger_has_root_cause_estimates(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("debugger", config)
        assert "Root cause" in result


# ===================================================================
# Custom agents list
# ===================================================================

class TestCustomAgentsList:
    def test_custom_agents_list(self):
        config = InvestigationConfig(agents=["debugger"])
        assert build_sequential_thinking_protocol("debugger", config) != ""
        assert build_sequential_thinking_protocol("code-reviewer", config) == ""

    def test_empty_agents_list(self):
        config = InvestigationConfig(agents=[])
        assert build_sequential_thinking_protocol("code-reviewer", config) == ""
        assert build_sequential_thinking_protocol("debugger", config) == ""


# ===================================================================
# Prompt composition snapshot
# ===================================================================

class TestPromptComposition:
    def test_full_protocol_contains_all_sections(self):
        """Verify the composed prompt has all expected sections in order."""
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("code-reviewer", config)
        # All sections must appear
        assert "SEQUENTIAL THINKING METHODOLOGY" in result
        assert "Hypothesis-Verification Cycle" in result
        assert "Revision and Confidence" in result
        assert "Thought Estimates: Code Review" in result
        # Sections must appear in correct order
        methodology_idx = result.index("SEQUENTIAL THINKING METHODOLOGY")
        hypothesis_idx = result.index("Hypothesis-Verification Cycle")
        revision_idx = result.index("Revision and Confidence")
        profile_idx = result.index("Thought Estimates: Code Review")
        assert methodology_idx < hypothesis_idx < revision_idx < profile_idx

    def test_debugger_protocol_sections_in_order(self):
        config = InvestigationConfig()
        result = build_sequential_thinking_protocol("debugger", config)
        methodology_idx = result.index("SEQUENTIAL THINKING METHODOLOGY")
        revision_idx = result.index("Revision and Confidence")
        profile_idx = result.index("Thought Estimates: Debugging")
        assert methodology_idx < revision_idx < profile_idx
