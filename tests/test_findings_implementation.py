"""Tests for Finding 2 (Context7 Research Enhancement).

Finding 2: Expanded Context7 research queries + per-milestone research injection.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_team.config import (
    AgentTeamConfig,
    TechResearchConfig,
    _dict_to_config,
)
from agent_team.agents import (
    build_milestone_execution_prompt,
    build_orchestrator_prompt,
)
from agent_team.tech_research import (
    TechStackEntry,
    TechResearchResult,
    build_expanded_research_queries,
    build_milestone_research_queries,
    build_research_queries,
    _EXPANDED_QUERY_TEMPLATES,
    _PRD_FEATURE_QUERY_MAP,
    _INTEGRATION_QUERY_TEMPLATES,
)


# ============================================================
# Helpers
# ============================================================

def _default_config(**overrides) -> AgentTeamConfig:
    cfg = AgentTeamConfig()
    for key, val in overrides.items():
        parts = key.split(".")
        obj = cfg
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], val)
    return cfg


def _make_stack(techs: list[tuple[str, str | None, str]]) -> list[TechStackEntry]:
    """Create a tech stack from (name, version, category) tuples."""
    return [
        TechStackEntry(name=n, version=v, category=c, source="test")
        for n, v, c in techs
    ]


# ============================================================
# FINDING 2: Context7 Research Enhancement
# ============================================================

class TestFinding2Config:
    """Test config fields for expanded research queries."""

    def test_default_values(self):
        cfg = AgentTeamConfig()
        assert cfg.tech_research.expanded_queries is True
        assert cfg.tech_research.max_expanded_queries == 4

    def test_yaml_loading(self):
        data = {
            "tech_research": {
                "expanded_queries": False,
                "max_expanded_queries": 6,
            }
        }
        cfg, _ = _dict_to_config(data)
        assert cfg.tech_research.expanded_queries is False
        assert cfg.tech_research.max_expanded_queries == 6

    def test_max_expanded_validation_negative(self):
        data = {"tech_research": {"max_expanded_queries": -1}}
        with pytest.raises(ValueError, match="max_expanded_queries"):
            _dict_to_config(data)

    def test_max_expanded_validation_zero_is_valid(self):
        data = {"tech_research": {"max_expanded_queries": 0}}
        cfg, _ = _dict_to_config(data)
        assert cfg.tech_research.max_expanded_queries == 0


class TestBuildExpandedResearchQueries:
    """Test build_expanded_research_queries function."""

    def test_basic_best_practice_queries(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=4)
        assert len(queries) > 0
        lib_names = [q[0] for q in queries]
        assert all(n == "React" for n in lib_names)

    def test_queries_contain_best_practices(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=4)
        query_texts = [q[1] for q in queries]
        assert any("best practices" in qt.lower() for qt in query_texts)

    def test_queries_contain_anti_patterns(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=4)
        query_texts = [q[1] for q in queries]
        assert any("anti-pattern" in qt.lower() for qt in query_texts)

    def test_prd_aware_queries_auth(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        prd = "This app needs JWT authentication and role-based access control."
        queries = build_expanded_research_queries(stack, prd_text=prd, max_expanded_per_tech=8)
        query_texts = [q[1] for q in queries]
        assert any("auth" in qt.lower() for qt in query_texts)

    def test_prd_aware_queries_file_upload(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        prd = "Users can file upload documents and images."
        queries = build_expanded_research_queries(stack, prd_text=prd, max_expanded_per_tech=8)
        query_texts = [q[1] for q in queries]
        assert any("upload" in qt.lower() for qt in query_texts)

    def test_prd_aware_queries_no_match(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        prd = "A simple static site."
        queries = build_expanded_research_queries(stack, prd_text=prd, max_expanded_per_tech=4)
        # Should still have basic best-practice queries
        assert len(queries) > 0

    def test_max_expanded_cap(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        prd = "authentication file upload real-time websocket email export excel pdf"
        queries = build_expanded_research_queries(stack, prd_text=prd, max_expanded_per_tech=2)
        react_queries = [q for q in queries if q[0] == "React"]
        assert len(react_queries) <= 2

    def test_multiple_techs(self):
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Express", "4.18.0", "backend_framework"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        react_queries = [q for q in queries if q[0] == "React"]
        express_queries = [q for q in queries if q[0] == "Express"]
        assert len(react_queries) > 0
        assert len(express_queries) > 0

    def test_cross_tech_integration_queries(self):
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Express", "4.18.0", "backend_framework"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        query_texts = [q[1] for q in queries]
        # Should have integration queries mentioning both techs
        assert any("React" in qt and "Express" in qt for qt in query_texts)

    def test_cross_tech_orm_backend(self):
        stack = _make_stack([
            ("ASP.NET Core", "8.0", "backend_framework"),
            ("Prisma", "5.0", "orm"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        query_texts = [q[1] for q in queries]
        assert any("Prisma" in qt for qt in query_texts)

    def test_cross_tech_frontend_ui(self):
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Tailwind CSS", "3.4.0", "ui_library"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        query_texts = [q[1] for q in queries]
        assert any("Tailwind" in qt for qt in query_texts)

    def test_empty_stack_returns_empty(self):
        queries = build_expanded_research_queries([], max_expanded_per_tech=4)
        assert queries == []

    def test_version_in_queries(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=4)
        query_texts = [q[1] for q in queries]
        assert any("v18.2.0" in qt for qt in query_texts)

    def test_no_version_still_works(self):
        stack = _make_stack([("React", None, "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=4)
        assert len(queries) > 0
        # No double spaces
        for _, qt in queries:
            assert "  " not in qt


class TestBuildMilestoneResearchQueries:
    """Test build_milestone_research_queries function."""

    def test_basic_milestone_queries(self):
        stack = _make_stack([
            ("Angular", "17.0", "frontend_framework"),
            ("ASP.NET Core", "8.0", "backend_framework"),
        ])
        queries = build_milestone_research_queries(
            milestone_title="Auth & User Management",
            milestone_requirements="REQ-001: JWT authentication with role-based access",
            tech_stack=stack,
        )
        assert len(queries) > 0

    def test_auth_milestone_gets_auth_queries(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        queries = build_milestone_research_queries(
            milestone_title="Authentication",
            milestone_requirements="REQ-001: JWT auth\nREQ-002: Role permission checks",
            tech_stack=stack,
        )
        query_texts = [q[1] for q in queries]
        assert any("auth" in qt.lower() for qt in query_texts)

    def test_file_upload_milestone(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        queries = build_milestone_research_queries(
            milestone_title="Document Management",
            milestone_requirements="REQ-001: File upload and storage",
            tech_stack=stack,
        )
        query_texts = [q[1] for q in queries]
        assert any("upload" in qt.lower() for qt in query_texts)

    def test_relevant_techs_only(self):
        stack = _make_stack([
            ("Angular", "17.0", "frontend_framework"),
            ("ASP.NET Core", "8.0", "backend_framework"),
            ("Redis", "7.0", "database"),
        ])
        queries = build_milestone_research_queries(
            milestone_title="Frontend Dashboard",
            milestone_requirements="REQ-001: Angular dashboard with charts",
            tech_stack=stack,
        )
        lib_names = {q[0] for q in queries}
        # Angular is mentioned, should be in queries
        assert "Angular" in lib_names

    def test_fallback_to_frameworks_when_no_explicit_mentions(self):
        """When no tech is explicitly named, frameworks are used as fallback
        but queries are only generated if PRD feature keywords match."""
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Express", "4.18.0", "backend_framework"),
            ("PostgreSQL", "15.0", "database"),
        ])
        # Use a keyword from _PRD_FEATURE_QUERY_MAP (e.g. "form") so
        # that the fallback framework techs get queries generated.
        queries = build_milestone_research_queries(
            milestone_title="Data Processing",
            milestone_requirements="REQ-001: Form validation and search filters",
            tech_stack=stack,
        )
        # Frameworks should be in the results via fallback
        lib_names = {q[0] for q in queries}
        assert len(lib_names) > 0
        assert "React" in lib_names or "Express" in lib_names

    def test_empty_inputs_returns_empty(self):
        queries = build_milestone_research_queries(
            milestone_title="",
            milestone_requirements="",
            tech_stack=[],
        )
        assert queries == []

    def test_max_8_queries_per_milestone(self):
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Express", "4.18.0", "backend_framework"),
        ])
        # PRD with many feature keywords to trigger many queries
        reqs = (
            "authentication file upload real-time websocket email "
            "export excel pdf notification search dashboard form table "
            "role permission cache queue"
        )
        queries = build_milestone_research_queries(
            milestone_title="Everything Milestone",
            milestone_requirements=reqs,
            tech_stack=stack,
        )
        assert len(queries) <= 8

    def test_no_duplicate_queries(self):
        stack = _make_stack([("Express", "4.18.0", "backend_framework")])
        queries = build_milestone_research_queries(
            milestone_title="Auth",
            milestone_requirements="authentication auth JWT",
            tech_stack=stack,
        )
        assert len(queries) == len(set(queries))


class TestFinding2MilestonePromptInjection:
    """Test Context7 research injection in milestone execution prompt."""

    def test_context7_section_always_present(self):
        """Context7 live research instructions should always be in milestone prompt."""
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
        )
        assert "[CONTEXT7 RESEARCH DURING EXECUTION]" in prompt

    def test_context7_tool_names_in_prompt(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
        )
        assert "mcp__context7__resolve-library-id" in prompt
        assert "mcp__context7__query-docs" in prompt

    def test_context7_usage_instructions(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
        )
        assert "verify the correct method signature" in prompt
        assert "DO NOT:" in prompt
        assert "Guess at API signatures" in prompt

    def test_milestone_research_content_injection(self):
        cfg = AgentTeamConfig()
        ms_research = "- **React**: React v18.2.0 form handling and validation"
        prompt = build_milestone_execution_prompt(
            task="Build a web app",
            depth="standard",
            config=cfg,
            milestone_research_content=ms_research,
        )
        assert "[MILESTONE-SPECIFIC TECH RESEARCH" in prompt
        assert "TARGETED FOR THIS MILESTONE" in prompt
        assert ms_research in prompt

    def test_milestone_research_empty_not_injected(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app",
            depth="standard",
            config=cfg,
            milestone_research_content="",
        )
        assert "[MILESTONE-SPECIFIC TECH RESEARCH" not in prompt

    def test_both_tech_and_milestone_research(self):
        cfg = AgentTeamConfig()
        tech = "## React\n- Use hooks\n- Avoid class components"
        ms = "- **React**: React v18.2.0 form handling"
        prompt = build_milestone_execution_prompt(
            task="Build a web app",
            depth="standard",
            config=cfg,
            tech_research_content=tech,
            milestone_research_content=ms,
        )
        assert "[TECH STACK BEST PRACTICES" in prompt
        assert "[MILESTONE-SPECIFIC TECH RESEARCH" in prompt
        assert tech in prompt
        assert ms in prompt

    def test_milestone_research_prioritization_note(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app",
            depth="standard",
            config=cfg,
            milestone_research_content="some content",
        )
        assert "Prioritize these patterns over generic research" in prompt


class TestFinding2ExpandedQueryTemplates:
    """Test the expanded query template data structures."""

    def test_expanded_templates_exist(self):
        assert len(_EXPANDED_QUERY_TEMPLATES) > 0

    def test_expanded_templates_have_name_placeholder(self):
        for template in _EXPANDED_QUERY_TEMPLATES:
            assert "{name}" in template

    def test_prd_feature_map_not_empty(self):
        assert len(_PRD_FEATURE_QUERY_MAP) > 0

    def test_prd_feature_map_all_have_name(self):
        for keyword, template in _PRD_FEATURE_QUERY_MAP.items():
            assert "{name}" in template, f"Template for '{keyword}' missing {{name}}"

    def test_integration_templates_not_empty(self):
        assert len(_INTEGRATION_QUERY_TEMPLATES) > 0

    def test_integration_templates_use_frozenset_keys(self):
        for key in _INTEGRATION_QUERY_TEMPLATES:
            assert isinstance(key, frozenset)
            assert len(key) == 2

    def test_key_prd_features_covered(self):
        """Ensure critical features have query templates."""
        important_keywords = ["authentication", "auth", "file upload", "form", "table", "search"]
        for kw in important_keywords:
            assert kw in _PRD_FEATURE_QUERY_MAP, f"Missing PRD feature keyword: {kw}"


class TestFinding2IntegrationQueryGeneration:
    """Test cross-technology integration query generation."""

    def test_frontend_backend_integration(self):
        stack = _make_stack([
            ("Angular", "17.0", "frontend_framework"),
            ("ASP.NET Core", "8.0", "backend_framework"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=1)
        query_texts = [q[1] for q in queries]
        # Should produce CORS or API endpoint queries
        has_integration = any(
            ("Angular" in qt and "ASP.NET" in qt) or "CORS" in qt
            for qt in query_texts
        )
        assert has_integration, f"No integration query found in: {query_texts}"

    def test_backend_orm_integration(self):
        stack = _make_stack([
            ("Express", "4.18.0", "backend_framework"),
            ("Prisma", "5.0", "orm"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=1)
        query_texts = [q[1] for q in queries]
        has_integration = any(
            "Express" in qt and "Prisma" in qt
            for qt in query_texts
        )
        assert has_integration, f"No backend-ORM integration query found in: {query_texts}"

    def test_frontend_ui_integration(self):
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Material UI", "5.14.0", "ui_library"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=1)
        query_texts = [q[1] for q in queries]
        has_integration = any(
            "React" in qt and "Material" in qt
            for qt in query_texts
        )
        assert has_integration, f"No frontend-UI integration query found in: {query_texts}"

    def test_backend_database_integration(self):
        stack = _make_stack([
            ("Express", "4.18.0", "backend_framework"),
            ("PostgreSQL", "15.0", "database"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=1)
        query_texts = [q[1] for q in queries]
        has_integration = any(
            "Express" in qt and "PostgreSQL" in qt
            for qt in query_texts
        )
        assert has_integration, f"No backend-DB integration query found in: {query_texts}"

    def test_no_integration_for_single_tech(self):
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        # Only per-tech queries, no integration queries
        lib_names = {q[0] for q in queries}
        assert lib_names == {"React"}

    def test_missing_category_pair_skipped(self):
        """If only frontend_framework exists, no frontend+backend pair."""
        stack = _make_stack([
            ("React", "18.2.0", "frontend_framework"),
            ("Jest", "29.0", "testing"),
        ])
        queries = build_expanded_research_queries(stack, max_expanded_per_tech=2)
        query_texts = [q[1] for q in queries]
        # No cross-tech integration queries should appear
        has_cross_tech = any(
            "React" in qt and "Jest" in qt
            for qt in query_texts
        )
        assert not has_cross_tech


class TestFinding2CliWiring:
    """Test that per-milestone research is wired in cli.py."""

    def test_build_milestone_research_queries_import_in_cli(self):
        """Verify build_milestone_research_queries is imported/used in cli.py."""
        import ast
        cli_path = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
        content = cli_path.read_text(encoding="utf-8")
        assert "build_milestone_research_queries" in content

    def test_milestone_research_content_passed_to_prompt(self):
        """Verify milestone_research_content is passed to build_milestone_execution_prompt."""
        cli_path = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
        content = cli_path.read_text(encoding="utf-8")
        assert "milestone_research_content=ms_research_content" in content

    def test_detected_tech_stack_variable_exists(self):
        """Verify _detected_tech_stack is initialized in _run_prd_milestones."""
        cli_path = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
        content = cli_path.read_text(encoding="utf-8")
        assert "_detected_tech_stack" in content
        assert "_detected_tech_stack: list = []" in content

    def test_expanded_queries_config_check_in_cli(self):
        """Verify config.tech_research.expanded_queries is checked in cli.py."""
        cli_path = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
        content = cli_path.read_text(encoding="utf-8")
        assert "config.tech_research.expanded_queries" in content



# ============================================================
# CROSS-FINDING: No regressions in existing features
# ============================================================

class TestNoRegressionExistingPrompts:
    """Verify existing prompt features still work with findings changes."""

    def test_orchestrator_prompt_still_has_review_warning(self):
        cfg = AgentTeamConfig()
        prompt = build_orchestrator_prompt(
            task="Build a web app", depth="standard", config=cfg,
        )
        assert "100% convergence ratios" in prompt

    def test_milestone_prompt_still_has_convergence_markers(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
        )
        assert "convergence health checks" in prompt

    def test_milestone_prompt_still_accepts_tech_research_content(self):
        cfg = AgentTeamConfig()
        tech = "## React\n- Use hooks"
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
            tech_research_content=tech,
        )
        assert tech in prompt
        assert "[TECH STACK BEST PRACTICES" in prompt

    def test_milestone_prompt_still_accepts_ui_requirements(self):
        cfg = AgentTeamConfig()
        ui = "Use Inter font, blue primary color"
        prompt = build_milestone_execution_prompt(
            task="Build a web app", depth="standard", config=cfg,
            ui_requirements_content=ui,
        )
        # UI content should appear somewhere in the prompt
        assert ui in prompt or "DESIGN REFERENCE" in prompt


class TestNoRegressionExistingConfig:
    """Verify existing config features survive the findings changes."""

    def test_existing_milestone_fields_preserved(self):
        cfg = AgentTeamConfig()
        assert hasattr(cfg.milestone, "review_recovery_retries")
        assert hasattr(cfg.milestone, "mock_data_scan")
        assert hasattr(cfg.milestone, "ui_compliance_scan")
        assert hasattr(cfg.milestone, "resume_from_milestone")

    def test_existing_tech_research_fields_preserved(self):
        cfg = AgentTeamConfig()
        assert hasattr(cfg.tech_research, "enabled")
        assert hasattr(cfg.tech_research, "max_techs")
        assert hasattr(cfg.tech_research, "max_queries_per_tech")
        assert hasattr(cfg.tech_research, "retry_on_incomplete")
        assert hasattr(cfg.tech_research, "injection_max_chars")

    def test_dict_to_config_returns_tuple(self):
        """Verify _dict_to_config still returns (config, overrides) tuple."""
        result = _dict_to_config({})
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], AgentTeamConfig)
        assert isinstance(result[1], set)

    def test_build_research_queries_still_works(self):
        """Verify original build_research_queries is unchanged."""
        stack = _make_stack([("React", "18.2.0", "frontend_framework")])
        queries = build_research_queries(stack, max_per_tech=2)
        assert len(queries) == 2
        assert all(q[0] == "React" for q in queries)
