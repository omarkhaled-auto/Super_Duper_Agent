"""Tests for agent_team.code_quality_standards."""

from __future__ import annotations

from agent_team.code_quality_standards import (
    ARCHITECTURE_QUALITY_STANDARDS,
    BACKEND_STANDARDS,
    CODE_REVIEW_STANDARDS,
    DEBUGGING_STANDARDS,
    FRONTEND_STANDARDS,
    TESTING_STANDARDS,
    get_standards_for_agent,
)


# ===================================================================
# Frontend Standards
# ===================================================================

class TestFrontendStandards:
    def test_content_length(self):
        assert len(FRONTEND_STANDARDS) > 1000

    def test_has_all_anti_patterns(self):
        for i in range(1, 16):
            code = f"FRONT-{i:03d}"
            assert code in FRONTEND_STANDARDS, f"Missing {code}"

    def test_has_state_management_section(self):
        assert "State Management" in FRONTEND_STANDARDS

    def test_has_typescript_section(self):
        assert "TypeScript" in FRONTEND_STANDARDS

    def test_has_performance_section(self):
        assert "Performance" in FRONTEND_STANDARDS

    def test_has_accessibility_section(self):
        assert "Accessibility" in FRONTEND_STANDARDS

    def test_has_tutorial_warning(self):
        assert "tutorial" in FRONTEND_STANDARDS.lower()


# ===================================================================
# Backend Standards
# ===================================================================

class TestBackendStandards:
    def test_content_length(self):
        assert len(BACKEND_STANDARDS) > 1000

    def test_has_all_anti_patterns(self):
        for i in range(1, 16):
            code = f"BACK-{i:03d}"
            assert code in BACKEND_STANDARDS, f"Missing {code}"

    def test_has_api_design_section(self):
        assert "API Design" in BACKEND_STANDARDS

    def test_has_error_handling_section(self):
        assert "Error Handling" in BACKEND_STANDARDS

    def test_has_security_owasp_section(self):
        assert "Security" in BACKEND_STANDARDS
        assert "OWASP" in BACKEND_STANDARDS

    def test_has_database_section(self):
        assert "Database" in BACKEND_STANDARDS

    def test_references_n_plus_1_and_injection(self):
        assert "N+1" in BACKEND_STANDARDS
        assert "Injection" in BACKEND_STANDARDS or "injection" in BACKEND_STANDARDS


# ===================================================================
# Code Review Standards
# ===================================================================

class TestCodeReviewStandards:
    def test_content_length(self):
        assert len(CODE_REVIEW_STANDARDS) > 1000

    def test_has_all_anti_patterns(self):
        for i in range(1, 16):
            code = f"REVIEW-{i:03d}"
            assert code in CODE_REVIEW_STANDARDS, f"Missing {code}"

    def test_has_priority_sequence(self):
        text = CODE_REVIEW_STANDARDS
        sec_pos = text.index("SECURITY")
        cor_pos = text.index("CORRECTNESS")
        perf_pos = text.index("PERFORMANCE")
        assert sec_pos < cor_pos < perf_pos

    def test_has_severity_framework(self):
        assert "CRITICAL" in CODE_REVIEW_STANDARDS
        assert "HIGH" in CODE_REVIEW_STANDARDS
        assert "MEDIUM" in CODE_REVIEW_STANDARDS
        assert "LOW" in CODE_REVIEW_STANDARDS

    def test_has_hallucinated_api_reference(self):
        assert "Hallucinated" in CODE_REVIEW_STANDARDS


# ===================================================================
# Testing Standards
# ===================================================================

class TestTestingStandards:
    def test_content_length(self):
        assert len(TESTING_STANDARDS) > 1000

    def test_has_all_anti_patterns(self):
        for i in range(1, 16):
            code = f"TEST-{i:03d}"
            assert code in TESTING_STANDARDS, f"Missing {code}"

    def test_has_arrange_act_assert(self):
        assert "Arrange" in TESTING_STANDARDS
        assert "Act" in TESTING_STANDARDS
        assert "Assert" in TESTING_STANDARDS

    def test_has_test_structure_section(self):
        assert "Test Structure" in TESTING_STANDARDS

    def test_has_mocking_guidance(self):
        assert "Mocking" in TESTING_STANDARDS or "Mock" in TESTING_STANDARDS


# ===================================================================
# Debugging Standards
# ===================================================================

class TestDebuggingStandards:
    def test_content_length(self):
        assert len(DEBUGGING_STANDARDS) > 1000

    def test_has_all_anti_patterns(self):
        for i in range(1, 11):
            code = f"DEBUG-{i:03d}"
            assert code in DEBUGGING_STANDARDS, f"Missing {code}"

    def test_has_reproduce_methodology(self):
        assert "Reproduce" in DEBUGGING_STANDARDS

    def test_has_regression_test_requirement(self):
        assert "regression" in DEBUGGING_STANDARDS.lower()


# ===================================================================
# Architecture Quality Standards
# ===================================================================

class TestArchitectureQualityStandards:
    def test_content_length(self):
        assert len(ARCHITECTURE_QUALITY_STANDARDS) > 500

    def test_has_dependency_flow_direction(self):
        assert "Dependency" in ARCHITECTURE_QUALITY_STANDARDS
        assert "ONE direction" in ARCHITECTURE_QUALITY_STANDARDS

    def test_has_error_handling_architecture(self):
        assert "Error Handling" in ARCHITECTURE_QUALITY_STANDARDS


# ===================================================================
# get_standards_for_agent()
# ===================================================================

class TestGetStandardsForAgent:
    def test_code_writer_gets_frontend_and_backend(self):
        result = get_standards_for_agent("code-writer")
        assert "FRONT-001" in result
        assert "BACK-001" in result

    def test_code_reviewer_gets_review_standards(self):
        result = get_standards_for_agent("code-reviewer")
        assert "REVIEW-001" in result

    def test_test_runner_gets_testing_standards(self):
        result = get_standards_for_agent("test-runner")
        assert "TEST-001" in result

    def test_debugger_gets_debugging_standards(self):
        result = get_standards_for_agent("debugger")
        assert "DEBUG-001" in result

    def test_architect_gets_architecture_quality(self):
        result = get_standards_for_agent("architect")
        assert "ARCHITECTURE QUALITY" in result

    def test_unknown_agent_returns_empty(self):
        assert get_standards_for_agent("unknown-agent") == ""

    def test_planner_returns_empty(self):
        assert get_standards_for_agent("planner") == ""

    def test_researcher_returns_empty(self):
        assert get_standards_for_agent("researcher") == ""

    def test_task_assigner_returns_empty(self):
        assert get_standards_for_agent("task-assigner") == ""

    def test_security_auditor_returns_empty(self):
        assert get_standards_for_agent("security-auditor") == ""


# ===================================================================
# Edge cases
# ===================================================================

class TestEdgeCases:
    """Edge case tests for code quality standards module."""

    def test_empty_string_agent_returns_empty(self):
        assert get_standards_for_agent("") == ""

    def test_case_sensitive_agent_name(self):
        """Agent names are case-sensitive — uppercase should return empty."""
        assert get_standards_for_agent("CODE-WRITER") == ""
        assert get_standards_for_agent("PLANNER") == ""

    def test_underscore_agent_name_returns_empty(self):
        """Config uses underscores, but SDK names use hyphens."""
        assert get_standards_for_agent("code_writer") == ""

    def test_code_writer_has_both_standards_separated(self):
        """code-writer gets FRONTEND and BACKEND separated by double newline."""
        result = get_standards_for_agent("code-writer")
        assert "FRONTEND CODE QUALITY" in result
        assert "BACKEND CODE QUALITY" in result
        # Verify separation
        front_end = result.index("FRONTEND")
        back_end = result.index("BACKEND")
        between = result[front_end:back_end]
        assert "\n\n" in between

    def test_all_constants_are_non_empty(self):
        from agent_team.code_quality_standards import (
            FRONTEND_STANDARDS, BACKEND_STANDARDS,
            CODE_REVIEW_STANDARDS, TESTING_STANDARDS,
            DEBUGGING_STANDARDS, ARCHITECTURE_QUALITY_STANDARDS,
        )
        for name, const in [
            ("FRONTEND", FRONTEND_STANDARDS),
            ("BACKEND", BACKEND_STANDARDS),
            ("REVIEW", CODE_REVIEW_STANDARDS),
            ("TESTING", TESTING_STANDARDS),
            ("DEBUGGING", DEBUGGING_STANDARDS),
            ("ARCHITECTURE", ARCHITECTURE_QUALITY_STANDARDS),
        ]:
            assert len(const) > 0, f"{name} is empty"
            assert const == const.strip(), f"{name} has leading/trailing whitespace"

    def test_all_constants_start_with_markdown_header(self):
        from agent_team.code_quality_standards import (
            FRONTEND_STANDARDS, BACKEND_STANDARDS,
            CODE_REVIEW_STANDARDS, TESTING_STANDARDS,
            DEBUGGING_STANDARDS, ARCHITECTURE_QUALITY_STANDARDS,
        )
        for name, const in [
            ("FRONTEND", FRONTEND_STANDARDS),
            ("BACKEND", BACKEND_STANDARDS),
            ("REVIEW", CODE_REVIEW_STANDARDS),
            ("TESTING", TESTING_STANDARDS),
            ("DEBUGGING", DEBUGGING_STANDARDS),
            ("ARCHITECTURE", ARCHITECTURE_QUALITY_STANDARDS),
        ]:
            assert const.startswith("##"), f"{name} doesn't start with markdown header"

    def test_standards_map_has_exactly_five_agents(self):
        from agent_team.code_quality_standards import _AGENT_STANDARDS_MAP
        assert len(_AGENT_STANDARDS_MAP) == 5
        expected = {"code-writer", "code-reviewer", "test-runner", "debugger", "architect"}
        assert set(_AGENT_STANDARDS_MAP.keys()) == expected

    def test_each_mapped_agent_returns_non_empty(self):
        for agent in ["code-writer", "code-reviewer", "test-runner", "debugger", "architect"]:
            result = get_standards_for_agent(agent)
            assert len(result) > 100, f"{agent} standards too short"
