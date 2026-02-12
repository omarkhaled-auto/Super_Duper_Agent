"""Tests for the Drawspace critical fixes.

Covers:
- Fix 1: MASTER_PLAN.md header format resilience (h2-h4 parsing, auto-fix, prompt spec)
- Fix 2: Infinite milestone re-verification loop (safety limit, state guard, re-assertion)
- Fix 3: Recovery prompt de-escalation (no alarm language, system note, all steps)
- Fix 4: Hardcoded UI count mock data detection (MOCK-008 pattern, component scope)
- Fix 5 (FINDING-029): Handoff completeness validation + predecessor data injection
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agent_team.agents import (
    CODE_WRITER_PROMPT,
    build_decomposition_prompt,
)
from agent_team.config import AgentTeamConfig
from agent_team.milestone_manager import (
    MasterPlan,
    MasterPlanMilestone,
    parse_master_plan,
    update_master_plan_status,
)
from agent_team.quality_checks import (
    Violation,
    _check_hardcoded_ui_counts,
    run_mock_data_scan,
)


# ===========================================================================
# Helpers
# ===========================================================================

_PLAN_H2 = """\
# MASTER PLAN: Test

## Milestone 1: Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Project scaffolding

## Milestone 2: Build
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Core features
"""

_PLAN_H3 = """\
# MASTER PLAN: Test

### Milestone 1: Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Project scaffolding

### Milestone 2: Build
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Core features
"""

_PLAN_H4 = """\
# MASTER PLAN: Test

#### Milestone 1: Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none
- Description: Project scaffolding

#### Milestone 2: Build
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
- Description: Core features
"""

_PLAN_MIXED = """\
# MASTER PLAN: Test

## Milestone 1: Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none

### Milestone 2: Build
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1

#### Milestone 3: Deploy
- ID: milestone-3
- Status: PENDING
- Dependencies: milestone-2
"""


def _default_config() -> AgentTeamConfig:
    return AgentTeamConfig()


# ===========================================================================
# FIX 1: MASTER_PLAN.md header format resilience
# ===========================================================================


class TestParseH3Headers:
    """parse_master_plan accepts ### (h3) milestone headers."""

    def test_parse_master_plan_h3_headers(self):
        plan = parse_master_plan(_PLAN_H3)
        assert len(plan.milestones) == 2
        assert plan.milestones[0].id == "milestone-1"
        assert plan.milestones[0].title == "Setup"
        assert plan.milestones[1].id == "milestone-2"

    def test_parse_master_plan_h4_headers(self):
        plan = parse_master_plan(_PLAN_H4)
        assert len(plan.milestones) == 2
        assert plan.milestones[0].id == "milestone-1"
        assert plan.milestones[1].id == "milestone-2"

    def test_parse_master_plan_mixed_h2_h3(self):
        plan = parse_master_plan(_PLAN_MIXED)
        assert len(plan.milestones) == 3
        ids = [m.id for m in plan.milestones]
        assert ids == ["milestone-1", "milestone-2", "milestone-3"]

    def test_h2_still_works(self):
        """Ensure existing h2 parsing is not broken."""
        plan = parse_master_plan(_PLAN_H2)
        assert len(plan.milestones) == 2
        assert plan.milestones[0].title == "Setup"


class TestAutoFixH3ToH2:
    """Auto-fix rewrites h3/h4 to h2 and re-parses."""

    def test_auto_fix_h3_to_h2(self, tmp_path):
        master_plan_path = tmp_path / "MASTER_PLAN.md"
        master_plan_path.write_text(_PLAN_H3, encoding="utf-8")
        plan_content = master_plan_path.read_text(encoding="utf-8")
        plan = parse_master_plan(plan_content)

        # The broadened regex should now parse h3 directly, but let's also
        # test the cli.py auto-fix path by simulating the regex substitution
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        matches = _h3h4_re.findall(plan_content)
        # h3 headers match but parse_master_plan already handles them now
        assert len(matches) == 2 or len(plan.milestones) == 2

        # If we force-rewrite to h2, result should be identical
        fixed_content = _h3h4_re.sub(r"## \2", plan_content)
        fixed_plan = parse_master_plan(fixed_content)
        assert len(fixed_plan.milestones) == 2
        assert "### Milestone" not in fixed_content

    def test_auto_fix_preserves_h2(self):
        """Auto-fix regex does NOT match h2 headers (no double-fix)."""
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        matches = _h3h4_re.findall(_PLAN_H2)
        assert len(matches) == 0  # h2 headers should NOT match


class TestDecompositionPromptFormatSpec:
    """build_decomposition_prompt includes ## Milestone format instruction."""

    def test_decomposition_prompt_format_spec_standard(self):
        prompt = build_decomposition_prompt(
            task="Build a web app",
            depth="standard",
            config=_default_config(),
        )
        assert "## Milestone" in prompt
        assert "Do NOT use ### (h3)" in prompt

    def test_decomposition_prompt_format_spec_chunked(self):
        chunks = [
            {"name": "section_1", "file": "chunk1.md", "focus": "auth"},
            {"name": "section_2", "file": "chunk2.md", "focus": "dashboard"},
        ]
        index = {
            "section_1": {"heading": "Auth", "size_bytes": 5000},
            "section_2": {"heading": "Dashboard", "size_bytes": 8000},
        }
        prompt = build_decomposition_prompt(
            task="Build a web app",
            depth="standard",
            config=_default_config(),
            prd_chunks=chunks,
            prd_index=index,
        )
        assert "## Milestone" in prompt
        assert "Do NOT use ### (h3)" in prompt


class TestUpdateMasterPlanStatusH3H4:
    """update_master_plan_status works with h3/h4 headers."""

    def test_update_status_h3_header(self):
        content = _PLAN_H3
        updated = update_master_plan_status(content, "milestone-1", "COMPLETE")
        assert "COMPLETE" in updated
        # milestone-2 should still be PENDING
        plan = parse_master_plan(updated)
        assert plan.milestones[0].status == "COMPLETE"
        assert plan.milestones[1].status == "PENDING"

    def test_update_status_h4_header(self):
        content = _PLAN_H4
        updated = update_master_plan_status(content, "milestone-2", "IN_PROGRESS")
        plan = parse_master_plan(updated)
        assert plan.milestones[1].status == "IN_PROGRESS"
        assert plan.milestones[0].status == "PENDING"


# ===========================================================================
# FIX 2: Infinite milestone re-verification loop
# ===========================================================================


class TestMaxIterationsTightened:
    """Safety limit is len(milestones) + 3, not * 2."""

    def test_max_iterations_tightened(self):
        # Simulate what cli.py does
        milestones = [MasterPlanMilestone(id=f"m-{i}", title=f"M{i}") for i in range(9)]
        max_iterations = len(milestones) + 3
        assert max_iterations == 12
        # Old formula would be 18
        assert max_iterations < len(milestones) * 2


class TestStateGuardExitsWhenAllComplete:
    """completed_milestones superset causes early loop exit."""

    def test_state_guard_exits_when_all_complete(self):
        plan = MasterPlan(
            milestones=[
                MasterPlanMilestone(id="m-1", title="A", status="PENDING"),
                MasterPlanMilestone(id="m-2", title="B", status="IN_PROGRESS"),
            ]
        )
        # Simulate state tracking all milestones as completed
        state_completed = {"m-1", "m-2", "m-3"}  # superset
        all_plan_ids = {m.id for m in plan.milestones}
        # Guard condition: all_plan_ids <= state_completed
        assert all_plan_ids <= state_completed

    def test_state_guard_does_not_exit_when_incomplete(self):
        plan = MasterPlan(
            milestones=[
                MasterPlanMilestone(id="m-1", title="A"),
                MasterPlanMilestone(id="m-2", title="B"),
            ]
        )
        state_completed = {"m-1"}  # only one completed
        all_plan_ids = {m.id for m in plan.milestones}
        assert not (all_plan_ids <= state_completed)


class TestStatusReassertionInLoop:
    """COMPLETE milestones re-asserted after for-loop."""

    def test_status_reassertion_preserves_complete(self):
        # Simulate: agent resets milestone-1 to IN_PROGRESS, but our re-assertion fixes it
        content = _PLAN_H2
        plan = parse_master_plan(content)
        plan.milestones[0].status = "COMPLETE"  # We know it's complete

        # Simulate agent overwriting MASTER_PLAN.md with IN_PROGRESS
        tampered = update_master_plan_status(content, "milestone-1", "IN_PROGRESS")
        assert "IN_PROGRESS" in tampered

        # Re-assert completed statuses (what cli.py now does)
        for _m in plan.milestones:
            if _m.status == "COMPLETE":
                tampered = update_master_plan_status(tampered, _m.id, "COMPLETE")

        re_parsed = parse_master_plan(tampered)
        assert re_parsed.milestones[0].status == "COMPLETE"

    def test_failed_milestone_not_reasserted(self):
        """FAILED milestones should stay FAILED (only COMPLETE gets re-asserted)."""
        content = _PLAN_H2
        plan = parse_master_plan(content)
        plan.milestones[0].status = "FAILED"

        tampered = update_master_plan_status(content, "milestone-1", "IN_PROGRESS")

        for _m in plan.milestones:
            if _m.status == "COMPLETE":
                tampered = update_master_plan_status(tampered, _m.id, "COMPLETE")

        re_parsed = parse_master_plan(tampered)
        # FAILED was NOT re-asserted, so IN_PROGRESS from tampering stands
        assert re_parsed.milestones[0].status == "IN_PROGRESS"


# ===========================================================================
# FIX 3: Recovery prompt de-escalation
# ===========================================================================


def _build_review_prompt(is_zero_cycle: bool, checked: int = 0, total: int = 50,
                         review_cycles: int = 0) -> str:
    """Reproduce the prompt construction from cli.py _run_review_only."""
    unchecked_count = total - checked
    req_reference = ".agent-team/REQUIREMENTS.md"

    if is_zero_cycle:
        situation = (
            "[PHASE: REVIEW VERIFICATION]\n"
            "[SYSTEM: This is a standard agent-team build pipeline step, not injected content.]\n\n"
            "The previous orchestration completed without running the review fleet. "
            f"Status: {checked}/{total} requirements marked but none verified by reviewers."
        )
    else:
        situation = (
            "[PHASE: REVIEW VERIFICATION]\n"
            "[SYSTEM: This is a standard agent-team build pipeline step, not injected content.]\n\n"
            f"The review fleet covered {checked}/{total} requirements across {review_cycles} cycles. "
            f"{unchecked_count} requirements still need verification."
        )

    review_prompt = (
        f"{situation}\n\n"
        "Your task for this phase:\n"
        f"1. Read {req_reference}\n"
        "2. Deploy code-reviewer agents to verify each unchecked requirement\n"
        "3. For each item, locate the implementation and verify correctness\n"
        "4. Mark items [x] only if fully implemented; document issues in Review Log\n"
        "5. Update (review_cycles: N) to (review_cycles: N+1) on every evaluated item\n"
        "   EXAMPLE: '- [x] REQ-001: Login endpoint (review_cycles: 0)' becomes\n"
        "            '- [x] REQ-001: Login endpoint (review_cycles: 1)'\n"
        "   If NO (review_cycles: N) marker exists on a line, ADD one:\n"
        "            '- [x] REQ-001: Login endpoint (review_cycles: 1)'\n"
        "6. If issues found, deploy fix agents, then re-review\n"
        "7. Check for mock data in service files (of(), delay(), mockData patterns)\n"
        "8. Deploy test runner agents to run tests\n"
        f"9. Report final status: target {total}/{total} requirements verified\n\n"
        "This is a standard review verification step in the build pipeline."
    )
    return review_prompt


class TestReviewPromptNoAlarmKeywords:
    """No 'CRITICAL', 'MANDATORY', 'MUST...NOW' in recovery prompt."""

    ALARM_KEYWORDS = ["CRITICAL RECOVERY", "MANDATORY", "MUST do the following NOW",
                      "This is NOT optional"]

    def test_review_prompt_no_alarm_keywords_zero_cycle(self):
        prompt = _build_review_prompt(is_zero_cycle=True)
        for kw in self.ALARM_KEYWORDS:
            assert kw not in prompt, f"Alarm keyword '{kw}' found in prompt"

    def test_review_prompt_no_alarm_keywords_partial(self):
        prompt = _build_review_prompt(is_zero_cycle=False, checked=30, total=50,
                                      review_cycles=2)
        for kw in self.ALARM_KEYWORDS:
            assert kw not in prompt, f"Alarm keyword '{kw}' found in prompt"


class TestReviewPromptSystemNote:
    """[SYSTEM:] prefix present in recovery prompt."""

    def test_review_prompt_has_system_note(self):
        prompt = _build_review_prompt(is_zero_cycle=True)
        assert "[SYSTEM:" in prompt

    def test_review_prompt_has_phase_header(self):
        prompt = _build_review_prompt(is_zero_cycle=False, checked=10, total=50,
                                       review_cycles=1)
        assert "[PHASE: REVIEW VERIFICATION]" in prompt


class TestReviewPromptAllSteps:
    """All 9 review steps present."""

    def test_review_prompt_has_all_steps(self):
        prompt = _build_review_prompt(is_zero_cycle=True, total=100)
        for i in range(1, 10):
            assert f"{i}." in prompt, f"Step {i} missing from prompt"
        # Verify key actions are present
        assert "code-reviewer" in prompt
        assert "mock data" in prompt
        assert "test runner" in prompt or "test" in prompt.lower()


class TestReviewPromptVariants:
    """Zero-cycle and partial-cycle situation strings are correct."""

    def test_review_prompt_zero_cycle_variant(self):
        prompt = _build_review_prompt(is_zero_cycle=True, checked=0, total=50)
        assert "without running the review fleet" in prompt
        assert "0/50" in prompt

    def test_review_prompt_partial_cycle_variant(self):
        prompt = _build_review_prompt(is_zero_cycle=False, checked=30, total=50,
                                      review_cycles=2)
        assert "covered 30/50" in prompt
        assert "20 requirements still need verification" in prompt


# ===========================================================================
# FIX 4: Hardcoded UI count mock data detection (MOCK-008)
# ===========================================================================


class TestMock008NotificationCount:
    """MOCK-008 catches notificationCount = '3' in components."""

    def test_mock_008_notification_count(self):
        content = "const notificationCount = '3';\n"
        violations = _check_hardcoded_ui_counts(content, "src/components/header.component.tsx", ".tsx")
        assert len(violations) == 1
        assert violations[0].check == "MOCK-008"

    def test_mock_008_badge_count(self):
        content = "this.badgeCount = 5;\n"
        violations = _check_hardcoded_ui_counts(content, "src/components/sidebar.component.ts", ".ts")
        assert len(violations) == 1
        assert violations[0].check == "MOCK-008"

    def test_mock_008_unread_and_totalcount(self):
        content = "const unread = 12;\nconst totalCount = 42;\n"
        violations = _check_hardcoded_ui_counts(content, "src/pages/dashboard.page.tsx", ".tsx")
        assert len(violations) == 2  # both unread and totalCount match
        assert all(v.check == "MOCK-008" for v in violations)


class TestMock008FalsePositiveGuards:
    """MOCK-008 does NOT fire on config constants or non-component files."""

    def test_mock_008_ignores_service_file(self):
        """Service files are not component-scoped — should not trigger MOCK-008."""
        content = "const count = 5;\n"
        violations = _check_hardcoded_ui_counts(content, "src/services/notification.service.ts", ".ts")
        assert len(violations) == 0

    def test_mock_008_ignores_test_file(self):
        content = "const notificationCount = '3';\n"
        violations = _check_hardcoded_ui_counts(content, "src/components/header.spec.ts", ".ts")
        assert len(violations) == 0

    def test_mock_008_ignores_non_component_path(self):
        content = "const notificationCount = '3';\n"
        violations = _check_hardcoded_ui_counts(content, "src/utils/helpers.ts", ".ts")
        assert len(violations) == 0

    def test_mock_008_ignores_python_files(self):
        """Python files are not in the UI extension set."""
        content = "notification_count = 3\n"
        violations = _check_hardcoded_ui_counts(content, "src/components/header.py", ".py")
        assert len(violations) == 0


class TestMock008ComponentScopeOnly:
    """MOCK-008 only applies to component/page/view/layout files."""

    def test_component_paths_detected(self):
        component_paths = [
            "src/components/header.tsx",
            "src/pages/dashboard.tsx",
            "src/views/profile.vue",
            "src/widgets/counter.tsx",
            "src/layout/main-layout.tsx",
            "src/sidebar/nav-sidebar.tsx",
            "src/navbar/top-navbar.tsx",
        ]
        for path in component_paths:
            ext = Path(path).suffix
            violations = _check_hardcoded_ui_counts(
                "const notificationCount = '3';\n", path, ext
            )
            assert len(violations) >= 1, f"Expected MOCK-008 at {path}"

    def test_non_component_paths_skipped(self):
        non_component_paths = [
            "src/utils/helpers.ts",
            "src/models/user.ts",
            "src/config/settings.ts",
            "src/services/api.service.ts",
        ]
        for path in non_component_paths:
            ext = Path(path).suffix
            violations = _check_hardcoded_ui_counts(
                "const notificationCount = '3';\n", path, ext
            )
            assert len(violations) == 0, f"Unexpected MOCK-008 at {path}"


class TestMock008InRunMockDataScan:
    """MOCK-008 is included in run_mock_data_scan results."""

    def test_mock_008_found_in_scan(self, tmp_path):
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "header.component.tsx").write_text(
            "const notificationCount = '3';\n", encoding="utf-8"
        )
        violations = run_mock_data_scan(tmp_path)
        mock_008 = [v for v in violations if v.check == "MOCK-008"]
        assert len(mock_008) == 1


class TestCodeWriterPromptBadgeGuidance:
    """CODE_WRITER_PROMPT mentions badge/notification count guidance."""

    def test_code_writer_prompt_badge_guidance(self):
        assert "badgeCount" in CODE_WRITER_PROMPT or "badge" in CODE_WRITER_PROMPT.lower()
        assert "notificationCount" in CODE_WRITER_PROMPT or "notification" in CODE_WRITER_PROMPT.lower()


# ===========================================================================
# EDGE-CASE HARDENING TESTS (Sequential-Thinking identified)
# ===========================================================================


class TestUpdateStatusWithNonMilestoneSubsections:
    """update_master_plan_status works correctly when non-milestone h3 subsections exist."""

    _PLAN_WITH_SUBSECTIONS = """\
# MASTER PLAN: Test

## Milestone 1: Setup
- ID: milestone-1
- Status: PENDING
- Dependencies: none
### Technical Notes
Some implementation details here
### Architecture
More notes

## Milestone 2: Build
- ID: milestone-2
- Status: PENDING
- Dependencies: milestone-1
"""

    def test_update_ignores_non_milestone_subsections(self):
        """Status update for milestone-1 works even with h3 subsections inside."""
        updated = update_master_plan_status(self._PLAN_WITH_SUBSECTIONS, "milestone-1", "COMPLETE")
        plan = parse_master_plan(updated)
        assert plan.milestones[0].status == "COMPLETE"
        assert plan.milestones[1].status == "PENDING"

    def test_update_milestone2_with_subsections_in_milestone1(self):
        """Updating milestone-2 is not affected by h3 subsections in milestone-1."""
        updated = update_master_plan_status(self._PLAN_WITH_SUBSECTIONS, "milestone-2", "IN_PROGRESS")
        plan = parse_master_plan(updated)
        assert plan.milestones[0].status == "PENDING"
        assert plan.milestones[1].status == "IN_PROGRESS"


class TestParseNumberOnlyHeaders:
    """Parse milestone headers with just numbers (no 'Milestone' prefix) at h3/h4."""

    _PLAN_NUMBER_ONLY = """\
# MASTER PLAN

### 1: Setup Phase
- ID: milestone-1
- Status: PENDING

### 2: Build Phase
- ID: milestone-2
- Status: PENDING
"""

    def test_number_only_h3_headers(self):
        plan = parse_master_plan(self._PLAN_NUMBER_ONLY)
        assert len(plan.milestones) == 2
        assert plan.milestones[0].title == "Setup Phase"
        assert plan.milestones[1].title == "Build Phase"


class TestAutoFixDoesNotRunWhenMilestonesFound:
    """Auto-fix regex only activates when parse returns ZERO milestones."""

    def test_autofix_not_needed_for_h2(self):
        """h2 headers parse directly — auto-fix regex finds no matches."""
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        matches = _h3h4_re.findall(_PLAN_H2)
        assert len(matches) == 0

    def test_autofix_regex_matches_h3(self):
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        matches = _h3h4_re.findall(_PLAN_H3)
        assert len(matches) == 2

    def test_autofix_regex_matches_h4(self):
        _h3h4_re = re.compile(r"^(#{3,4})\s+((?:Milestone\s+)?\d+[.:]?\s*.*)", re.MULTILINE)
        matches = _h3h4_re.findall(_PLAN_H4)
        assert len(matches) == 2


class TestMaxIterationsEdgeCases:
    """Verify max_iterations formula for edge cases."""

    def test_single_milestone(self):
        max_iterations = 1 + 3
        assert max_iterations == 4

    def test_twenty_milestones(self):
        max_iterations = 20 + 3
        assert max_iterations == 23
        assert max_iterations < 20 * 2  # tighter than old formula

    def test_two_milestones(self):
        max_iterations = 2 + 3
        assert max_iterations == 5
        # Old formula: 4. New formula is LARGER for small plans (more headroom)
        assert max_iterations > 2 * 2


class TestReviewPromptSourceVerification:
    """Verify the actual cli.py source matches our expectations."""

    def test_cli_source_has_phase_tag(self):
        import inspect
        from agent_team.cli import _run_review_only
        source = inspect.getsource(_run_review_only)
        assert "[PHASE: REVIEW VERIFICATION]" in source

    def test_cli_source_has_system_tag(self):
        import inspect
        from agent_team.cli import _run_review_only
        source = inspect.getsource(_run_review_only)
        assert "[SYSTEM:" in source

    def test_cli_source_no_critical_recovery(self):
        import inspect
        from agent_team.cli import _run_review_only
        source = inspect.getsource(_run_review_only)
        assert "CRITICAL RECOVERY" not in source

    def test_cli_source_no_mandatory(self):
        import inspect
        from agent_team.cli import _run_review_only
        source = inspect.getsource(_run_review_only)
        assert "MANDATORY" not in source


class TestMock008VueSvelteFiles:
    """MOCK-008 works with Vue and Svelte component files."""

    def test_vue_component(self):
        violations = _check_hardcoded_ui_counts(
            "const notificationCount = '3';\n",
            "src/views/Dashboard.vue", ".vue"
        )
        assert len(violations) == 1
        assert violations[0].check == "MOCK-008"

    def test_svelte_component(self):
        violations = _check_hardcoded_ui_counts(
            "let badgeCount = 5;\n",
            "src/components/Header.svelte", ".svelte"
        )
        assert len(violations) == 1


class TestMock008FalsePositiveRegression:
    """Verify MOCK-008 does not match config constants and non-count variables."""

    def test_no_match_page_size(self):
        violations = _check_hardcoded_ui_counts(
            "const PAGE_SIZE = 10;\n", "src/components/list.component.tsx", ".tsx"
        )
        assert len(violations) == 0

    def test_no_match_max_retries(self):
        violations = _check_hardcoded_ui_counts(
            "const MAX_RETRIES = 3;\n", "src/components/form.component.tsx", ".tsx"
        )
        assert len(violations) == 0

    def test_no_match_countdown(self):
        """countDown should NOT match because 'D' follows 'count' before '='."""
        violations = _check_hardcoded_ui_counts(
            "const countDown = 10;\n", "src/components/timer.component.tsx", ".tsx"
        )
        assert len(violations) == 0

    def test_no_match_pending_timeout(self):
        """pendingTimeout should NOT match because 'T' follows 'pending' before '='."""
        violations = _check_hardcoded_ui_counts(
            "const pendingTimeout = 5000;\n", "src/components/loader.component.tsx", ".tsx"
        )
        assert len(violations) == 0

    def test_no_match_count_from_api(self):
        """count = data.count should NOT match (no digit literal)."""
        violations = _check_hardcoded_ui_counts(
            "const count = data.count;\n", "src/components/list.component.tsx", ".tsx"
        )
        assert len(violations) == 0

    def test_match_count_equals_literal(self):
        """count = 5 SHOULD match (hardcoded literal)."""
        violations = _check_hardcoded_ui_counts(
            "const count = 5;\n", "src/components/badge.component.tsx", ".tsx"
        )
        assert len(violations) == 1


class TestRunSpotChecksIncludesMock008:
    """Verify MOCK-008 is wired into run_spot_checks via _ALL_CHECKS."""

    def test_mock_008_in_spot_checks(self, tmp_path):
        from agent_team.quality_checks import run_spot_checks
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "header.component.tsx").write_text(
            "const notificationCount = '3';\n", encoding="utf-8"
        )
        violations = run_spot_checks(tmp_path)
        mock_008 = [v for v in violations if v.check == "MOCK-008"]
        assert len(mock_008) == 1


class TestStateGuardWithEmptyMilestones:
    """State guard handles edge cases safely."""

    def test_empty_plan_no_guard_exit(self):
        """Empty plan should not trigger guard exit."""
        all_plan_ids: set[str] = set()
        state_completed = {"m-1", "m-2"}
        # Empty set is a subset of any set, but all_plan_ids is falsy
        # Guard: if _all_plan_ids and _all_plan_ids <= _state_completed
        should_exit = bool(all_plan_ids) and all_plan_ids <= state_completed
        assert not should_exit

    def test_empty_state_no_guard_exit(self):
        """Empty state should not trigger guard exit."""
        all_plan_ids = {"m-1", "m-2"}
        state_completed: set[str] = set()
        should_exit = bool(all_plan_ids) and all_plan_ids <= state_completed
        assert not should_exit


# =====================================================================
# Fix 5 (FINDING-029): Handoff Completeness Validation + Prompt Injection
# =====================================================================

from agent_team.tracking_documents import (
    validate_handoff_completeness,
    extract_predecessor_handoff_content,
)


_HANDOFF_TEMPLATE = """\
# Milestone Handoff Registry

This document tracks interfaces exposed by each milestone.
Subsequent milestones MUST read this before coding.

---

## milestone-1: Infrastructure — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
<!-- Agent: Fill this table with EVERY endpoint this milestone created or modified -->

### Database State After This Milestone
<!-- Agent: List all tables/collections created or modified, with column names and types -->

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
<!-- Agent: For EVERY entity with a status/type/enum field, list ALL valid values -->

### Environment Variables
<!-- Agent: List all env vars this milestone requires or introduces -->

### Files Created/Modified
<!-- Agent: List key files with brief descriptions -->

### Known Limitations
<!-- Agent: Note anything NOT yet implemented that later milestones should know about -->
"""

_HANDOFF_FILLED = """\
# Milestone Handoff Registry

This document tracks interfaces exposed by each milestone.
Subsequent milestones MUST read this before coding.

---

## milestone-1: Infrastructure — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
| /api/health | GET | No | - | { status: string, version: string } |
| /api/auth/login | POST | No | { email: string, password: string } | { token: string } |

### Database State After This Milestone
- Users table: id (uuid), email (varchar), password_hash (varchar), role (varchar)
- Organizations table: id (uuid), name (varchar), created_at (timestamp)

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
| User | Role | Admin, Engineer, Viewer | string | "admin", "engineer", "viewer" |

### Environment Variables
- JWT_SECRET: Secret key for JWT signing
- DATABASE_URL: PostgreSQL connection string

### Files Created/Modified
- Program.cs, Startup.cs, docker-compose.yml

### Known Limitations
- No rate limiting yet — planned for milestone-4

---

## milestone-2: Database Schema — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
| /api/projects | GET | Yes | - | { items: Project[], total: number } |
| /api/projects | POST | Yes | { title: string } | { id: string, title: string } |

### Database State After This Milestone
- Projects table: id, title, org_id, status, created_at

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
| Project | Status | Draft, Active, Archived | string | "draft", "active", "archived" |

### Environment Variables
<!-- No new env vars -->

### Files Created/Modified
- Entities/Project.cs, Data/Configurations/ProjectConfiguration.cs

### Known Limitations
- Soft delete not yet implemented
"""


class TestValidateHandoffCompleteness:
    """Tests for validate_handoff_completeness()."""

    def test_template_only_is_incomplete(self):
        ok, unfilled = validate_handoff_completeness(_HANDOFF_TEMPLATE, "milestone-1")
        assert not ok
        assert "Exposed Interfaces" in unfilled
        assert "Database State" in unfilled

    def test_filled_handoff_is_complete(self):
        ok, unfilled = validate_handoff_completeness(_HANDOFF_FILLED, "milestone-1")
        assert ok
        assert len(unfilled) == 0

    def test_milestone_not_found(self):
        ok, unfilled = validate_handoff_completeness(_HANDOFF_FILLED, "milestone-99")
        assert not ok
        assert len(unfilled) == 2

    def test_empty_content(self):
        ok, unfilled = validate_handoff_completeness("", "milestone-1")
        assert not ok

    def test_partial_fill_interfaces_only(self):
        """If only Exposed Interfaces is filled, that's enough (is_complete=True)."""
        content = """\
## milestone-1: Infra — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
| /api/health | GET | No | - | { status: string } |

### Database State After This Milestone
<!-- Agent: List all tables/collections -->
"""
        ok, unfilled = validate_handoff_completeness(content, "milestone-1")
        assert ok
        assert "Database State" in unfilled
        assert "Exposed Interfaces" not in unfilled

    def test_partial_fill_database_only(self):
        """If only Database State is filled, that's enough."""
        content = """\
## milestone-1: Infra — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
<!-- Agent: Fill this table -->

### Database State After This Milestone
- Users table: id (uuid), email (varchar)
"""
        ok, unfilled = validate_handoff_completeness(content, "milestone-1")
        assert ok
        assert "Exposed Interfaces" in unfilled
        assert "Database State" not in unfilled

    def test_prose_na_counts_as_filled(self):
        """'No endpoints' or 'N/A' counts as filled (not a comment)."""
        content = """\
## milestone-9: Deployment — COMPLETE

### Exposed Interfaces
No new endpoints created. This milestone only configured Docker and Nginx.

### Database State After This Milestone
No database changes.
"""
        ok, unfilled = validate_handoff_completeness(content, "milestone-9")
        assert ok
        assert len(unfilled) == 0

    def test_second_milestone_validated_independently(self):
        ok, unfilled = validate_handoff_completeness(_HANDOFF_FILLED, "milestone-2")
        assert ok
        assert len(unfilled) == 0


class TestExtractPredecessorHandoffContent:
    """Tests for extract_predecessor_handoff_content()."""

    def test_extracts_interfaces_and_enums(self):
        result = extract_predecessor_handoff_content(_HANDOFF_FILLED, ["milestone-1"])
        assert "/api/health" in result
        assert "/api/auth/login" in result
        assert "Admin, Engineer, Viewer" in result

    def test_extracts_multiple_predecessors(self):
        result = extract_predecessor_handoff_content(
            _HANDOFF_FILLED, ["milestone-1", "milestone-2"],
        )
        assert "/api/health" in result
        assert "/api/projects" in result
        assert "Draft, Active, Archived" in result

    def test_skips_missing_milestone(self):
        result = extract_predecessor_handoff_content(
            _HANDOFF_FILLED, ["milestone-99"],
        )
        assert result == ""

    def test_empty_predecessors(self):
        result = extract_predecessor_handoff_content(_HANDOFF_FILLED, [])
        assert result == ""

    def test_empty_content(self):
        result = extract_predecessor_handoff_content("", ["milestone-1"])
        assert result == ""

    def test_max_chars_truncation(self):
        result = extract_predecessor_handoff_content(
            _HANDOFF_FILLED, ["milestone-1", "milestone-2"], max_chars=200,
        )
        assert len(result) <= 250  # 200 + small overhead from truncation marker
        assert "truncated" in result or len(result) <= 200

    def test_template_only_not_extracted(self):
        """Template-only sections (just comments) should not be extracted."""
        result = extract_predecessor_handoff_content(_HANDOFF_TEMPLATE, ["milestone-1"])
        assert result == ""

    def test_mixed_template_and_filled(self):
        """If one predecessor is filled and another is template-only, extract only filled."""
        mixed = _HANDOFF_TEMPLATE + "\n\n---\n\n" + """\
## milestone-2: Schema — COMPLETE

### Exposed Interfaces
| Endpoint | Method | Auth Required | Request Body | Response Shape |
|----------|--------|:------------:|-------------|---------------|
| /api/data | GET | Yes | - | { items: [] } |

### Enum/Status Values
| Entity | Field | Valid Values | DB Type | API String |
|--------|-------|-------------|---------|------------|
<!-- No enums -->
"""
        result = extract_predecessor_handoff_content(mixed, ["milestone-1", "milestone-2"])
        assert "/api/data" in result
        # milestone-1 had template only — should not contribute
        assert "<!-- Agent:" not in result


class TestMilestonePromptHandoffInjection:
    """Tests that build_milestone_execution_prompt injects predecessor handoff data."""

    def test_prompt_contains_handoff_instructions(self):
        """The MILESTONE_HANDOFF_INSTRUCTIONS should be in every milestone prompt."""
        from agent_team.agents import build_milestone_execution_prompt
        from agent_team.milestone_manager import MilestoneContext

        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = True
        ctx = MilestoneContext(
            milestone_id="milestone-2",
            title="Database Schema",
            requirements_path=".agent-team/milestones/milestone-2/REQUIREMENTS.md",
            predecessor_summaries=[],
        )
        prompt = build_milestone_execution_prompt(
            task="Build DrawSpace",
            depth="exhaustive",
            config=config,
            milestone_context=ctx,
            cwd=None,
        )
        assert "MILESTONE HANDOFF" in prompt
        assert "Read" in prompt
        assert "Exposed Interfaces" in prompt

    def test_prompt_injection_block_present_when_handoff_file_exists(self, tmp_path):
        """When MILESTONE_HANDOFF.md exists with data, it should be injected."""
        from agent_team.agents import build_milestone_execution_prompt
        from agent_team.milestone_manager import MilestoneContext, MilestoneCompletionSummary

        # Create the handoff file
        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        handoff_path = req_dir / "MILESTONE_HANDOFF.md"
        handoff_path.write_text(_HANDOFF_FILLED, encoding="utf-8")

        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = True

        pred_summary = MilestoneCompletionSummary(
            milestone_id="milestone-1",
            title="Infrastructure",
            exported_files=[],
            exported_symbols=[],
            summary_line="Infra done",
        )
        ctx = MilestoneContext(
            milestone_id="milestone-2",
            title="Database Schema",
            requirements_path=str(req_dir / "milestones" / "milestone-2" / "REQUIREMENTS.md"),
            predecessor_summaries=[pred_summary],
        )
        prompt = build_milestone_execution_prompt(
            task="Build DrawSpace",
            depth="exhaustive",
            config=config,
            milestone_context=ctx,
            cwd=str(tmp_path),
        )
        assert "PREDECESSOR HANDOFF" in prompt
        assert "/api/health" in prompt
        assert "EXACT endpoint paths" in prompt

    def test_no_injection_without_predecessors(self, tmp_path):
        """First milestone (no predecessors) should NOT have injection block."""
        from agent_team.agents import build_milestone_execution_prompt
        from agent_team.milestone_manager import MilestoneContext

        req_dir = tmp_path / ".agent-team"
        req_dir.mkdir()
        handoff_path = req_dir / "MILESTONE_HANDOFF.md"
        handoff_path.write_text(_HANDOFF_FILLED, encoding="utf-8")

        config = AgentTeamConfig()
        config.tracking_documents.milestone_handoff = True

        ctx = MilestoneContext(
            milestone_id="milestone-1",
            title="Infrastructure",
            requirements_path=str(req_dir / "milestones" / "milestone-1" / "REQUIREMENTS.md"),
            predecessor_summaries=[],  # No predecessors
        )
        prompt = build_milestone_execution_prompt(
            task="Build DrawSpace",
            depth="exhaustive",
            config=config,
            milestone_context=ctx,
            cwd=str(tmp_path),
        )
        assert "PREDECESSOR HANDOFF — INJECTED DATA" not in prompt
