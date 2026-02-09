"""Tests for UI Requirements Hardening (Fix 6).

Covers: design_reference.py helpers, quality_checks.py UI compliance,
config.py new fields, agents.py prompt content, and milestone prompt
UI enforcement.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent_team.config import (
    AgentTeamConfig,
    DesignReferenceConfig,
    MilestoneConfig,
    _dict_to_config,
)
from src.agent_team.design_reference import (
    DesignExtractionError,
    _split_into_sections,
    validate_ui_requirements_content,
    generate_fallback_ui_requirements,
    _infer_design_direction,
    _DIRECTION_TABLE,
    run_design_extraction_with_retry,
)
from src.agent_team.quality_checks import (
    Violation,
    _check_ui_compliance,
    run_ui_compliance_scan,
)
from src.agent_team.agents import (
    CODE_WRITER_PROMPT,
    CODE_REVIEWER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    build_milestone_execution_prompt,
)


# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

GOOD_UI_CONTENT = """
## Color System
- Primary: #1A1A2E
- Secondary: #E8D5B7
- Accent: #C9A96E
- Background: #FFFFFF

## Typography
- Heading font: Cormorant Garamond
- Body font: Outfit

## Spacing
- Base unit: 8px
- sm: 8px
- md: 16px
- lg: 24px

## Component Patterns
- Button styles with border-radius
- Card patterns with shadow
- Input field styles
"""


def _make_config(**overrides) -> AgentTeamConfig:
    """Helper to create a config with optional overrides."""
    cfg = AgentTeamConfig()
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


# ===================================================================
# 1. TestSplitIntoSections
# ===================================================================


class TestSplitIntoSections:
    """Tests for _split_into_sections markdown parser."""

    def test_well_formed_sections(self):
        content = "## Color System\n- Primary: #123\n## Typography\n- Font: Inter\n"
        result = _split_into_sections(content)
        assert "color system" in result
        assert "typography" in result
        assert "#123" in result["color system"]
        assert "Inter" in result["typography"]

    def test_empty_content(self):
        result = _split_into_sections("")
        assert result == {}

    def test_no_sections(self):
        result = _split_into_sections("Just some text\nwithout any headers\n")
        assert result == {}

    def test_nested_headers(self):
        content = "## Color System\n### Palette\n- Primary: #AAA\n### Dark Mode\n- BG: #000\n"
        result = _split_into_sections(content)
        assert "color system" in result
        body = result["color system"]
        assert "### Palette" in body
        assert "### Dark Mode" in body
        assert "#AAA" in body
        assert "#000" in body


# ===================================================================
# 2. TestValidateUIRequirementsContent
# ===================================================================


class TestValidateUIRequirementsContent:
    """Tests for validate_ui_requirements_content quality checks."""

    def test_good_content(self):
        issues = validate_ui_requirements_content(GOOD_UI_CONTENT)
        assert issues == [], f"Expected no issues but got: {issues}"

    def test_missing_colors(self):
        content = "## Color System\n- Primary: #ABC\n## Typography\n- Heading font: Inter\n## Spacing\n- sm: 8px\n- md: 16px\n- lg: 24px\n## Component Patterns\n- Button styles\n- Card patterns\n"
        issues = validate_ui_requirements_content(content)
        color_issues = [i for i in issues if "hex color" in i]
        assert len(color_issues) == 1
        assert "only 1 hex color" in color_issues[0]

    def test_missing_fonts(self):
        content = "## Color System\n- Primary: #AAA\n- Secondary: #BBB\n- Accent: #CCC\n## Typography\nNo fonts here\n## Spacing\n- sm: 8px\n- md: 16px\n- lg: 24px\n## Component Patterns\n- Button\n- Card\n"
        issues = validate_ui_requirements_content(content)
        font_issues = [i for i in issues if "font family" in i.lower()]
        assert len(font_issues) == 1

    def test_missing_spacing(self):
        content = "## Color System\n- Primary: #AAA\n- Secondary: #BBB\n- Accent: #CCC\n## Typography\n- Heading font: Inter\n## Spacing\n- Only one: 8px\n## Component Patterns\n- Button\n- Card\n"
        issues = validate_ui_requirements_content(content)
        spacing_issues = [i for i in issues if "spacing" in i.lower()]
        assert len(spacing_issues) == 1

    def test_missing_components(self):
        content = "## Color System\n- Primary: #AAA\n- Secondary: #BBB\n- Accent: #CCC\n## Typography\n- Heading font: Inter\n## Spacing\n- sm: 8px\n- md: 16px\n- lg: 24px\n## Component Patterns\nNo components here\n"
        issues = validate_ui_requirements_content(content)
        component_issues = [i for i in issues if "component" in i.lower()]
        assert len(component_issues) == 1

    def test_not_found_excessive(self):
        markers = "\n".join([f"- Value {i}: NOT FOUND" for i in range(7)])
        content = f"## Color System\n- Primary: #AAA\n- Secondary: #BBB\n- Accent: #CCC\n{markers}\n## Typography\n- Heading font: Inter\n## Spacing\n- sm: 8px\n- md: 16px\n- lg: 24px\n## Component Patterns\n- Button\n- Card\n"
        issues = validate_ui_requirements_content(content)
        nf_issues = [i for i in issues if "NOT FOUND" in i]
        assert len(nf_issues) == 1
        assert "7" in nf_issues[0] or "Excessive" in nf_issues[0]

    def test_not_found_acceptable(self):
        markers = "\n".join([f"- Value {i}: NOT FOUND" for i in range(3)])
        content = f"## Color System\n- Primary: #AAA\n- Secondary: #BBB\n- Accent: #CCC\n{markers}\n## Typography\n- Heading font: Inter\n## Spacing\n- sm: 8px\n- md: 16px\n- lg: 24px\n## Component Patterns\n- Button\n- Card\n"
        issues = validate_ui_requirements_content(content)
        nf_issues = [i for i in issues if "NOT FOUND" in i]
        assert len(nf_issues) == 0

    def test_all_sections_empty(self):
        content = "## Color System\n\n## Typography\n\n## Spacing\n\n## Component Patterns\n"
        issues = validate_ui_requirements_content(content)
        assert len(issues) >= 4  # At least one issue per section


# ===================================================================
# 3. TestGenerateFallbackUIRequirements
# ===================================================================


class TestGenerateFallbackUIRequirements:
    """Tests for generate_fallback_ui_requirements heuristic generator."""

    def test_fintech_luxury(self):
        direction = _infer_design_direction("Build a fintech payment platform")
        assert direction == "luxury"
        assert _DIRECTION_TABLE["luxury"]["heading_font"] == "Cormorant Garamond"

    def test_developer_brutalist(self):
        direction = _infer_design_direction("developer tool CLI dashboard")
        assert direction == "brutalist"

    def test_saas_minimal(self):
        direction = _infer_design_direction("SaaS dashboard analytics")
        assert direction == "minimal_modern"

    def test_unknown_default(self):
        direction = _infer_design_direction("something random and unusual")
        assert direction == "minimal_modern"

    def test_file_output(self, tmp_path: Path):
        config = AgentTeamConfig()
        config.convergence.requirements_dir = ".agent-team"
        content = generate_fallback_ui_requirements(
            task="Build a SaaS dashboard",
            config=config,
            cwd=str(tmp_path),
        )
        output_file = tmp_path / ".agent-team" / "UI_REQUIREMENTS.md"
        assert output_file.is_file()
        disk_content = output_file.read_text(encoding="utf-8")
        assert disk_content == content
        assert "FALLBACK-GENERATED" in content

    def test_content_has_required_sections(self, tmp_path: Path):
        config = AgentTeamConfig()
        config.convergence.requirements_dir = ".agent-team"
        content = generate_fallback_ui_requirements(
            task="Build a luxury fintech dashboard",
            config=config,
            cwd=str(tmp_path),
        )
        # Validate structural sections are present (headers exist)
        from src.agent_team.design_reference import validate_ui_requirements
        missing = validate_ui_requirements(content)
        assert missing == [], f"Fallback content missing sections: {missing}"
        # Content quality: fallback should pass all quality checks
        issues = validate_ui_requirements_content(content)
        assert len(issues) == 0, f"Fallback content failed validation: {issues}"


# ===================================================================
# 4. TestRunDesignExtractionWithRetry
# ===================================================================


class TestRunDesignExtractionWithRetry:
    """Tests for run_design_extraction_with_retry retry logic."""

    def test_success_first_try(self):
        async def _test():
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                new_callable=AsyncMock,
                return_value=("content", 1.0),
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                result = await run_design_extraction_with_retry(
                    urls=["https://example.com"],
                    config=AgentTeamConfig(),
                    cwd="/tmp",
                    backend="api",
                    max_retries=2,
                    base_delay=0.01,
                )
                assert result == ("content", 1.0)

        asyncio.run(_test())

    def test_success_after_retry(self):
        async def _test():
            mock = AsyncMock(
                side_effect=[
                    DesignExtractionError("fail1"),
                    ("content-retry", 2.0),
                ]
            )
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                result = await run_design_extraction_with_retry(
                    urls=["https://example.com"],
                    config=AgentTeamConfig(),
                    cwd="/tmp",
                    backend="api",
                    max_retries=2,
                    base_delay=0.01,
                )
                assert result[0] == "content-retry"
                assert result[1] == 2.0

        asyncio.run(_test())

    def test_all_attempts_fail(self):
        async def _test():
            mock = AsyncMock(
                side_effect=DesignExtractionError("always fails")
            )
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(DesignExtractionError, match="3 attempts"):
                    await run_design_extraction_with_retry(
                        urls=["https://example.com"],
                        config=AgentTeamConfig(),
                        cwd="/tmp",
                        backend="api",
                        max_retries=2,
                        base_delay=0.01,
                    )

        asyncio.run(_test())

    def test_cost_accumulation(self):
        async def _test():
            call_count = 0

            async def _side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise DesignExtractionError("first fail")
                return ("ok", 3.5)

            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                new_callable=AsyncMock,
                side_effect=_side_effect,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                content, cost = await run_design_extraction_with_retry(
                    urls=["https://example.com"],
                    config=AgentTeamConfig(),
                    cwd="/tmp",
                    backend="api",
                    max_retries=2,
                    base_delay=0.01,
                )
                assert content == "ok"
                assert cost == 3.5

        asyncio.run(_test())

    def test_respects_max_retries(self):
        async def _test():
            mock = AsyncMock(
                side_effect=DesignExtractionError("always fails")
            )
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(DesignExtractionError):
                    await run_design_extraction_with_retry(
                        urls=["https://example.com"],
                        config=AgentTeamConfig(),
                        cwd="/tmp",
                        backend="api",
                        max_retries=0,
                        base_delay=0.01,
                    )
                # With max_retries=0, only 1 attempt total
                assert mock.call_count == 1

        asyncio.run(_test())


# ===================================================================
# 5. TestUICompliancePatterns
# ===================================================================


class TestUICompliancePatterns:
    """Tests for _check_ui_compliance regex patterns."""

    def test_hardcoded_hex_css(self):
        content = 'div { color: #FF0000; }'
        violations = _check_ui_compliance(content, "src/Button.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "UI-001" in checks

    def test_hardcoded_hex_style(self):
        content = "backgroundColor: '#FF0000'"
        violations = _check_ui_compliance(content, "src/Button.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "UI-001" in checks

    def test_tailwind_arbitrary_hex(self):
        content = '<div className="bg-[#FF0000]">'
        violations = _check_ui_compliance(content, "src/Card.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "UI-001b" in checks

    def test_default_tailwind_extended(self):
        content = '<button className="bg-indigo-500">'
        violations = _check_ui_compliance(content, "src/Hero.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "UI-002" in checks

    def test_generic_font_config(self):
        # UI-003 only fires in files that pass the _EXT_UI gate AND match
        # _RE_CONFIG_FILE. Use a .scss variables file (in _EXT_UI set).
        content = "fontFamily: Inter, sans-serif"
        violations = _check_ui_compliance(
            content, "src/theme/_variables.scss", ".scss"
        )
        checks = [v.check for v in violations]
        assert "UI-003" in checks

    def test_arbitrary_spacing(self):
        # The regex matches Tailwind utility classes like p-13, m-[13px]
        content = '<div className="p-13">'
        violations = _check_ui_compliance(content, "src/Card.tsx", ".tsx")
        checks = [v.check for v in violations]
        assert "UI-004" in checks

    def test_grid_aligned_no_violation(self):
        # 16 is on the 4px grid — no UI-004
        content = '<div className="p-16">'
        violations = _check_ui_compliance(content, "src/Card.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 0

    def test_config_file_exempt_from_colors(self):
        content = "primary: #1A1A2E"
        violations = _check_ui_compliance(
            content, "tailwind.config.ts", ".ts"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0

    def test_test_file_excluded(self):
        content = 'div { color: #FF0000; } bg-[#FF0000] bg-indigo-500'
        violations = _check_ui_compliance(
            content, "src/Button.test.tsx", ".tsx"
        )
        assert violations == []

    def test_non_ui_extension(self):
        content = 'color: #FF0000; bg-[#FF0000]'
        violations = _check_ui_compliance(content, "utils/helpers.py", ".py")
        assert violations == []


# ===================================================================
# 6. TestRunUIComplianceScan
# ===================================================================


class TestRunUIComplianceScan:
    """Tests for run_ui_compliance_scan project-level scanner."""

    def test_finds_violations(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        tsx_file = src / "Button.tsx"
        tsx_file.write_text('<div className="bg-[#FF0000]">click</div>', encoding="utf-8")
        violations = run_ui_compliance_scan(tmp_path)
        checks = [v.check for v in violations]
        assert "UI-001b" in checks

    def test_config_exempt(self, tmp_path: Path):
        config_file = tmp_path / "tailwind.config.ts"
        config_file.write_text('primary: "#1A1A2E"', encoding="utf-8")
        violations = run_ui_compliance_scan(tmp_path)
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0

    def test_test_excluded(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        test_file = src / "Button.test.tsx"
        test_file.write_text('color: #FF0000; bg-[#FF0000]', encoding="utf-8")
        violations = run_ui_compliance_scan(tmp_path)
        assert violations == []

    def test_empty_project(self, tmp_path: Path):
        violations = run_ui_compliance_scan(tmp_path)
        assert violations == []


# ===================================================================
# 7. TestConfigNewFields
# ===================================================================


class TestConfigNewFields:
    """Tests for new config fields on DesignReferenceConfig and MilestoneConfig."""

    def test_design_reference_defaults(self):
        cfg = DesignReferenceConfig()
        assert cfg.extraction_retries == 2
        assert cfg.fallback_generation is True
        assert cfg.content_quality_check is True

    def test_milestone_defaults(self):
        cfg = MilestoneConfig()
        assert cfg.ui_compliance_scan is True

    def test_dict_to_config_design_reference(self):
        data = {
            "design_reference": {
                "extraction_retries": 5,
                "fallback_generation": False,
                "content_quality_check": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.design_reference.extraction_retries == 5
        assert cfg.design_reference.fallback_generation is False
        assert cfg.design_reference.content_quality_check is False

    def test_dict_to_config_milestone(self):
        data = {
            "milestone": {
                "ui_compliance_scan": False,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.milestone.ui_compliance_scan is False

    def test_dict_to_config_defaults(self):
        cfg = _dict_to_config({})
        assert cfg.design_reference.extraction_retries == 2
        assert cfg.design_reference.fallback_generation is True
        assert cfg.design_reference.content_quality_check is True
        assert cfg.milestone.ui_compliance_scan is True

    def test_extraction_retries_zero(self):
        data = {
            "design_reference": {
                "extraction_retries": 0,
            }
        }
        cfg = _dict_to_config(data)
        assert cfg.design_reference.extraction_retries == 0


# ===================================================================
# 8. TestCodeWriterUICompliancePolicy
# ===================================================================


class TestCodeWriterUICompliancePolicy:
    """Tests that CODE_WRITER_PROMPT contains UI compliance policy text."""

    def test_contains_ui_compliance_policy(self):
        assert "UI COMPLIANCE POLICY" in CODE_WRITER_PROMPT

    def test_contains_ui_fail_rules(self):
        for i in range(1, 8):
            rule = f"UI-FAIL-{i:03d}"
            assert rule in CODE_WRITER_PROMPT, f"{rule} missing from CODE_WRITER_PROMPT"

    def test_same_severity_as_mock(self):
        assert "SAME SEVERITY AS MOCK DATA" in CODE_WRITER_PROMPT

    def test_mandatory_workflow(self):
        assert "MANDATORY WORKFLOW for UI files" in CODE_WRITER_PROMPT


# ===================================================================
# 9. TestMilestoneUIPhase
# ===================================================================


class TestMilestoneUIPhase:
    """Tests for UI enforcement in orchestrator + milestone prompts."""

    def test_orchestrator_has_step_3_7(self):
        assert "3.7." in ORCHESTRATOR_SYSTEM_PROMPT
        assert "UI DESIGN SYSTEM SETUP" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_orchestrator_has_design_requirements(self):
        assert "DESIGN-001" in ORCHESTRATOR_SYSTEM_PROMPT

    def test_milestone_prompt_has_ui_enforcement(self):
        config = AgentTeamConfig()
        prompt = build_milestone_execution_prompt(
            task="Build a dashboard",
            depth="standard",
            config=config,
        )
        assert "UI COMPLIANCE ENFORCEMENT" in prompt


# ===================================================================
# 10. TestRunUIComplianceFixCLI (GAP-1)
# ===================================================================


class TestRunUIComplianceFixCLI:
    """Tests for _run_ui_compliance_fix in cli.py."""

    def test_empty_violations_returns_zero(self):
        from src.agent_team.cli import _run_ui_compliance_fix

        async def _test():
            cost = await _run_ui_compliance_fix(
                cwd="/tmp",
                config=AgentTeamConfig(),
                ui_violations=[],
                task_text="Build a dashboard",
            )
            assert cost == 0.0

        asyncio.run(_test())

    def test_truncation_at_20(self):
        """Violations text truncates at 20 entries."""
        from src.agent_team.cli import _run_ui_compliance_fix
        from src.agent_team.quality_checks import Violation

        violations = [
            Violation(
                check=f"UI-001",
                message=f"Violation #{i}",
                file_path=f"src/File{i}.tsx",
                line=i,
                severity="warning",
            )
            for i in range(30)
        ]

        async def _test():
            with patch(
                "src.agent_team.cli.ClaudeSDKClient"
            ) as mock_cls, patch(
                "src.agent_team.cli._build_options", return_value={}
            ), patch(
                "src.agent_team.cli._process_response",
                new_callable=AsyncMock,
                return_value=1.0,
            ), patch(
                "src.agent_team.cli._backend", "api"
            ):
                mock_client = AsyncMock()
                mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

                cost = await _run_ui_compliance_fix(
                    cwd="/tmp",
                    config=AgentTeamConfig(),
                    ui_violations=violations,
                    task_text="Build a dashboard",
                )
                # Should have called query with text containing at most 20 violations
                query_arg = mock_client.query.call_args[0][0]
                # Count violation lines (each starts with "  - [UI-")
                violation_lines = [l for l in query_arg.splitlines() if l.strip().startswith("- [UI-")]
                assert len(violation_lines) == 20

        asyncio.run(_test())

    def test_sdk_exception_returns_zero(self):
        """If SDK client raises, function returns 0.0 (doesn't propagate)."""
        from src.agent_team.cli import _run_ui_compliance_fix
        from src.agent_team.quality_checks import Violation

        violations = [
            Violation(check="UI-001", message="bad color", file_path="src/A.tsx", line=1, severity="warning"),
        ]

        async def _test():
            with patch(
                "src.agent_team.cli.ClaudeSDKClient",
                side_effect=Exception("SDK failed"),
            ), patch(
                "src.agent_team.cli._build_options", return_value={}
            ), patch(
                "src.agent_team.cli._backend", "api"
            ):
                cost = await _run_ui_compliance_fix(
                    cwd="/tmp",
                    config=AgentTeamConfig(),
                    ui_violations=violations,
                    task_text="Build a dashboard",
                )
                assert cost == 0.0

        asyncio.run(_test())


# ===================================================================
# 11. TestFallbackDirectionVariants (GAP-3)
# ===================================================================


class TestFallbackDirectionVariants:
    """Tests for editorial and industrial directions in fallback generation."""

    def test_editorial_direction(self):
        direction = _infer_design_direction("Build a blog and news content platform")
        assert direction == "editorial"
        assert _DIRECTION_TABLE["editorial"]["heading_font"] == "Playfair Display"

    def test_industrial_direction(self):
        direction = _infer_design_direction("enterprise ERP logistics management")
        assert direction == "industrial"
        assert _DIRECTION_TABLE["industrial"]["primary"] == "#1E293B"

    def test_editorial_fallback_content(self, tmp_path: Path):
        config = AgentTeamConfig()
        config.convergence.requirements_dir = ".agent-team"
        content = generate_fallback_ui_requirements(
            task="Build a blog and news content platform",
            config=config,
            cwd=str(tmp_path),
        )
        assert "Playfair Display" in content
        assert "Newsreader" in content

    def test_industrial_fallback_content(self, tmp_path: Path):
        config = AgentTeamConfig()
        config.convergence.requirements_dir = ".agent-team"
        content = generate_fallback_ui_requirements(
            task="enterprise ERP logistics management",
            config=config,
            cwd=str(tmp_path),
        )
        assert "Space Grotesk" in content
        assert "#1E293B" in content


# ===================================================================
# 12. TestUIComplianceNegatives (GAP-4)
# ===================================================================


class TestUIComplianceNegatives:
    """Negative tests for UI compliance — things that should NOT be flagged."""

    def test_css_custom_property_not_flagged(self):
        """var(--color-primary) should not trigger UI-001."""
        content = "color: var(--color-primary);"
        violations = _check_ui_compliance(content, "src/Button.tsx", ".tsx")
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0

    def test_svg_hex_not_flagged_in_svg(self):
        """SVG files aren't in _EXT_UI, so hex colors in .svg shouldn't be flagged."""
        content = '<path fill="#FF0000" />'
        violations = _check_ui_compliance(content, "assets/icon.svg", ".svg")
        assert violations == []

    def test_tailwind_theme_color_not_flagged(self):
        """bg-primary (custom theme color) should not trigger UI-002."""
        content = '<div className="bg-primary text-accent">'
        violations = _check_ui_compliance(content, "src/Card.tsx", ".tsx")
        ui002 = [v for v in violations if v.check == "UI-002"]
        assert len(ui002) == 0

    def test_grid_aligned_css_spacing_not_flagged(self):
        """CSS padding: 16px (on 4px grid) should not trigger UI-004."""
        content = "padding: 16px;"
        violations = _check_ui_compliance(content, "src/Layout.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 0

    def test_zero_spacing_not_flagged(self):
        """p-0 should not trigger UI-004."""
        content = '<div className="p-0">'
        violations = _check_ui_compliance(content, "src/Box.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 0


# ===================================================================
# 13. TestAngularComponentTs (GAP-5)
# ===================================================================


class TestAngularComponentTs:
    """Test that Angular .component.ts files are scanned for UI compliance."""

    def test_component_ts_scanned(self):
        content = 'div { color: #FF0000; }'
        violations = _check_ui_compliance(
            content, "src/app/hero/hero.component.ts", ".ts"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) >= 1

    def test_regular_ts_not_scanned(self):
        """Regular .ts files (not config, not component) should be skipped."""
        content = 'div { color: #FF0000; }'
        violations = _check_ui_compliance(
            content, "src/utils/helpers.ts", ".ts"
        )
        assert violations == []


# ===================================================================
# 14. TestSplitIntoSectionsEdgeCases (GAP-6)
# ===================================================================


class TestSplitIntoSectionsEdgeCases:
    """Edge cases for _split_into_sections."""

    def test_h1_only_not_split(self):
        """Only H1 headers (# Title) should not create sections — only ## does."""
        content = "# Title\nSome intro text\n# Another Title\nMore text\n"
        result = _split_into_sections(content)
        assert result == {}

    def test_h3_only_not_split(self):
        """Only H3 headers (### Sub) should not create top-level sections."""
        content = "### Sub One\nText one\n### Sub Two\nText two\n"
        result = _split_into_sections(content)
        assert result == {}

    def test_mixed_h1_h2_h3(self):
        """H2 sections should capture H3 sub-sections inside them."""
        content = "# Doc Title\nIntro\n## Color System\n### Palette\n- Red: #F00\n## Typography\n- Font: Inter\n"
        result = _split_into_sections(content)
        assert "color system" in result
        assert "typography" in result
        assert "### Palette" in result["color system"]


# ===================================================================
# 15. TestConfigInvalidTypes (GAP-7 + HARD-2)
# ===================================================================


class TestConfigInvalidTypes:
    """Tests for _dict_to_config with invalid or edge-case values."""

    def test_negative_extraction_retries_raises(self):
        data = {"design_reference": {"extraction_retries": -1}}
        with pytest.raises(ValueError, match="extraction_retries"):
            _dict_to_config(data)

    def test_extraction_retries_zero_valid(self):
        cfg = _dict_to_config({"design_reference": {"extraction_retries": 0}})
        assert cfg.design_reference.extraction_retries == 0

    def test_extraction_retries_large_value(self):
        cfg = _dict_to_config({"design_reference": {"extraction_retries": 100}})
        assert cfg.design_reference.extraction_retries == 100


# ===================================================================
# 16. TestDirectionalSpacingVariants (HARD-3 verification)
# ===================================================================


class TestDirectionalSpacingVariants:
    """Tests for directional Tailwind spacing variants (pt-, pb-, ml-, mr-, etc.)."""

    def test_pt_flagged(self):
        content = '<div className="pt-13">'
        violations = _check_ui_compliance(content, "src/Box.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 1

    def test_mb_flagged(self):
        content = '<div className="mb-13">'
        violations = _check_ui_compliance(content, "src/Box.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 1

    def test_ml_grid_aligned_not_flagged(self):
        content = '<div className="ml-16">'
        violations = _check_ui_compliance(content, "src/Box.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 0

    def test_pr_flagged(self):
        content = '<div className="pr-13">'
        violations = _check_ui_compliance(content, "src/Box.tsx", ".tsx")
        ui004 = [v for v in violations if v.check == "UI-004"]
        assert len(ui004) == 1


# ===================================================================
# 17. TestConfigFileRegexHardening (HARD-1 verification)
# ===================================================================


class TestConfigFileRegexHardening:
    """Tests that config file regex doesn't false-positive on component names."""

    def test_theme_toggle_not_config(self):
        """ThemeToggle.tsx should NOT be treated as a config file."""
        content = "color: #FF0000;"
        violations = _check_ui_compliance(
            content, "src/components/ThemeToggle.tsx", ".tsx"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) >= 1  # Should be flagged (not exempt as config)

    def test_theme_provider_not_config(self):
        """ThemeProvider.tsx should NOT be treated as a config file."""
        content = "color: #FF0000;"
        violations = _check_ui_compliance(
            content, "src/components/ThemeProvider.tsx", ".tsx"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) >= 1

    def test_actual_theme_file_is_config(self):
        """theme.scss (bare name) should be treated as a config file."""
        content = "color: #FF0000;"
        violations = _check_ui_compliance(
            content, "src/styles/theme.scss", ".scss"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0  # Should be exempt as config

    def test_theme_subdir_is_config(self):
        """Files under a theme/ directory should be config."""
        content = "color: #FF0000;"
        violations = _check_ui_compliance(
            content, "src/theme/colors.scss", ".scss"
        )
        ui001 = [v for v in violations if v.check == "UI-001"]
        assert len(ui001) == 0  # Under theme/ dir, exempt


# ===================================================================
# 18. TestWordBoundaryDirectionInference (HARD-4 verification)
# ===================================================================


class TestWordBoundaryDirectionInference:
    """Tests that direction inference uses word boundaries."""

    def test_enterprise_matches_industrial(self):
        direction = _infer_design_direction("enterprise management platform")
        assert direction == "industrial"

    def test_enterprise_substring_no_match(self):
        """'enterprise' embedded in a larger word should still match
        (word boundary on 'enterprise' itself)."""
        direction = _infer_design_direction("Build a cool appenterprise")
        # 'enterprise' has a word boundary at 'app|enterprise' — 'p' is not
        # a word char boundary for 'enterprise' substring. But \b matches
        # between 'p' and 'e' only if they are word chars on both sides.
        # Actually \b between 'p' and 'e' does NOT fire since both are \w.
        # So this should NOT match 'enterprise' → falls back to minimal_modern.
        assert direction == "minimal_modern"

    def test_cli_keyword_word_boundary(self):
        """'cli' should match as a word, not as substring of 'clicking'."""
        direction = _infer_design_direction("Build a clicking game interface")
        assert direction != "brutalist"  # 'cli' is in 'clicking' but not at word boundary

    def test_cli_standalone_matches(self):
        direction = _infer_design_direction("Build a CLI tool for developers")
        assert direction == "brutalist"


# ===================================================================
# 19. TestUnexpectedExceptionNotRetried (CRITICAL-3 verification)
# ===================================================================


class TestUnexpectedExceptionNotRetried:
    """Verify that unexpected exceptions in retry wrapper are NOT retried."""

    def test_type_error_not_retried(self):
        async def _test():
            mock = AsyncMock(side_effect=TypeError("bad arg"))
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(DesignExtractionError, match="Unexpected error"):
                    await run_design_extraction_with_retry(
                        urls=["https://example.com"],
                        config=AgentTeamConfig(),
                        cwd="/tmp",
                        backend="api",
                        max_retries=2,
                        base_delay=0.01,
                    )
                # Should have called only once — not retried
                assert mock.call_count == 1

        asyncio.run(_test())

    def test_connection_error_is_retried(self):
        async def _test():
            mock = AsyncMock(
                side_effect=[
                    ConnectionError("conn refused"),
                    ("content-ok", 1.5),
                ]
            )
            with patch(
                "src.agent_team.design_reference.run_design_extraction",
                mock,
            ), patch("asyncio.sleep", new_callable=AsyncMock):
                result = await run_design_extraction_with_retry(
                    urls=["https://example.com"],
                    config=AgentTeamConfig(),
                    cwd="/tmp",
                    backend="api",
                    max_retries=2,
                    base_delay=0.01,
                )
                assert result[0] == "content-ok"
                assert mock.call_count == 2

        asyncio.run(_test())
