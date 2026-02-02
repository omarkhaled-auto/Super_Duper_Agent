"""Tests for agent_team.ui_standards."""

from __future__ import annotations

import pytest

from agent_team.ui_standards import UI_DESIGN_STANDARDS, load_ui_standards


# ===================================================================
# UI_DESIGN_STANDARDS constant
# ===================================================================

class TestUIDesignStandardsConstant:
    """Verify the built-in standards contain all required sections."""

    def test_content_is_non_empty(self):
        assert len(UI_DESIGN_STANDARDS) > 2000

    # --- Layer 1: Design Direction & Anti-Slop ---

    def test_has_distributional_convergence_warning(self):
        assert "DISTRIBUTIONAL CONVERGENCE" in UI_DESIGN_STANDARDS

    def test_has_design_direction_requirement(self):
        assert "DESIGN DIRECTION REQUIREMENT" in UI_DESIGN_STANDARDS

    def test_has_typography_section(self):
        assert "TYPOGRAPHY" in UI_DESIGN_STANDARDS
        assert "DISTINCTIVE" in UI_DESIGN_STANDARDS

    # --- Layer 2: Quality Framework ---

    def test_has_spacing_system(self):
        assert "SPACING SYSTEM" in UI_DESIGN_STANDARDS
        assert "8px" in UI_DESIGN_STANDARDS

    def test_has_color_system(self):
        assert "COLOR SYSTEM" in UI_DESIGN_STANDARDS

    def test_has_component_patterns(self):
        assert "COMPONENT PATTERNS" in UI_DESIGN_STANDARDS

    def test_has_component_state_completeness(self):
        assert "COMPONENT STATE COMPLETENESS" in UI_DESIGN_STANDARDS

    def test_has_layout_patterns(self):
        assert "LAYOUT PATTERNS" in UI_DESIGN_STANDARDS

    def test_has_motion_animation(self):
        assert "MOTION" in UI_DESIGN_STANDARDS

    def test_has_accessibility(self):
        assert "ACCESSIBILITY" in UI_DESIGN_STANDARDS
        assert "WCAG" in UI_DESIGN_STANDARDS

    def test_has_framework_adaptive_notes(self):
        assert "FRAMEWORK-ADAPTIVE" in UI_DESIGN_STANDARDS

    # --- Anti-patterns: SLOP-001 through SLOP-015 ---

    def test_has_all_15_slop_codes(self):
        for i in range(1, 16):
            code = f"SLOP-{i:03d}"
            assert code in UI_DESIGN_STANDARDS, f"Missing {code}"

    def test_has_focus_reference(self):
        assert "focus" in UI_DESIGN_STANDARDS.lower()

    def test_has_framework_mentions(self):
        assert "Tailwind" in UI_DESIGN_STANDARDS
        assert "shadcn" in UI_DESIGN_STANDARDS
        assert "CSS custom properties" in UI_DESIGN_STANDARDS

    def test_has_font_alternatives(self):
        assert "Playfair Display" in UI_DESIGN_STANDARDS
        assert "Cabinet Grotesk" in UI_DESIGN_STANDARDS
        assert "Bricolage Grotesque" in UI_DESIGN_STANDARDS

    def test_has_never_font_list(self):
        assert "NEVER" in UI_DESIGN_STANDARDS
        assert "Inter" in UI_DESIGN_STANDARDS
        assert "Roboto" in UI_DESIGN_STANDARDS
        assert "Arial" in UI_DESIGN_STANDARDS

    def test_has_component_states(self):
        for state in ("hover", "focus", "loading", "error", "empty"):
            assert state.lower() in UI_DESIGN_STANDARDS.lower(), f"Missing state: {state}"

    def test_has_copy_quality_guidelines(self):
        assert "COPY" in UI_DESIGN_STANDARDS
        assert "error messages" in UI_DESIGN_STANDARDS.lower()
        assert "empty states" in UI_DESIGN_STANDARDS.lower()


# ===================================================================
# load_ui_standards()
# ===================================================================

class TestLoadUIStandards:
    def test_empty_string_returns_builtin(self):
        result = load_ui_standards("")
        assert result == UI_DESIGN_STANDARDS

    def test_no_arg_returns_builtin(self):
        result = load_ui_standards()
        assert result == UI_DESIGN_STANDARDS

    def test_valid_custom_file(self, tmp_path):
        custom = tmp_path / "custom-standards.md"
        custom.write_text("MY CUSTOM DESIGN RULES", encoding="utf-8")
        result = load_ui_standards(str(custom))
        assert result == "MY CUSTOM DESIGN RULES"

    def test_missing_file_falls_back_to_builtin(self, tmp_path):
        result = load_ui_standards(str(tmp_path / "nonexistent.md"))
        assert result == UI_DESIGN_STANDARDS

    def test_directory_path_falls_back_to_builtin(self, tmp_path):
        result = load_ui_standards(str(tmp_path))
        assert result == UI_DESIGN_STANDARDS

    def test_custom_file_content_is_stripped(self, tmp_path):
        custom = tmp_path / "padded.md"
        custom.write_text("\n  CUSTOM RULES  \n\n", encoding="utf-8")
        result = load_ui_standards(str(custom))
        assert result == "CUSTOM RULES"
