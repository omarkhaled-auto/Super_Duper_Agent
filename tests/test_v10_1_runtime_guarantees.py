"""Tests for v10.1 Runtime Guarantees — Deliverables 10 + 11.

Deliverable 10: Artifact Verification Gate
  - ARTIFACT_RECOVERY_PROMPT constant
  - _run_artifact_recovery() async function
  - Post-orchestration gate in main() that checks REQUIREMENTS.md existence

Deliverable 11: Mandatory Convergence Recovery
  - elif health=="unknown" non-milestones else block forces recovery in PRD mode

Tests use the same source-text-inspection pattern as the rest of the test suite.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load source text once at module level (same pattern as test_v10_production_fixes.py)
# ---------------------------------------------------------------------------
_SRC = Path(__file__).resolve().parent.parent / "src" / "agent_team"
CLI_SOURCE = (_SRC / "cli.py").read_text(encoding="utf-8")
DISPLAY_SOURCE = (_SRC / "display.py").read_text(encoding="utf-8")


# ============================================================
# Deliverable 10A: ARTIFACT_RECOVERY_PROMPT constant
# ============================================================


def _extract_prompt_block(name: str) -> str:
    """Extract the body of a triple-quoted prompt constant from CLI_SOURCE.

    Finds ``NAME = \"\"\"\\`` and returns everything between the opening
    triple-quote and the closing triple-quote.
    """
    marker = f'{name} = """'
    start = CLI_SOURCE.find(marker)
    assert start != -1, f"{name} not found in cli.py"
    # Skip past the opening triple-quote
    body_start = start + len(marker)
    # Find the closing triple-quote
    close = CLI_SOURCE.find('"""', body_start)
    assert close != -1, f"Closing triple-quote not found for {name}"
    return CLI_SOURCE[body_start:close]


class TestArtifactRecoveryPrompt:
    """Verify ARTIFACT_RECOVERY_PROMPT exists with required content."""

    def test_prompt_constant_exists(self):
        assert "ARTIFACT_RECOVERY_PROMPT" in CLI_SOURCE

    def test_prompt_contains_requirements_md(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "REQUIREMENTS.md" in block

    def test_prompt_contains_svc_xxx(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "SVC-" in block, "ARTIFACT_RECOVERY_PROMPT must reference SVC-xxx service wiring"

    def test_prompt_contains_status_registry(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "STATUS_REGISTRY" in block

    def test_prompt_contains_tasks_md(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "TASKS.md" in block

    def test_prompt_has_requirements_dir_placeholder(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "{requirements_dir}" in block

    def test_prompt_has_task_text_placeholder(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "{task_text}" in block

    def test_prompt_is_multiline_string(self):
        # Must be a proper triple-quoted string assignment
        assert re.search(r'ARTIFACT_RECOVERY_PROMPT\s*=\s*"""', CLI_SOURCE)

    def test_prompt_mentions_artifact_recovery(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "ARTIFACT RECOVERY" in block

    def test_prompt_mentions_req_xxx(self):
        block = _extract_prompt_block("ARTIFACT_RECOVERY_PROMPT")
        assert "REQ-" in block


# ============================================================
# Deliverable 10B: _run_artifact_recovery() function
# ============================================================


class TestArtifactRecoveryFunction:
    """Verify _run_artifact_recovery async function structure."""

    def test_function_exists(self):
        assert "async def _run_artifact_recovery(" in CLI_SOURCE

    def test_function_has_cwd_param(self):
        # Extract the function signature (up to the closing paren)
        match = re.search(
            r"async def _run_artifact_recovery\((.*?)\)\s*->",
            CLI_SOURCE,
            re.DOTALL,
        )
        assert match is not None, "_run_artifact_recovery signature not found"
        sig = match.group(1)
        assert "cwd" in sig

    def test_function_has_config_param(self):
        match = re.search(
            r"async def _run_artifact_recovery\((.*?)\)\s*->",
            CLI_SOURCE,
            re.DOTALL,
        )
        sig = match.group(1)
        assert "config" in sig

    def test_function_has_task_text_param(self):
        match = re.search(
            r"async def _run_artifact_recovery\((.*?)\)\s*->",
            CLI_SOURCE,
            re.DOTALL,
        )
        sig = match.group(1)
        assert "task_text" in sig

    def test_function_has_prd_path_param(self):
        match = re.search(
            r"async def _run_artifact_recovery\((.*?)\)\s*->",
            CLI_SOURCE,
            re.DOTALL,
        )
        sig = match.group(1)
        assert "prd_path" in sig

    def test_function_uses_claude_sdk_client(self):
        # Must use ClaudeSDKClient, NOT _run_agent_session
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        # Find the next function definition or end of file
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "ClaudeSDKClient" in body

    def test_function_uses_process_response(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "_process_response" in body

    def test_function_uses_build_options(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "_build_options" in body

    def test_function_has_try_except(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "try:" in body
        assert "except" in body

    def test_function_logs_traceback(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "traceback.format_exc()" in body

    def test_function_references_backend_global(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "_backend" in body

    def test_function_returns_float(self):
        match = re.search(
            r"async def _run_artifact_recovery\(.*?\)\s*->\s*(\w+):",
            CLI_SOURCE,
            re.DOTALL,
        )
        assert match is not None
        assert match.group(1) == "float"

    def test_function_formats_prompt_with_requirements_dir(self):
        start = CLI_SOURCE.index("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "requirements_dir" in body
        assert ".format(" in body or "ARTIFACT_RECOVERY_PROMPT.format" in body


# ============================================================
# Deliverable 10C: Artifact Verification Gate in main()
# ============================================================


class TestArtifactVerificationGate:
    """Verify the post-orchestration artifact verification gate in main()."""

    def test_gate_condition_checks_prd_mode(self):
        # The gate must be conditional on _is_prd_mode
        assert "_is_prd_mode and not _use_milestones" in CLI_SOURCE

    def test_gate_checks_requirements_file_existence(self):
        # Must check if the requirements file exists
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        assert pos != -1, "Artifact verification gate comment block not found"
        block = CLI_SOURCE[pos:pos + 2000]
        assert ".is_file()" in block

    def test_gate_adds_artifact_recovery_to_recovery_types(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert '"artifact_recovery"' in block
        assert "recovery_types.append" in block

    def test_gate_calls_run_artifact_recovery(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "_run_artifact_recovery" in block

    def test_gate_has_try_except_crash_isolation(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "try:" in block
        assert "except" in block

    def test_gate_verifies_file_after_recovery(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        # After recovery, it checks again if the file was created
        # There should be two is_file() checks: one to see if missing, one to verify recovery
        count = block.count(".is_file()")
        assert count >= 2, f"Expected at least 2 is_file() checks, found {count}"

    def test_gate_has_else_branch_no_recovery_needed(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 3000]
        assert "no recovery needed" in block

    def test_gate_appears_before_contract_health_check(self):
        pos_artifact = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        pos_contract = CLI_SOURCE.find("Post-orchestration: Contract health check")
        assert pos_artifact != -1, "Artifact verification gate not found"
        assert pos_contract != -1, "Contract health check not found"
        assert pos_artifact < pos_contract, (
            f"Artifact verification gate (pos={pos_artifact}) must appear BEFORE "
            f"contract health check (pos={pos_contract})"
        )

    def test_gate_updates_state_cost(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "_current_state" in block
        assert "total_cost" in block

    def test_gate_passes_task_text_to_recovery(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "task_text=" in block

    def test_gate_passes_prd_path_to_recovery(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "prd_path=" in block

    def test_gate_also_checks_tasks_md(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "TASKS.md" in block


# ============================================================
# Deliverable 11: Mandatory Convergence Recovery
# ============================================================


class TestMandatoryConvergenceRecovery:
    """Verify the elif health=='unknown' block forces recovery in PRD mode."""

    def test_unknown_health_block_contains_is_prd_mode(self):
        # Find the recovery-decision block (after "needs_recovery = False")
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        assert pos_needs != -1
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        # Within the unknown branch, _is_prd_mode must appear
        unknown_pos = block_after.find('health == "unknown"')
        assert unknown_pos != -1, 'health == "unknown" not found after needs_recovery = False'
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]
        assert "_is_prd_mode" in unknown_block

    def test_prd_mode_sets_needs_recovery_true(self):
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        unknown_pos = block_after.find('health == "unknown"')
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]
        # Within the _is_prd_mode branch, needs_recovery = True must be set
        prd_pos = unknown_block.find("_is_prd_mode")
        assert prd_pos != -1
        prd_block = unknown_block[prd_pos:prd_pos + 800]
        assert "needs_recovery = True" in prd_block

    def test_non_prd_else_still_warns(self):
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        unknown_pos = block_after.find('health == "unknown"')
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]
        # The else branch (non-PRD) should still have the warning
        assert "no requirements found" in unknown_block

    def test_unknown_health_prd_message(self):
        assert "UNKNOWN HEALTH in PRD mode" in CLI_SOURCE

    def test_mandatory_review_fleet_message(self):
        assert "mandatory review fleet" in CLI_SOURCE.lower() or \
               "deploying mandatory review fleet" in CLI_SOURCE.lower()


# ============================================================
# Pipeline Execution Order
# ============================================================


class TestPipelineExecutionOrder:
    """Verify correct ordering of post-orchestration blocks in main()."""

    def test_artifact_gate_after_tasks_diagnostic(self):
        pos_tasks = CLI_SOURCE.find("TASKS.md diagnostic")
        pos_artifact = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        assert pos_tasks != -1, "TASKS.md diagnostic comment not found"
        assert pos_artifact != -1, "Artifact verification gate comment not found"
        assert pos_tasks < pos_artifact, (
            "TASKS.md diagnostic must appear BEFORE artifact verification gate"
        )

    def test_artifact_gate_before_contract_check(self):
        pos_artifact = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        pos_contract = CLI_SOURCE.find("Post-orchestration: Contract health check")
        assert pos_artifact != -1
        assert pos_contract != -1
        assert pos_artifact < pos_contract

    def test_contract_check_before_convergence_check(self):
        pos_contract = CLI_SOURCE.find("Post-orchestration: Contract health check")
        pos_convergence = CLI_SOURCE.find("Post-orchestration: Convergence health check")
        assert pos_contract != -1
        assert pos_convergence != -1
        assert pos_contract < pos_convergence

    def test_convergence_unknown_prd_sets_recovery(self):
        # After "needs_recovery = False", the unknown + _is_prd_mode branch
        # must set needs_recovery = True BEFORE the "if needs_recovery:" block
        pos_needs_false = CLI_SOURCE.find("needs_recovery = False")
        pos_needs_check = CLI_SOURCE.find("if needs_recovery:", pos_needs_false)
        assert pos_needs_false != -1
        assert pos_needs_check != -1
        # The _is_prd_mode + needs_recovery=True must be between these two positions
        middle = CLI_SOURCE[pos_needs_false:pos_needs_check]
        assert "_is_prd_mode" in middle
        assert "needs_recovery = True" in middle

    def test_recovery_types_append_before_recovery_check(self):
        # "artifact_recovery" is appended to recovery_types before the
        # convergence health check which adds "review_recovery"
        pos_artifact_append = CLI_SOURCE.find('"artifact_recovery"')
        pos_review_append = CLI_SOURCE.find('"review_recovery"')
        assert pos_artifact_append != -1
        assert pos_review_append != -1
        assert pos_artifact_append < pos_review_append


# ============================================================
# Recovery Type Label in display.py
# ============================================================


class TestRecoveryTypeLabel:
    """Verify artifact_recovery is a recognized recovery type in display.py."""

    def test_artifact_recovery_key_in_type_hints(self):
        assert '"artifact_recovery"' in DISPLAY_SOURCE

    def test_label_mentions_requirements_or_source_code(self):
        pos = DISPLAY_SOURCE.find('"artifact_recovery"')
        assert pos != -1
        # Get the value string for that key (rest of the line or next line)
        line_end = DISPLAY_SOURCE.find("\n", pos)
        if line_end == -1:
            line_end = len(DISPLAY_SOURCE)
        label_line = DISPLAY_SOURCE[pos:line_end]
        assert "REQUIREMENTS" in label_line or "source code" in label_line, (
            f"artifact_recovery label should mention REQUIREMENTS or source code, got: {label_line}"
        )

    def test_label_is_in_type_hints_dict(self):
        # The key should appear inside the type_hints dictionary
        pos_type_hints = DISPLAY_SOURCE.find("type_hints")
        pos_artifact = DISPLAY_SOURCE.find('"artifact_recovery"')
        assert pos_type_hints != -1
        assert pos_artifact != -1
        assert pos_type_hints < pos_artifact, (
            "artifact_recovery must appear after type_hints dict definition"
        )


# ============================================================
# Backward Compatibility
# ============================================================


class TestBackwardCompatibility:
    """Ensure non-PRD mode and milestones mode are not affected."""

    def test_artifact_gate_requires_prd_mode(self):
        # The gate condition includes _is_prd_mode — non-PRD mode skips it
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 200]
        assert "_is_prd_mode" in block

    def test_artifact_gate_excludes_milestones(self):
        # The gate condition includes "not _use_milestones"
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 200]
        assert "not _use_milestones" in block

    def test_convergence_unknown_non_prd_warning_preserved(self):
        # The original "no requirements found" warning for non-PRD must still exist
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        unknown_pos = block_after.find('health == "unknown"')
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]
        assert "no requirements found" in unknown_block

    def test_non_prd_unknown_does_not_set_recovery(self):
        # In the else branch of _is_prd_mode (non-PRD), needs_recovery should NOT be set
        # The else branch should only print a warning
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        unknown_pos = block_after.find('health == "unknown"')
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]

        # Find the else for _is_prd_mode
        prd_pos = unknown_block.find("if _is_prd_mode:")
        assert prd_pos != -1
        else_pos = unknown_block.find("else:", prd_pos)
        assert else_pos != -1
        # The else block should NOT contain needs_recovery = True
        else_block = unknown_block[else_pos:else_pos + 300]
        assert "needs_recovery = True" not in else_block

    def test_milestones_unknown_handler_unchanged(self):
        # Milestones path (with milestones_dir.iterdir()) still sets needs_recovery
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 3000]
        unknown_pos = block_after.find('health == "unknown"')
        unknown_block = block_after[unknown_pos:unknown_pos + 1500]
        assert "milestones_dir" in unknown_block


# ============================================================
# Issue #5 Confirmation: Review-fleet-marks-nothing scenario
# ============================================================


class TestIssue5Confirmation:
    """Confirm the existing code handles review-fleet-marks-nothing (Issue #5).

    In the health=="failed" block, when review_cycles > 0 and
    convergence_ratio < recovery_threshold, needs_recovery = True.
    """

    def test_failed_health_with_review_cycles_sets_recovery(self):
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 1500]
        failed_pos = block_after.find('health == "failed"')
        assert failed_pos != -1
        failed_block = block_after[failed_pos:failed_pos + 800]
        # The block must check review_cycles > 0
        assert "review_cycles > 0" in failed_block
        # And convergence_ratio < recovery_threshold
        assert "convergence_ratio < recovery_threshold" in failed_block
        # And set needs_recovery = True
        assert "needs_recovery = True" in failed_block

    def test_zero_cycle_failure_also_sets_recovery(self):
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 1500]
        failed_pos = block_after.find('health == "failed"')
        failed_block = block_after[failed_pos:failed_pos + 800]
        # Zero-cycle failure: review_cycles == 0 and total_requirements > 0
        assert "review_cycles == 0" in failed_block
        assert "total_requirements > 0" in failed_block

    def test_failed_health_partial_review_comment(self):
        # Must have a comment explaining partial-review failure
        pos_needs = CLI_SOURCE.find("needs_recovery = False")
        block_after = CLI_SOURCE[pos_needs:pos_needs + 1500]
        failed_pos = block_after.find('health == "failed"')
        failed_block = block_after[failed_pos:failed_pos + 800]
        assert "Partial-review failure" in failed_block or "insufficient coverage" in failed_block


# ============================================================
# Integration: Prompt and Gate Coherence
# ============================================================


class TestPromptGateCoherence:
    """Cross-check that prompt and gate are consistent."""

    def test_prompt_references_same_file_as_gate(self):
        # Both the prompt and gate reference REQUIREMENTS.md
        pos_prompt = CLI_SOURCE.find("ARTIFACT_RECOVERY_PROMPT")
        prompt_block = CLI_SOURCE[pos_prompt:pos_prompt + 3000]
        assert "REQUIREMENTS.md" in prompt_block

        pos_gate = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        gate_block = CLI_SOURCE[pos_gate:pos_gate + 2000]
        assert "requirements_file" in gate_block or "REQUIREMENTS.md" in gate_block

    def test_recovery_function_used_only_in_gate(self):
        # _run_artifact_recovery should be called from the gate, not elsewhere
        # Count occurrences: definition (1) + call in gate (1) = at minimum 2
        count = CLI_SOURCE.count("_run_artifact_recovery")
        assert count >= 2, f"Expected at least 2 occurrences, found {count}"

    def test_artifact_recovery_phase_name_consistent(self):
        # The function uses current_phase="artifact_recovery"
        start = CLI_SOURCE.find("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert 'current_phase="artifact_recovery"' in body or \
               "current_phase='artifact_recovery'" in body

    def test_prompt_mentions_scan_project_structure(self):
        # The prompt should instruct scanning the project
        block = CLI_SOURCE[CLI_SOURCE.index("ARTIFACT_RECOVERY_PROMPT"):]
        block = block[:3000]
        assert "Scan" in block or "scan" in block

    def test_gate_uses_asyncio_run(self):
        # The gate calls the async function via asyncio.run
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "asyncio.run" in block


# ============================================================
# Edge Cases and Robustness
# ============================================================


class TestEdgeCasesAndRobustness:
    """Additional robustness checks for the v10.1 features."""

    def test_recovery_prompt_mentions_step_numbers(self):
        # Should have structured steps (STEP 1, STEP 2, etc.)
        block = CLI_SOURCE[CLI_SOURCE.index("ARTIFACT_RECOVERY_PROMPT"):]
        block = block[:3000]
        assert "STEP 1" in block
        assert "STEP 2" in block

    def test_recovery_function_handles_prd_content(self):
        # Should read PRD content if prd_path is provided
        start = CLI_SOURCE.find("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "prd_path" in body
        assert "prd_content" in body or "read_text" in body

    def test_recovery_function_handles_missing_prd(self):
        # Should gracefully handle when PRD file doesn't exist
        start = CLI_SOURCE.find("async def _run_artifact_recovery(")
        next_def = CLI_SOURCE.find("\nasync def ", start + 1)
        if next_def == -1:
            next_def = CLI_SOURCE.find("\ndef ", start + 1)
        if next_def == -1:
            next_def = len(CLI_SOURCE)
        body = CLI_SOURCE[start:next_def]
        assert "is_file()" in body

    def test_gate_handles_recovery_cost(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "_artifact_cost" in block

    def test_v10_1_comment_marker_exists(self):
        # The gate must be clearly marked as v10.1
        assert "v10.1" in CLI_SOURCE

    def test_recovery_prompt_not_empty(self):
        # Ensure the prompt has substantial content
        match = re.search(
            r'ARTIFACT_RECOVERY_PROMPT\s*=\s*"""\\\n(.*?)"""',
            CLI_SOURCE,
            re.DOTALL,
        )
        assert match is not None, "Could not extract ARTIFACT_RECOVERY_PROMPT content"
        content = match.group(1).strip()
        assert len(content) > 200, f"Prompt seems too short ({len(content)} chars)"

    def test_gate_success_message(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "generated successfully" in block or "REQUIREMENTS.md generated" in block

    def test_gate_failure_message(self):
        pos = CLI_SOURCE.find("v10.1: Post-orchestration Artifact Verification Gate")
        block = CLI_SOURCE[pos:pos + 2000]
        assert "still not found" in block
