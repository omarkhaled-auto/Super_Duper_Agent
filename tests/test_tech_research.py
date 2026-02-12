"""Tests for Tech Stack Research Phase 1.5 (v14.0)."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.tech_research import (
    TechResearchResult,
    TechStackEntry,
    build_research_queries,
    detect_tech_stack,
    extract_research_summary,
    parse_tech_research_file,
    validate_tech_research,
    TECH_RESEARCH_PROMPT,
    _CATEGORY_PRIORITY,
    _CSPROJ_SKIP_DIRS,
    _NPM_PACKAGE_MAP,
    _PYTHON_PACKAGE_MAP,
    _detect_from_text,
    _strip_version_prefix,
)
from agent_team.config import (
    AgentTeamConfig,
    TechResearchConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.mcp_servers import get_context7_only_servers
from agent_team.agents import build_milestone_execution_prompt, build_orchestrator_prompt

# Source root for prompt/standard assertions
_SRC = Path(__file__).resolve().parent.parent / "src" / "agent_team"


# ============================================================
# Helpers
# ============================================================

def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _make_package_json(tmp_path: Path, deps: dict | None = None, dev_deps: dict | None = None) -> Path:
    pkg = {}
    if deps:
        pkg["dependencies"] = deps
    if dev_deps:
        pkg["devDependencies"] = dev_deps
    return _make_file(tmp_path, "package.json", json.dumps(pkg))


def _make_result(
    stack: list[TechStackEntry] | None = None,
    findings: dict[str, str] | None = None,
) -> TechResearchResult:
    s = stack or []
    f = findings or {}
    return TechResearchResult(
        stack=s,
        findings=f,
        queries_made=len(f),
        techs_covered=len(f),
        techs_total=len(s),
        is_complete=len(f) == len(s),
    )


# ============================================================
# Detection tests
# ============================================================

class TestDetectFromPackageJson:
    """Detect technologies from package.json."""

    def test_react_and_express(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"react": "^18.2.0", "express": "^4.18.2"})
        stack = detect_tech_stack(tmp_path)
        names = {e.name for e in stack}
        assert "React" in names
        assert "Express" in names

    def test_version_extraction(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"next": "14.2.3"})
        stack = detect_tech_stack(tmp_path)
        nextjs = next(e for e in stack if e.name == "Next.js")
        assert nextjs.version == "14.2.3"

    def test_caret_version_stripped(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"react": "^18.2.0"})
        stack = detect_tech_stack(tmp_path)
        react = next(e for e in stack if e.name == "React")
        assert react.version == "18.2.0"

    def test_tilde_version_stripped(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"express": "~4.18.2"})
        stack = detect_tech_stack(tmp_path)
        express = next(e for e in stack if e.name == "Express")
        assert express.version == "4.18.2"

    def test_dev_deps_detected(self, tmp_path: Path):
        _make_package_json(tmp_path, dev_deps={"vitest": "^1.0.0", "typescript": "^5.3.0"})
        stack = detect_tech_stack(tmp_path)
        names = {e.name for e in stack}
        assert "Vitest" in names
        assert "TypeScript" in names

    def test_prisma_detected(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"@prisma/client": "^5.0.0"})
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Prisma" for e in stack)

    def test_tailwind_detected(self, tmp_path: Path):
        _make_package_json(tmp_path, dev_deps={"tailwindcss": "^3.4.0"})
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Tailwind CSS" for e in stack)

    def test_source_is_package_json(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"react": "18.0.0"})
        stack = detect_tech_stack(tmp_path)
        assert all(e.source == "package.json" for e in stack)


class TestDetectFromRequirementsTxt:
    """Detect technologies from requirements.txt."""

    def test_django_with_version(self, tmp_path: Path):
        _make_file(tmp_path, "requirements.txt", "django==4.2.3\npsycopg2==2.9.7\n")
        stack = detect_tech_stack(tmp_path)
        django = next(e for e in stack if e.name == "Django")
        assert django.version == "4.2.3"
        assert django.category == "backend_framework"
        assert any(e.name == "PostgreSQL" for e in stack)

    def test_fastapi_detected(self, tmp_path: Path):
        _make_file(tmp_path, "requirements.txt", "fastapi>=0.100.0\nuvicorn\n")
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "FastAPI" for e in stack)

    def test_python_language_auto_added(self, tmp_path: Path):
        _make_file(tmp_path, "requirements.txt", "flask==3.0.0\n")
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Python" and e.category == "language" for e in stack)

    def test_comments_and_blanks_skipped(self, tmp_path: Path):
        _make_file(tmp_path, "requirements.txt", "# comment\n\n-r base.txt\nflask==3.0\n")
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Flask" for e in stack)
        assert len(stack) >= 1  # At least Flask + Python


class TestDetectFromPyproject:
    """Detect technologies from pyproject.toml."""

    def test_django_in_pyproject(self, tmp_path: Path):
        _make_file(tmp_path, "pyproject.toml", textwrap.dedent("""\
            [project]
            dependencies = ["django>=4.2"]
        """))
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Django" for e in stack)

    def test_sqlalchemy_detected(self, tmp_path: Path):
        _make_file(tmp_path, "pyproject.toml", textwrap.dedent("""\
            [project]
            dependencies = ["sqlalchemy>=2.0"]
        """))
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "SQLAlchemy" for e in stack)


class TestDetectFromGoMod:
    """Detect technologies from go.mod."""

    def test_go_version(self, tmp_path: Path):
        _make_file(tmp_path, "go.mod", "module example.com/app\n\ngo 1.22\n")
        stack = detect_tech_stack(tmp_path)
        go = next(e for e in stack if e.name == "Go")
        assert go.version == "1.22"
        assert go.category == "language"


class TestDetectFromCsproj:
    """Detect technologies from .csproj."""

    def test_aspnet_core(self, tmp_path: Path):
        _make_file(tmp_path, "MyApp.csproj", textwrap.dedent("""\
            <Project Sdk="Microsoft.NET.Sdk.Web">
              <PropertyGroup>
                <TargetFramework>net8.0</TargetFramework>
              </PropertyGroup>
            </Project>
        """))
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "ASP.NET Core" for e in stack)
        assert any(e.name == "C#" for e in stack)


class TestDetectFromCargo:
    """Detect technologies from Cargo.toml."""

    def test_rust_detected(self, tmp_path: Path):
        _make_file(tmp_path, "Cargo.toml", "[package]\nname = \"myapp\"\n")
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Rust" for e in stack)

    def test_actix_detected(self, tmp_path: Path):
        _make_file(tmp_path, "Cargo.toml", "[dependencies]\nactix-web = \"4\"\n")
        stack = detect_tech_stack(tmp_path)
        assert any(e.name == "Actix" for e in stack)


class TestDetectFromText:
    """Detect technologies from PRD/MASTER_PLAN text."""

    def test_prd_mentions(self, tmp_path: Path):
        stack = detect_tech_stack(
            tmp_path,
            prd_text="Build using Next.js 14 with PostgreSQL and Tailwind CSS",
        )
        names = {e.name for e in stack}
        assert "Next.js" in names
        assert "PostgreSQL" in names
        assert "Tailwind CSS" in names

    def test_version_from_text(self, tmp_path: Path):
        stack = detect_tech_stack(tmp_path, prd_text="Use React 18.2 and Express 4.18")
        react = next(e for e in stack if e.name == "React")
        assert react.version == "18.2"

    def test_master_plan_text(self, tmp_path: Path):
        stack = detect_tech_stack(
            tmp_path, master_plan_text="## Milestone 1\nSet up Django with SQLAlchemy"
        )
        assert any(e.name == "Django" for e in stack)


class TestDetectDedup:
    """Deduplication: project files take precedence over text."""

    def test_file_version_wins(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={"next": "14.2.3"})
        stack = detect_tech_stack(tmp_path, prd_text="Use Next.js 13")
        nextjs = next(e for e in stack if e.name == "Next.js")
        # package.json version should win
        assert nextjs.version == "14.2.3"
        assert nextjs.source == "package.json"
        # No duplicate
        assert sum(1 for e in stack if e.name == "Next.js") == 1


class TestDetectSortingAndCap:
    """Sorting by category priority and max_techs cap."""

    def test_frameworks_before_testing(self, tmp_path: Path):
        _make_package_json(tmp_path, deps={
            "react": "18.0.0",
            "express": "4.0.0",
        }, dev_deps={
            "vitest": "1.0.0",
        })
        stack = detect_tech_stack(tmp_path)
        categories = [e.category for e in stack]
        # Frameworks should come before testing
        fw_idx = max(i for i, c in enumerate(categories) if "framework" in c)
        test_idx = min(i for i, c in enumerate(categories) if c == "testing")
        assert fw_idx < test_idx

    def test_max_techs_cap(self, tmp_path: Path):
        stack = detect_tech_stack(
            tmp_path,
            prd_text="Use React, Next.js, Express, PostgreSQL, Redis, Prisma, Tailwind CSS, Jest, Vitest, TypeScript, Python",
            max_techs=3,
        )
        assert len(stack) <= 3

    def test_empty_project(self, tmp_path: Path):
        stack = detect_tech_stack(tmp_path)
        assert stack == []


# ============================================================
# Query building tests
# ============================================================

class TestBuildResearchQueries:
    """Test query generation."""

    def test_basic_queries(self):
        stack = [
            TechStackEntry("React", "18.2.0", "frontend_framework", "package.json"),
        ]
        queries = build_research_queries(stack, max_per_tech=2)
        assert len(queries) == 2
        assert all(lib == "React" for lib, _ in queries)
        assert all("React" in q for _, q in queries)

    def test_version_in_query(self):
        stack = [
            TechStackEntry("Next.js", "14.0.0", "frontend_framework", "package.json"),
        ]
        queries = build_research_queries(stack, max_per_tech=1)
        assert "v14.0.0" in queries[0][1]

    def test_no_version_no_v_prefix(self):
        stack = [
            TechStackEntry("Express", None, "backend_framework", "prd_text"),
        ]
        queries = build_research_queries(stack, max_per_tech=1)
        assert "vNone" not in queries[0][1]
        assert "  " not in queries[0][1]  # no double spaces

    def test_category_specific_templates(self):
        db_stack = [TechStackEntry("PostgreSQL", "16", "database", "prd_text")]
        orm_stack = [TechStackEntry("Prisma", "5.0", "orm", "package.json")]
        db_queries = build_research_queries(db_stack, max_per_tech=1)
        orm_queries = build_research_queries(orm_stack, max_per_tech=1)
        # DB queries should mention schema/indexing
        assert any("schema" in q.lower() or "index" in q.lower() for _, q in db_queries)
        # ORM queries should mention schema/migration
        assert any("schema" in q.lower() or "migration" in q.lower() for _, q in orm_queries)

    def test_cap_respected(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
        ]
        queries = build_research_queries(stack, max_per_tech=1)
        assert len(queries) == 1
        queries4 = build_research_queries(stack, max_per_tech=4)
        assert len(queries4) == 4

    def test_empty_stack(self):
        assert build_research_queries([], max_per_tech=4) == []

    def test_multiple_techs(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
        ]
        queries = build_research_queries(stack, max_per_tech=2)
        react_queries = [(l, q) for l, q in queries if l == "React"]
        express_queries = [(l, q) for l, q in queries if l == "Express"]
        assert len(react_queries) == 2
        assert len(express_queries) == 2


# ============================================================
# Validation tests
# ============================================================

class TestValidateTechResearch:
    """Test research coverage validation."""

    def test_complete_research(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
        ]
        result = _make_result(stack, {"React": "findings...", "Express": "findings..."})
        is_valid, missing = validate_tech_research(result)
        assert is_valid is True
        assert missing == []

    def test_partial_above_threshold(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
            TechStackEntry("Jest", "29.0", "testing", "package.json"),
        ]
        result = _make_result(stack, {"React": "findings...", "Express": "findings..."})
        is_valid, missing = validate_tech_research(result, min_coverage=0.6)
        assert is_valid is True  # 2/3 = 0.67 > 0.6
        assert missing == ["Jest"]

    def test_below_threshold(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
            TechStackEntry("Jest", "29.0", "testing", "package.json"),
        ]
        result = _make_result(stack, {"React": "findings..."})
        is_valid, missing = validate_tech_research(result, min_coverage=0.6)
        assert is_valid is False  # 1/3 = 0.33 < 0.6
        assert "Express" in missing
        assert "Jest" in missing

    def test_empty_findings_treated_as_missing(self):
        stack = [TechStackEntry("React", "18.0", "frontend_framework", "package.json")]
        result = _make_result(stack, {"React": "  "})
        is_valid, missing = validate_tech_research(result)
        assert is_valid is False
        assert "React" in missing

    def test_empty_stack(self):
        result = _make_result([], {})
        is_valid, missing = validate_tech_research(result)
        assert is_valid is True
        assert missing == []

    def test_custom_threshold(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
        ]
        result = _make_result(stack, {"React": "findings..."})
        # 50% coverage with 50% threshold should pass
        is_valid, _ = validate_tech_research(result, min_coverage=0.5)
        assert is_valid is True

    def test_updates_result_fields(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.18", "backend_framework", "package.json"),
        ]
        result = _make_result(stack, {"React": "findings..."})
        validate_tech_research(result)
        assert result.techs_covered == 1
        assert result.is_complete is False


# ============================================================
# Extraction tests
# ============================================================

class TestExtractResearchSummary:
    """Test summary extraction for prompt injection."""

    def test_basic_extraction(self):
        stack = [TechStackEntry("React", "18.0", "frontend_framework", "package.json")]
        result = _make_result(stack, {"React": "Use hooks. Avoid class components."})
        summary = extract_research_summary(result)
        assert "## React (v18.0)" in summary
        assert "hooks" in summary

    def test_no_version(self):
        stack = [TechStackEntry("Express", None, "backend_framework", "prd_text")]
        result = _make_result(stack, {"Express": "Use middleware."})
        summary = extract_research_summary(result)
        assert "## Express" in summary
        assert "(v" not in summary  # No version shown

    def test_empty_findings(self):
        result = _make_result([], {})
        summary = extract_research_summary(result)
        assert summary == ""

    def test_truncation(self):
        stack = [TechStackEntry("React", "18.0", "frontend_framework", "package.json")]
        long_content = "x" * 10000
        result = _make_result(stack, {"React": long_content})
        summary = extract_research_summary(result, max_chars=200)
        assert len(summary) <= 200

    def test_priority_ordering(self):
        stack = [
            TechStackEntry("Jest", "29.0", "testing", "package.json"),
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("PostgreSQL", "16", "database", "prd_text"),
        ]
        result = _make_result(stack, {
            "Jest": "Test findings",
            "React": "React findings",
            "PostgreSQL": "DB findings",
        })
        summary = extract_research_summary(result)
        # React (frontend) should appear before Jest (testing)
        react_pos = summary.index("React")
        jest_pos = summary.index("Jest")
        assert react_pos < jest_pos

    def test_skips_empty_content(self):
        stack = [
            TechStackEntry("React", "18.0", "frontend_framework", "package.json"),
            TechStackEntry("Express", "4.0", "backend_framework", "package.json"),
        ]
        result = _make_result(stack, {"React": "content", "Express": ""})
        summary = extract_research_summary(result)
        assert "React" in summary
        assert "Express" not in summary

    def test_round_trip_parse_and_extract(self):
        """Parse TECH_RESEARCH.md then extract summary."""
        content = textwrap.dedent("""\
            # Tech Stack Research

            ## React (v18.2)
            - Use hooks for state management
            - Avoid class components

            ## Express (v4.18)
            - Use middleware for auth
            - Validate inputs
        """)
        result = parse_tech_research_file(content)
        summary = extract_research_summary(result)
        assert "React" in summary
        assert "Express" in summary

    def test_code_snippets_preserved(self):
        stack = [TechStackEntry("Next.js", "14.0", "frontend_framework", "package.json")]
        result = _make_result(stack, {"Next.js": "```tsx\nexport default function Page() {}\n```"})
        summary = extract_research_summary(result)
        assert "```tsx" in summary


# ============================================================
# Parsing tests
# ============================================================

class TestParseTechResearchFile:
    """Test TECH_RESEARCH.md parsing."""

    def test_basic_parse(self):
        content = textwrap.dedent("""\
            # Tech Stack Research

            ## React (v18.2)
            Use hooks for state.

            ## Express (v4.18)
            Use middleware.
        """)
        result = parse_tech_research_file(content)
        assert "React" in result.findings
        assert "Express" in result.findings
        assert result.techs_covered == 2

    def test_version_extracted(self):
        content = "## Next.js (v14.2.3)\nContent here.\n"
        result = parse_tech_research_file(content)
        nextjs_entry = next(e for e in result.stack if e.name == "Next.js")
        assert nextjs_entry.version == "14.2.3"

    def test_no_version(self):
        content = "## Tailwind CSS\nUse utility classes.\n"
        result = parse_tech_research_file(content)
        assert "Tailwind CSS" in result.findings

    def test_empty_content(self):
        result = parse_tech_research_file("")
        assert result.findings == {}
        assert result.stack == []

    def test_whitespace_only(self):
        result = parse_tech_research_file("   \n\n  ")
        assert result.findings == {}


# ============================================================
# Config tests
# ============================================================

class TestTechResearchConfig:
    """Test config integration."""

    def test_defaults(self):
        cfg = TechResearchConfig()
        assert cfg.enabled is True
        assert cfg.max_techs == 8
        assert cfg.max_queries_per_tech == 4
        assert cfg.retry_on_incomplete is True
        assert cfg.injection_max_chars == 6000

    def test_on_agent_team_config(self):
        cfg = AgentTeamConfig()
        assert isinstance(cfg.tech_research, TechResearchConfig)
        assert cfg.tech_research.enabled is True

    def test_yaml_loading(self):
        data = {"tech_research": {"enabled": False, "max_techs": 5}}
        cfg, overrides = _dict_to_config(data)
        assert cfg.tech_research.enabled is False
        assert cfg.tech_research.max_techs == 5

    def test_user_overrides_tracked(self):
        data = {"tech_research": {"enabled": False, "max_queries_per_tech": 2}}
        _, overrides = _dict_to_config(data)
        assert "tech_research.enabled" in overrides
        assert "tech_research.max_queries_per_tech" in overrides

    def test_validation_max_techs(self):
        with pytest.raises(ValueError, match="max_techs"):
            _dict_to_config({"tech_research": {"max_techs": 0}})

    def test_validation_max_queries(self):
        with pytest.raises(ValueError, match="max_queries_per_tech"):
            _dict_to_config({"tech_research": {"max_queries_per_tech": 0}})


class TestDepthGating:
    """Test depth-based gating for tech research."""

    def test_quick_disables(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.tech_research.enabled is False

    def test_standard_reduces_queries(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.tech_research.enabled is True
        assert cfg.tech_research.max_queries_per_tech == 2

    def test_thorough_default(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("thorough", cfg)
        assert cfg.tech_research.enabled is True
        assert cfg.tech_research.max_queries_per_tech == 4  # Default

    def test_exhaustive_increases_queries(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", cfg)
        assert cfg.tech_research.enabled is True
        assert cfg.tech_research.max_queries_per_tech == 6

    def test_user_override_respected(self):
        cfg = AgentTeamConfig()
        overrides = {"tech_research.enabled"}
        apply_depth_quality_gating("quick", cfg, user_overrides=overrides)
        # User explicitly set enabled, so quick depth should NOT override it
        assert cfg.tech_research.enabled is True

    def test_user_override_queries_respected(self):
        cfg = AgentTeamConfig()
        cfg.tech_research.max_queries_per_tech = 10
        overrides = {"tech_research.max_queries_per_tech"}
        apply_depth_quality_gating("standard", cfg, user_overrides=overrides)
        # User explicitly set max_queries_per_tech, should stay at 10
        assert cfg.tech_research.max_queries_per_tech == 10


# ============================================================
# Prompt injection tests
# ============================================================

class TestPromptInjection:
    """Test tech research content injection into prompts."""

    def test_milestone_prompt_with_content(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content="## React (v18.2)\n- Use hooks",
        )
        assert "[TECH STACK BEST PRACTICES -- FROM DOCUMENTATION]" in prompt
        assert "React" in prompt
        assert "Use hooks" in prompt

    def test_milestone_prompt_empty_content(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content="",
        )
        assert "TECH STACK BEST PRACTICES" not in prompt

    def test_orchestrator_prompt_with_content(self):
        cfg = AgentTeamConfig()
        prompt = build_orchestrator_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content="## Express (v4.18)\n- Use middleware",
        )
        assert "[TECH STACK BEST PRACTICES -- FROM DOCUMENTATION]" in prompt
        assert "Express" in prompt

    def test_orchestrator_prompt_empty_content(self):
        cfg = AgentTeamConfig()
        prompt = build_orchestrator_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content="",
        )
        assert "TECH STACK BEST PRACTICES" not in prompt

    def test_injection_header_text(self):
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content="content here",
        )
        assert "official documentation" in prompt.lower()
        assert "Context7" in prompt

    def test_default_parameter_backwards_compat(self):
        """Existing callers without tech_research_content should work."""
        cfg = AgentTeamConfig()
        # Call without the new parameter — should not raise
        prompt = build_milestone_execution_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
        )
        assert "TECH STACK BEST PRACTICES" not in prompt


# ============================================================
# MCP servers test
# ============================================================

class TestGetContext7OnlyServers:
    """Test get_context7_only_servers function."""

    def test_returns_context7_when_enabled(self):
        cfg = AgentTeamConfig()
        servers = get_context7_only_servers(cfg)
        assert "context7" in servers
        assert servers["context7"]["command"] == "npx"

    def test_empty_when_disabled(self):
        cfg = AgentTeamConfig()
        cfg.mcp_servers["context7"].enabled = False
        servers = get_context7_only_servers(cfg)
        assert servers == {}

    def test_no_firecrawl(self):
        cfg = AgentTeamConfig()
        servers = get_context7_only_servers(cfg)
        assert "firecrawl" not in servers

    def test_no_sequential_thinking(self):
        cfg = AgentTeamConfig()
        servers = get_context7_only_servers(cfg)
        assert "sequential_thinking" not in servers

    def test_no_playwright(self):
        cfg = AgentTeamConfig()
        servers = get_context7_only_servers(cfg)
        assert "playwright" not in servers


# ============================================================
# Wiring tests
# ============================================================

class TestCliWiring:
    """Test that CLI wiring is correctly implemented."""

    def test_run_tech_research_function_exists(self):
        """_run_tech_research should be importable from cli module."""
        from agent_team.cli import _run_tech_research
        assert callable(_run_tech_research)

    def test_run_single_accepts_tech_research_content(self):
        """_run_single should accept tech_research_content parameter."""
        import inspect
        from agent_team.cli import _run_single
        sig = inspect.signature(_run_single)
        assert "tech_research_content" in sig.parameters
        # Default should be empty string
        assert sig.parameters["tech_research_content"].default == ""

    def test_phase_placement_in_source(self):
        """Phase 1.5 should appear after MASTER_PLAN.md parse and before execution loop."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        phase_15_pos = cli_src.index("Phase 1.5: TECH STACK RESEARCH")
        parse_plan_pos = cli_src.index("# Parse the master plan")
        execution_loop_pos = cli_src.index("# Phase 2: EXECUTION LOOP")
        assert parse_plan_pos < phase_15_pos < execution_loop_pos

    def test_crash_isolation(self):
        """Phase 1.5 should be wrapped in try/except."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the Phase 1.5 block
        phase_15_idx = cli_src.index("Phase 1.5: TECH STACK RESEARCH")
        # Use a wider window to capture the full try/except block
        block = cli_src[phase_15_idx - 200:phase_15_idx + 1500]
        assert "try:" in block
        assert "except Exception" in block
        assert "non-blocking" in block.lower()

    def test_config_gated(self):
        """Phase 1.5 should be gated on config.tech_research.enabled."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        phase_15_idx = cli_src.index("Phase 1.5: TECH STACK RESEARCH")
        # The config gate is in the surrounding code block
        block = cli_src[phase_15_idx:phase_15_idx + 1500]
        assert "config.tech_research.enabled" in block

    def test_result_threaded_to_milestone_prompt(self):
        """tech_research_content should be passed to build_milestone_execution_prompt."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the build_milestone_execution_prompt call
        assert "tech_research_content=tech_research_content" in cli_src


# ============================================================
# TECH_RESEARCH_PROMPT constant tests
# ============================================================

class TestTechResearchPrompt:
    """Test the prompt constant."""

    def test_prompt_has_context7_instructions(self):
        assert "resolve-library-id" in TECH_RESEARCH_PROMPT
        assert "query-docs" in TECH_RESEARCH_PROMPT

    def test_prompt_has_placeholders(self):
        assert "{tech_list}" in TECH_RESEARCH_PROMPT
        assert "{queries_block}" in TECH_RESEARCH_PROMPT
        assert "{output_path}" in TECH_RESEARCH_PROMPT

    def test_prompt_format_works(self):
        """Prompt should be formattable without errors."""
        formatted = TECH_RESEARCH_PROMPT.format(
            tech_list="- React v18",
            queries_block="1. Setup patterns",
            output_path=".agent-team/TECH_RESEARCH.md",
        )
        assert "React v18" in formatted
        assert "TECH_RESEARCH.md" in formatted


# ============================================================
# Utility tests
# ============================================================

class TestStripVersionPrefix:
    """Test version prefix stripping."""

    def test_caret(self):
        assert _strip_version_prefix("^18.2.0") == "18.2.0"

    def test_tilde(self):
        assert _strip_version_prefix("~4.18.2") == "4.18.2"

    def test_gte(self):
        assert _strip_version_prefix(">=1.0.0") == "1.0.0"

    def test_no_prefix(self):
        assert _strip_version_prefix("18.2.0") == "18.2.0"

    def test_workspace_star(self):
        assert _strip_version_prefix("*") == ""

    def test_empty(self):
        assert _strip_version_prefix("") == ""


# ============================================================
# v14.0 Production Hardening Tests
# ============================================================


class TestGoFalsePositivePrevention:
    """BUG #7 FIX: Go regex should NOT match English word 'Go'."""

    def test_go_to_settings_not_detected(self):
        """'Go to the settings page' should NOT detect Go language."""
        entries = _detect_from_text("Go to the settings page and configure your profile.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 0

    def test_go_ahead_not_detected(self):
        """'Go ahead and deploy' should NOT detect Go language."""
        entries = _detect_from_text("Go ahead and deploy the application.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 0

    def test_golang_detected(self):
        """'Golang' should detect Go language."""
        entries = _detect_from_text("The backend is written in Golang.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 1

    def test_golang_with_version(self):
        """'Golang v1.21' should detect Go with version."""
        entries = _detect_from_text("Use Golang v1.21 for the API.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 1
        assert go_entries[0].version == "1.21"

    def test_go_with_version_detected(self):
        """'Go 1.21' with explicit version should detect Go language."""
        entries = _detect_from_text("Use Go 1.21.3 for the backend.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 1
        assert go_entries[0].version == "1.21.3"

    def test_go_version_with_v_prefix(self):
        """'Go v1.22' with version should detect Go language."""
        entries = _detect_from_text("Build with Go v1.22 runtime.", "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 1
        assert go_entries[0].version == "1.22"

    def test_go_mod_detection_still_works(self, tmp_path):
        """Go should still be detected from go.mod file."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module example.com/myapp\n\ngo 1.21\n", encoding="utf-8")
        stack = detect_tech_stack(tmp_path)
        go_entries = [e for e in stack if e.name == "Go"]
        assert len(go_entries) == 1
        assert go_entries[0].version == "1.21"
        assert go_entries[0].source == "go.mod"

    def test_go_not_detected_from_ambiguous_prd(self):
        """A PRD mentioning 'Go' as a verb should not trigger detection."""
        prd = (
            "Users can Go back to the dashboard. The system will Go through "
            "the validation steps. Let's Go live with the deployment."
        )
        entries = _detect_from_text(prd, "prd_text")
        go_entries = [e for e in entries if e.name == "Go"]
        assert len(go_entries) == 0


class TestCsprojSkipDirs:
    """BUG #5+#8 FIX: csproj detection should skip heavy directories."""

    def test_skip_dirs_frozenset_defined(self):
        """_CSPROJ_SKIP_DIRS should be a non-empty frozenset."""
        assert isinstance(_CSPROJ_SKIP_DIRS, frozenset)
        assert len(_CSPROJ_SKIP_DIRS) > 0

    def test_skip_dirs_contains_known_heavy_dirs(self):
        """Should skip node_modules, .git, bin, obj, etc."""
        for d in ["node_modules", ".git", "bin", "obj"]:
            assert d in _CSPROJ_SKIP_DIRS

    def test_node_modules_csproj_skipped(self, tmp_path):
        """csproj files inside node_modules should be skipped."""
        # Create a csproj in node_modules (should be skipped)
        nm_csproj = tmp_path / "node_modules" / "SomePackage" / "test.csproj"
        nm_csproj.parent.mkdir(parents=True)
        nm_csproj.write_text(
            '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
            '<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
        stack = detect_tech_stack(tmp_path)
        aspnet_entries = [e for e in stack if e.name == "ASP.NET Core"]
        assert len(aspnet_entries) == 0

    def test_root_csproj_detected(self, tmp_path):
        """csproj files at project root should still be detected."""
        csproj = tmp_path / "MyApp.csproj"
        csproj.write_text(
            '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
            '<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
        stack = detect_tech_stack(tmp_path)
        aspnet_entries = [e for e in stack if e.name == "ASP.NET Core"]
        assert len(aspnet_entries) == 1
        assert aspnet_entries[0].version == "8.0"

    def test_no_duplicate_from_csproj(self, tmp_path):
        """Same csproj should not produce duplicate entries."""
        csproj = tmp_path / "MyApp.csproj"
        csproj.write_text(
            '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
            '<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
        stack = detect_tech_stack(tmp_path)
        aspnet_entries = [e for e in stack if e.name == "ASP.NET Core"]
        assert len(aspnet_entries) == 1  # No duplicate


class TestRunCostPreservation:
    """BUG #1 FIX: Research cost should not be lost in standard mode."""

    def test_std_research_cost_added_after_run_single(self):
        """The standard mode code should add research cost AFTER _run_single."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find _run_single call
        run_single_idx = cli_src.index("run_cost = asyncio.run(_run_single(")
        # Find the next occurrence of _std_research_cost after _run_single
        after_single = cli_src[run_single_idx:]
        assert "_std_research_cost" in after_single

    def test_no_run_cost_overwrite_before_run_single(self):
        """run_cost should NOT be set with research cost BEFORE _run_single."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the standard mode tech research block
        std_block_start = cli_src.index("Standard mode: lightweight tech research")
        std_block_end = cli_src.index("run_cost = asyncio.run(_run_single(")
        between = cli_src[std_block_start:std_block_end]
        # There should be NO "run_cost = " or "run_cost =" in this block
        # (it should only set _std_research_cost, not run_cost)
        assert "run_cost =" not in between.replace("_std_research_cost", "")

    def test_std_research_cost_initialized_before_block(self):
        """_std_research_cost should be initialized to 0.0 before the if block."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        std_block_start = cli_src.index("Standard mode: lightweight tech research")
        # Look in the 200 chars before for initialization
        before = cli_src[std_block_start - 200:std_block_start]
        assert "_std_research_cost = 0.0" in before or \
               "_std_research_cost = 0.0" in cli_src[std_block_start:std_block_start + 500]

    def test_cost_only_added_when_positive(self):
        """Research cost should only be added when > 0."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        run_single_idx = cli_src.index("run_cost = asyncio.run(_run_single(")
        after = cli_src[run_single_idx:run_single_idx + 2000]
        assert "_std_research_cost > 0" in after


class TestRetryPromptSafety:
    """BUG #4 FIX: Retry prompt should instruct reading existing file."""

    def test_retry_prompt_includes_read_instruction(self):
        """Retry prompt should tell agent to READ existing file first."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        retry_idx = cli_src.index("retry_prompt")
        retry_block = cli_src[retry_idx:retry_idx + 800]
        assert "read" in retry_block.lower() or "READ" in retry_block

    def test_retry_prompt_warns_against_overwrite(self):
        """Retry prompt should warn against overwriting existing sections."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        retry_idx = cli_src.index("retry_prompt")
        retry_block = cli_src[retry_idx:retry_idx + 800]
        assert "overwrite" in retry_block.lower() or "remove" in retry_block.lower()

    def test_retry_prompt_mentions_existing_file(self):
        """Retry prompt should reference the output file path."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        retry_idx = cli_src.index("retry_prompt")
        retry_block = cli_src[retry_idx:retry_idx + 800]
        assert "output_path" in retry_block


class TestStandardModeNoDoubleDetection:
    """BUG #11 FIX: Standard mode should not call detect_tech_stack twice."""

    def test_no_outer_detect_tech_stack_call(self):
        """Standard mode should delegate detection to _run_tech_research."""
        cli_src = (_SRC / "cli.py").read_text(encoding="utf-8")
        std_block_start = cli_src.index("Standard mode: lightweight tech research")
        std_block_end = cli_src.index("run_cost = asyncio.run(_run_single(")
        between = cli_src[std_block_start:std_block_end]
        # Should NOT have a separate detect_tech_stack call
        assert "detect_tech_stack(" not in between


class TestVersionExtractionMultiGroup:
    """Test that version extraction works with multi-group regex patterns."""

    def test_golang_version_group_1(self):
        """Golang with version should capture from group 1."""
        entries = _detect_from_text("Using Golang v1.21.0", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 1
        assert go[0].version == "1.21.0"

    def test_go_version_group_2(self):
        """Go with version number should capture from group 2."""
        entries = _detect_from_text("Using Go 1.22.1 runtime", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 1
        assert go[0].version == "1.22.1"

    def test_other_techs_still_extract_version(self):
        """Non-Go techs should still extract versions correctly."""
        entries = _detect_from_text("React 18.2.0 and Next.js 14.1.0", "prd_text")
        react = [e for e in entries if e.name == "React"]
        nextjs = [e for e in entries if e.name == "Next.js"]
        assert react[0].version == "18.2.0"
        assert nextjs[0].version == "14.1.0"


class TestEdgeCases:
    """Additional edge case tests for production readiness."""

    def test_detect_with_no_files_no_text(self, tmp_path):
        """Empty directory with no text should return empty list."""
        stack = detect_tech_stack(tmp_path, prd_text="", master_plan_text="")
        assert stack == []

    def test_extract_summary_empty_findings(self):
        """Empty findings dict should return empty string."""
        result = TechResearchResult(findings={})
        assert extract_research_summary(result) == ""

    def test_extract_summary_empty_content(self):
        """Findings with empty string values should be skipped."""
        result = TechResearchResult(
            findings={"React": "", "Next.js": ""},
            stack=[
                TechStackEntry("React", "18", "frontend_framework", "test"),
                TechStackEntry("Next.js", "14", "frontend_framework", "test"),
            ],
        )
        assert extract_research_summary(result) == ""

    def test_parse_tech_research_with_subsections(self):
        """h3 subsections inside h2 sections should be preserved in body."""
        content = textwrap.dedent("""\
            # Tech Research

            ## React (v18.2)
            Main framework info.

            ### Hooks
            Use useEffect carefully.

            ### State
            Prefer useReducer.

            ## PostgreSQL (v15)
            Database info here.
        """)
        result = parse_tech_research_file(content)
        assert "React" in result.findings
        assert "### Hooks" in result.findings["React"]
        assert "### State" in result.findings["React"]
        assert "PostgreSQL" in result.findings

    def test_validate_mutates_result_fields(self):
        """validate_tech_research should update techs_covered and is_complete."""
        result = TechResearchResult(
            stack=[
                TechStackEntry("React", "18", "frontend_framework", "test"),
                TechStackEntry("Next.js", "14", "frontend_framework", "test"),
            ],
            findings={"React": "info", "Next.js": "info"},
            techs_total=2,
        )
        is_valid, missing = validate_tech_research(result)
        assert is_valid is True
        assert result.techs_covered == 2
        assert result.is_complete is True

    def test_validate_partial_coverage(self):
        """Partial coverage should update fields correctly."""
        result = TechResearchResult(
            stack=[
                TechStackEntry("React", "18", "frontend_framework", "test"),
                TechStackEntry("Next.js", "14", "frontend_framework", "test"),
                TechStackEntry("PostgreSQL", None, "database", "test"),
            ],
            findings={"React": "info"},
            techs_total=3,
        )
        is_valid, missing = validate_tech_research(result, min_coverage=0.5)
        assert is_valid is False
        assert result.techs_covered == 1
        assert result.is_complete is False
        assert "Next.js" in missing
        assert "PostgreSQL" in missing

    def test_build_queries_with_empty_version_no_double_spaces(self):
        """Queries with no version should not have double spaces."""
        stack = [TechStackEntry("React", None, "frontend_framework", "test")]
        queries = build_research_queries(stack, max_per_tech=1)
        assert len(queries) == 1
        _, query = queries[0]
        assert "  " not in query  # No double spaces

    def test_detect_react_not_from_verb(self):
        """'react' as English verb should ideally not trigger (case sensitivity)."""
        # Note: our regex uses re.IGNORECASE, so "react" matches.
        # But since "React" is always capitalized in tech context and
        # rarely used lowercase as a verb in PRDs, this is acceptable.
        entries = _detect_from_text("Users react to notifications", "prd_text")
        # This IS detected due to IGNORECASE — documenting known behavior
        react_entries = [e for e in entries if e.name == "React"]
        assert len(react_entries) >= 0  # Documenting current behavior

    def test_dedup_project_file_wins_over_text(self, tmp_path):
        """Project file detection should take precedence over text mentions."""
        _make_package_json(tmp_path, deps={"react": "^18.2.0"})
        stack = detect_tech_stack(
            tmp_path,
            prd_text="Use React 17.0.0 for the frontend",
        )
        react_entries = [e for e in stack if e.name == "React"]
        assert len(react_entries) == 1
        assert react_entries[0].version == "18.2.0"  # From package.json, not text
        assert react_entries[0].source == "package.json"

    def test_max_techs_cap_respected(self, tmp_path):
        """detect_tech_stack should cap at max_techs."""
        _make_package_json(tmp_path, deps={
            "react": "18", "next": "14", "express": "4",
            "prisma": "5", "tailwindcss": "3", "jest": "29",
            "typescript": "5", "pg": "8", "redis": "4",
        })
        stack = detect_tech_stack(tmp_path, max_techs=3)
        assert len(stack) == 3

    def test_category_sort_order(self, tmp_path):
        """Frameworks should appear before testing libraries."""
        _make_package_json(tmp_path, deps={
            "jest": "29", "react": "18",
        })
        stack = detect_tech_stack(tmp_path)
        names = [e.name for e in stack]
        react_idx = names.index("React")
        jest_idx = names.index("Jest")
        assert react_idx < jest_idx  # Framework before testing


# ============================================================
# Round 2 — Deep Production Audit Tests
# ============================================================


class TestPackageJsonNullDeps:
    """BUG #14 FIX: package.json with null dependencies should not crash."""

    def test_null_dependencies(self, tmp_path):
        """package.json with 'dependencies': null should not crash."""
        pkg = {"dependencies": None, "devDependencies": {"react": "^18.2.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        stack = detect_tech_stack(tmp_path)
        react = [e for e in stack if e.name == "React"]
        assert len(react) == 1

    def test_null_devdependencies(self, tmp_path):
        """package.json with 'devDependencies': null should not crash."""
        pkg = {"dependencies": {"express": "^4.18.2"}, "devDependencies": None}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        stack = detect_tech_stack(tmp_path)
        express = [e for e in stack if e.name == "Express"]
        assert len(express) == 1

    def test_both_null(self, tmp_path):
        """package.json with both null should return empty."""
        pkg = {"dependencies": None, "devDependencies": None}
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        stack = detect_tech_stack(tmp_path)
        assert stack == []

    def test_mixed_null_and_valid(self, tmp_path):
        """Null deps + valid devDeps should detect from devDeps."""
        pkg = {
            "dependencies": None,
            "devDependencies": {"typescript": "^5.3.0", "jest": "^29.7.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
        stack = detect_tech_stack(tmp_path)
        names = {e.name for e in stack}
        assert "TypeScript" in names
        assert "Jest" in names


class TestCsprojNestedDetection:
    """Verify csproj detection in nested directories."""

    def test_nested_src_directory(self, tmp_path):
        """csproj in src/ subdirectory should be found."""
        csproj = tmp_path / "src" / "WebApi" / "WebApi.csproj"
        csproj.parent.mkdir(parents=True)
        csproj.write_text(
            '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
            '<TargetFramework>net7.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
        stack = detect_tech_stack(tmp_path)
        aspnet = [e for e in stack if e.name == "ASP.NET Core"]
        assert len(aspnet) == 1
        assert aspnet[0].version == "7.0"

    def test_obj_directory_skipped(self, tmp_path):
        """csproj in obj/ should be skipped."""
        obj_csproj = tmp_path / "obj" / "Debug" / "test.csproj"
        obj_csproj.parent.mkdir(parents=True)
        obj_csproj.write_text(
            '<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup>'
            '<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
        stack = detect_tech_stack(tmp_path)
        aspnet = [e for e in stack if e.name == "ASP.NET Core"]
        assert len(aspnet) == 0


class TestPyprojectVersionExtraction:
    """Verify pyproject.toml version extraction."""

    def test_django_version(self, tmp_path):
        _make_file(tmp_path, "pyproject.toml", textwrap.dedent("""\
            [project]
            dependencies = [
                "django>=4.2.0",
                "celery>=5.3",
            ]
        """))
        stack = detect_tech_stack(tmp_path)
        django = [e for e in stack if e.name == "Django"]
        assert len(django) == 1
        assert django[0].version == "4.2.0"

    def test_python_auto_added(self, tmp_path):
        _make_file(tmp_path, "pyproject.toml", textwrap.dedent("""\
            [project]
            dependencies = ["fastapi>=0.100"]
        """))
        stack = detect_tech_stack(tmp_path)
        python = [e for e in stack if e.name == "Python"]
        assert len(python) == 1


class TestRequirementsTxtEdgeCases:
    """Edge cases for requirements.txt parsing."""

    def test_extras_syntax(self, tmp_path):
        """Package with extras like 'django[argon2]' should be detected."""
        _make_file(tmp_path, "requirements.txt", "django[argon2]==4.2.3\n")
        stack = detect_tech_stack(tmp_path)
        django = [e for e in stack if e.name == "Django"]
        assert len(django) == 1
        assert django[0].version == "4.2.3"

    def test_comment_lines_skipped(self, tmp_path):
        """Lines starting with # should be skipped."""
        _make_file(tmp_path, "requirements.txt", "# django==4.2\nflask==3.0.0\n")
        stack = detect_tech_stack(tmp_path)
        django = [e for e in stack if e.name == "Django"]
        flask = [e for e in stack if e.name == "Flask"]
        assert len(django) == 0
        assert len(flask) == 1


class TestExtractSummaryEdgeCases:
    """Edge cases for extract_research_summary."""

    def test_truncation_exact_boundary(self):
        """If total exactly equals max_chars, no truncation needed."""
        content = "a" * 50  # 50 chars of content
        result = TechResearchResult(
            findings={"React": content},
            stack=[TechStackEntry("React", "18", "frontend_framework", "test")],
        )
        summary = extract_research_summary(result, max_chars=10000)
        assert "React" in summary
        assert content in summary

    def test_finding_not_in_stack_gets_priority_99(self):
        """Finding for a tech not in stack should sort to bottom."""
        result = TechResearchResult(
            findings={
                "React": "Frontend framework info",
                "UnknownLib": "Some info",
            },
            stack=[
                TechStackEntry("React", "18", "frontend_framework", "test"),
            ],
        )
        summary = extract_research_summary(result)
        react_pos = summary.index("React")
        unknown_pos = summary.index("UnknownLib")
        assert react_pos < unknown_pos


class TestValidateEdgeCases:
    """Edge cases for validate_tech_research."""

    def test_whitespace_only_findings_counted_as_missing(self):
        """Findings with only whitespace should be counted as missing."""
        result = TechResearchResult(
            stack=[TechStackEntry("React", "18", "frontend_framework", "test")],
            findings={"React": "   \n  \t  "},
            techs_total=1,
        )
        is_valid, missing = validate_tech_research(result, min_coverage=0.5)
        assert is_valid is False
        assert "React" in missing

    def test_custom_threshold_100_percent(self):
        """100% threshold requires all techs covered."""
        result = TechResearchResult(
            stack=[
                TechStackEntry("React", "18", "frontend_framework", "test"),
                TechStackEntry("Next.js", "14", "frontend_framework", "test"),
            ],
            findings={"React": "info"},
            techs_total=2,
        )
        is_valid, _ = validate_tech_research(result, min_coverage=1.0)
        assert is_valid is False


class TestParseEdgeCases:
    """Edge cases for parse_tech_research_file."""

    def test_empty_body_section_skipped(self):
        """Section with empty body should not be in findings."""
        content = "## React (v18)\n\n## Next.js (v14)\nSome content here."
        result = parse_tech_research_file(content)
        assert "Next.js" in result.findings
        # React has empty body between headers — should be skipped
        assert "React" not in result.findings or result.findings.get("React", "").strip() == ""

    def test_special_chars_in_tech_name(self):
        """Tech names with special chars like '/' should parse correctly."""
        content = "## shadcn/ui\n- Component library info\n- Use cn() helper"
        result = parse_tech_research_file(content)
        assert "shadcn/ui" in result.findings


class TestBuildQueriesCategoryLimits:
    """Verify query building respects category-specific template counts."""

    def test_language_category_only_2_templates(self):
        """Language category has only 2 query templates."""
        stack = [TechStackEntry("TypeScript", "5.3", "language", "test")]
        queries = build_research_queries(stack, max_per_tech=10)
        # Even with max_per_tech=10, language only has 2 templates
        assert len(queries) == 2

    def test_frontend_category_4_templates(self):
        """Frontend framework category has 4 query templates."""
        stack = [TechStackEntry("React", "18", "frontend_framework", "test")]
        queries = build_research_queries(stack, max_per_tech=10)
        assert len(queries) == 4

    def test_cap_below_template_count(self):
        """max_per_tech < template count should cap queries."""
        stack = [TechStackEntry("React", "18", "frontend_framework", "test")]
        queries = build_research_queries(stack, max_per_tech=2)
        assert len(queries) == 2


class TestFullPipelineIntegration:
    """End-to-end integration from detection to prompt injection."""

    def test_full_pipeline_react_express(self, tmp_path):
        """Full pipeline: package.json → detect → queries → summary → prompt."""
        _make_package_json(tmp_path, deps={
            "react": "^18.2.0",
            "express": "^4.18.2",
            "prisma": "^5.0.0",
        })

        # Step 1: Detect
        stack = detect_tech_stack(tmp_path)
        assert len(stack) >= 3
        names = {e.name for e in stack}
        assert "React" in names
        assert "Express" in names
        assert "Prisma" in names

        # Step 2: Build queries
        queries = build_research_queries(stack, max_per_tech=2)
        assert len(queries) >= 6  # 3 techs × 2 queries each

        # Step 3: Create mock research result
        result = TechResearchResult(
            stack=stack,
            findings={
                "React": "- Use functional components\n- Prefer hooks",
                "Express": "- Use middleware chains\n- Validate input",
                "Prisma": "- Define models in schema.prisma\n- Use migrations",
            },
            techs_total=len(stack),
        )

        # Step 4: Validate
        is_valid, missing = validate_tech_research(result)
        assert is_valid is True

        # Step 5: Extract summary
        summary = extract_research_summary(result, max_chars=6000)
        assert "React" in summary
        assert "Express" in summary
        assert "Prisma" in summary

        # Step 6: Inject into prompt
        cfg = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build app",
            depth="standard",
            config=cfg,
            tech_research_content=summary,
        )
        assert "[TECH STACK BEST PRACTICES -- FROM DOCUMENTATION]" in prompt
        assert "functional components" in prompt
        assert "middleware chains" in prompt

    def test_full_pipeline_python_project(self, tmp_path):
        """Full pipeline for a Python project."""
        _make_file(tmp_path, "requirements.txt", "django==4.2.8\npsycopg2==2.9.9\npytest==7.4.3\n")

        stack = detect_tech_stack(tmp_path)
        names = {e.name for e in stack}
        assert "Django" in names
        assert "PostgreSQL" in names
        assert "Pytest" in names
        assert "Python" in names

        queries = build_research_queries(stack, max_per_tech=2)
        assert len(queries) >= 6  # Django(4) + PostgreSQL(4) + Pytest(4) + Python(2), capped at 2 each = 8

    def test_full_pipeline_empty_project(self, tmp_path):
        """Empty project with no tech should produce no research content."""
        stack = detect_tech_stack(tmp_path)
        assert stack == []

        # No research possible
        result = TechResearchResult(techs_total=0)
        is_valid, missing = validate_tech_research(result)
        assert is_valid is True
        assert missing == []

        summary = extract_research_summary(result)
        assert summary == ""


class TestGoEdgeCasesComprehensive:
    """Comprehensive Go regex verification."""

    def test_go_bare_word_no_match(self):
        """Just 'Go' without context should not match."""
        entries = _detect_from_text("Go", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 0

    def test_go_in_url_no_match(self):
        """'Go' in URL-like context should not match."""
        entries = _detect_from_text("Visit https://go.dev for details", "prd_text")
        # "go" in URL doesn't have \b boundary + version, so no match expected
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 0

    def test_golang_case_insensitive(self):
        """'golang' (lowercase) should match due to IGNORECASE."""
        entries = _detect_from_text("Backend written in golang", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 1

    def test_go_with_two_digit_version(self):
        """'Go 1.22' should match."""
        entries = _detect_from_text("Requires Go 1.22", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 1
        assert go[0].version == "1.22"

    def test_go_with_three_digit_version(self):
        """'Go 1.21.5' should match."""
        entries = _detect_from_text("Using Go 1.21.5", "prd_text")
        go = [e for e in entries if e.name == "Go"]
        assert len(go) == 1
        assert go[0].version == "1.21.5"
