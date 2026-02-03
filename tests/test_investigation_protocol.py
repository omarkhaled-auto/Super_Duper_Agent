"""Tests for agent_team.investigation_protocol."""

from __future__ import annotations

import pytest

from agent_team.config import InvestigationConfig
from agent_team.investigation_protocol import (
    _AGENT_FOCUS,
    _BASE_PROTOCOL,
    _GEMINI_CLI_SECTION,
    _REVIEWER_BASH_SCOPING,
    build_investigation_protocol,
)


# ===================================================================
# Template string sanity checks
# ===================================================================

class TestTemplateStrings:
    def test_base_protocol_non_empty(self):
        assert len(_BASE_PROTOCOL) > 100

    def test_base_protocol_has_phases(self):
        assert "Phase 1: SCOPE" in _BASE_PROTOCOL
        assert "Phase 2: INVESTIGATE" in _BASE_PROTOCOL
        assert "Phase 3: SYNTHESIZE" in _BASE_PROTOCOL
        assert "Phase 4: EVIDENCE" in _BASE_PROTOCOL

    def test_base_protocol_has_escalation_rule(self):
        assert "DYNAMIC ESCALATION" in _BASE_PROTOCOL

    def test_gemini_section_non_empty(self):
        assert len(_GEMINI_CLI_SECTION) > 100

    def test_gemini_section_has_syntax(self):
        assert "gemini" in _GEMINI_CLI_SECTION
        assert "--include-directories" in _GEMINI_CLI_SECTION

    def test_reviewer_bash_scoping_non_empty(self):
        assert len(_REVIEWER_BASH_SCOPING) > 50

    def test_reviewer_bash_scoping_prohibits_tests(self):
        assert "PROHIBITED" in _REVIEWER_BASH_SCOPING

    def test_agent_focus_has_reviewer(self):
        assert "code-reviewer" in _AGENT_FOCUS

    def test_agent_focus_has_security(self):
        assert "security-auditor" in _AGENT_FOCUS

    def test_agent_focus_has_debugger(self):
        assert "debugger" in _AGENT_FOCUS

    def test_agent_focus_all_non_empty(self):
        for name, focus in _AGENT_FOCUS.items():
            assert len(focus) > 50, f"{name} focus is too short"


# ===================================================================
# build_investigation_protocol() — basic behavior
# ===================================================================

class TestBuildInvestigationProtocol:
    def test_returns_empty_for_unlisted_agent(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("planner", config, gemini_available=False)
        assert result == ""

    def test_returns_empty_for_code_writer(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-writer", config, gemini_available=False)
        assert result == ""

    def test_returns_protocol_for_code_reviewer(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config, gemini_available=False)
        assert len(result) > 100
        assert "DEEP INVESTIGATION PROTOCOL" in result

    def test_returns_protocol_for_security_auditor(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("security-auditor", config, gemini_available=False)
        assert len(result) > 100
        assert "DEEP INVESTIGATION PROTOCOL" in result

    def test_returns_protocol_for_debugger(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("debugger", config, gemini_available=False)
        assert len(result) > 100
        assert "DEEP INVESTIGATION PROTOCOL" in result


# ===================================================================
# Gemini section inclusion/exclusion
# ===================================================================

class TestGeminiSection:
    def test_gemini_section_included_when_available(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config, gemini_available=True)
        assert "Gemini CLI" in result
        assert "--include-directories" in result

    def test_gemini_section_excluded_when_unavailable(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config, gemini_available=False)
        assert "Gemini CLI" not in result
        assert "--include-directories" not in result

    def test_gemini_section_for_debugger(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("debugger", config, gemini_available=True)
        assert "Gemini CLI" in result

    def test_gemini_section_for_security_auditor(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("security-auditor", config, gemini_available=True)
        assert "Gemini CLI" in result


# ===================================================================
# Bash scoping rules
# ===================================================================

class TestBashScoping:
    def test_bash_scoping_only_for_reviewer_with_gemini(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config, gemini_available=True)
        assert "Bash Scoping Rules" in result
        assert "PROHIBITED" in result

    def test_no_bash_scoping_for_reviewer_without_gemini(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config, gemini_available=False)
        assert "Bash Scoping Rules" not in result

    def test_no_bash_scoping_for_debugger(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("debugger", config, gemini_available=True)
        assert "Bash Scoping Rules" not in result

    def test_no_bash_scoping_for_security_auditor(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("security-auditor", config, gemini_available=True)
        assert "Bash Scoping Rules" not in result


# ===================================================================
# Query budget (max_queries_per_agent)
# ===================================================================

class TestQueryBudget:
    def test_default_budget_in_protocol(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config)
        assert "8" in result  # default max_queries_per_agent

    def test_custom_budget_in_protocol(self):
        config = InvestigationConfig(max_queries_per_agent=5)
        result = build_investigation_protocol("code-reviewer", config)
        assert "5" in result

    def test_budget_in_gemini_section(self):
        config = InvestigationConfig(max_queries_per_agent=3)
        result = build_investigation_protocol("code-reviewer", config, gemini_available=True)
        assert "3 queries max" in result or "3 Gemini queries" in result


# ===================================================================
# Model flag
# ===================================================================

class TestModelFlag:
    def test_model_flag_included_when_set(self):
        config = InvestigationConfig(gemini_model="gemini-2.5-pro")
        result = build_investigation_protocol("code-reviewer", config, gemini_available=True)
        assert "-m gemini-2.5-pro" in result

    def test_model_flag_absent_when_empty(self):
        config = InvestigationConfig(gemini_model="")
        result = build_investigation_protocol("code-reviewer", config, gemini_available=True)
        assert "-m " not in result

    def test_model_flag_not_in_base_protocol(self):
        config = InvestigationConfig(gemini_model="gemini-2.5-pro")
        result = build_investigation_protocol("code-reviewer", config, gemini_available=False)
        assert "-m gemini-2.5-pro" not in result  # no Gemini section → no model flag


# ===================================================================
# Custom agents list
# ===================================================================

class TestCustomAgentsList:
    def test_custom_agents_list(self):
        config = InvestigationConfig(agents=["debugger"])
        assert build_investigation_protocol("debugger", config) != ""
        assert build_investigation_protocol("code-reviewer", config) == ""
        assert build_investigation_protocol("security-auditor", config) == ""

    def test_empty_agents_list(self):
        config = InvestigationConfig(agents=[])
        assert build_investigation_protocol("code-reviewer", config) == ""
        assert build_investigation_protocol("debugger", config) == ""

    def test_all_default_agents_get_protocol(self):
        config = InvestigationConfig()
        for agent in ["code-reviewer", "security-auditor", "debugger"]:
            result = build_investigation_protocol(agent, config)
            assert len(result) > 100, f"{agent} should get protocol"


# ===================================================================
# Per-agent focus content
# ===================================================================

class TestPerAgentFocus:
    def test_reviewer_has_data_flow_focus(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config)
        assert "data flow" in result.lower() or "Trace data flow" in result

    def test_reviewer_has_wiring_focus(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("code-reviewer", config)
        assert "wiring" in result.lower() or "WIRE-xxx" in result

    def test_security_has_input_path_focus(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("security-auditor", config)
        assert "input" in result.lower()

    def test_security_has_auth_flow_focus(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("security-auditor", config)
        assert "auth" in result.lower()

    def test_debugger_has_root_cause_focus(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("debugger", config)
        assert "root cause" in result.lower() or "Root cause" in result

    def test_debugger_has_variable_tracing(self):
        config = InvestigationConfig()
        result = build_investigation_protocol("debugger", config)
        assert "variable" in result.lower() or "trace" in result.lower()
