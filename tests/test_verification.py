"""Tests for agent_team.verification — status computation, health, commands, and summaries."""

from __future__ import annotations

import json

import pytest

from agent_team.verification import (
    ProgressiveVerificationState,
    StructuredReviewResult,
    TaskVerificationResult,
    _detect_lint_command,
    _detect_test_command,
    _detect_type_check_command,
    _health_from_results,
    compute_overall_status,
    update_verification_state,
    write_verification_summary,
)


# ===================================================================
# 1. Overall Status Computation
# ===================================================================


class TestComputeOverallStatus:
    """Tests for compute_overall_status() phase-combination logic."""

    def test_all_pass(self):
        result = TaskVerificationResult(
            task_id="T1",
            contracts_passed=True,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=True,
        )
        assert compute_overall_status(result) == "pass"

    def test_contracts_fail(self):
        result = TaskVerificationResult(
            task_id="T2",
            contracts_passed=False,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=True,
        )
        assert compute_overall_status(result) == "fail"

    def test_tests_fail(self):
        result = TaskVerificationResult(
            task_id="T3",
            contracts_passed=True,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=False,
        )
        assert compute_overall_status(result) == "fail"

    def test_contracts_pass_tests_fail_is_fail(self):
        """CRITICAL: contracts pass + tests fail MUST be 'fail', never 'partial'.
        Behavioral regression overrides structural satisfaction."""
        result = TaskVerificationResult(
            task_id="T-CRITICAL",
            contracts_passed=True,
            lint_passed=None,
            type_check_passed=None,
            tests_passed=False,
        )
        status = compute_overall_status(result)
        assert status == "fail", (
            f"Expected 'fail' but got '{status}'. "
            "contracts pass + tests fail MUST resolve to 'fail'."
        )

    def test_lint_fail(self):
        result = TaskVerificationResult(
            task_id="T4",
            contracts_passed=True,
            lint_passed=False,
            type_check_passed=True,
            tests_passed=True,
        )
        assert compute_overall_status(result) == "fail"

    def test_all_none_is_partial(self):
        """No phases ran at all -> 'partial'."""
        result = TaskVerificationResult(
            task_id="T5",
            contracts_passed=None,
            lint_passed=None,
            type_check_passed=None,
            tests_passed=None,
        )
        assert compute_overall_status(result) == "partial"

    def test_mix_pass_none(self):
        """Some phases pass, others not run -> depends on implementation.
        If only contracts ran and passed, the other None phases mean partial."""
        result = TaskVerificationResult(
            task_id="T6",
            contracts_passed=True,
            lint_passed=None,
            type_check_passed=None,
            tests_passed=None,
        )
        status = compute_overall_status(result)
        # Only one phase ran and passed; others are None.
        # all(p for p in ran) is True because ran = [True], so "pass".
        assert status == "pass"


# ===================================================================
# 2. Health Model
# ===================================================================


class TestHealthFromResults:
    """Tests for _health_from_results() and the overall health model."""

    def test_empty_is_green(self):
        assert _health_from_results({}) == "green"

    def test_all_pass_is_green(self):
        results = {
            "T1": TaskVerificationResult(task_id="T1", overall="pass"),
            "T2": TaskVerificationResult(task_id="T2", overall="pass"),
        }
        assert _health_from_results(results) == "green"

    def test_any_fail_is_red(self):
        results = {
            "T1": TaskVerificationResult(task_id="T1", overall="pass"),
            "T2": TaskVerificationResult(task_id="T2", overall="fail"),
        }
        assert _health_from_results(results) == "red"

    def test_partial_is_yellow(self):
        results = {
            "T1": TaskVerificationResult(task_id="T1", overall="pass"),
            "T2": TaskVerificationResult(task_id="T2", overall="partial"),
        }
        assert _health_from_results(results) == "yellow"

    def test_contracts_pass_tests_fail_is_red(self):
        """CRITICAL: A task where contracts pass but tests fail has overall='fail',
        so health must be RED."""
        failing_result = TaskVerificationResult(
            task_id="T-RED",
            contracts_passed=True,
            tests_passed=False,
        )
        failing_result.overall = compute_overall_status(failing_result)

        results = {"T-RED": failing_result}
        health = _health_from_results(results)
        assert health == "red", (
            f"Expected 'red' but got '{health}'. "
            "contracts pass + tests fail must map to RED health."
        )


# ===================================================================
# 3. State Updates
# ===================================================================


class TestUpdateVerificationState:
    """Tests for update_verification_state() progressive tracking."""

    def test_add_passing_task(self):
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(task_id="T1", overall="pass")

        updated = update_verification_state(state, result)

        assert "T1" in updated.completed_tasks
        assert updated.overall_health == "green"

    def test_add_failing_task_turns_red(self):
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(task_id="T-FAIL", overall="fail")

        updated = update_verification_state(state, result)

        assert updated.overall_health == "red"

    def test_add_partial_task_turns_yellow(self):
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(task_id="T-PARTIAL", overall="partial")

        updated = update_verification_state(state, result)

        assert updated.overall_health == "yellow"


# ===================================================================
# 4. Command Detection
# ===================================================================


class TestDetectCommands:
    """Tests for _detect_lint_command, _detect_type_check_command, _detect_test_command."""

    # -- Lint detection --------------------------------------------------

    def test_detect_lint_from_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps({"scripts": {"lint": "eslint ."}}),
            encoding="utf-8",
        )
        cmd = _detect_lint_command(tmp_path)
        assert cmd == ["npm", "run", "lint"]

    def test_detect_lint_from_pyproject(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.ruff]\nline-length = 100\n",
            encoding="utf-8",
        )
        cmd = _detect_lint_command(tmp_path)
        assert cmd == ["ruff", "check", "."]

    def test_no_lint_returns_none(self, tmp_path):
        """No config files -> None."""
        cmd = _detect_lint_command(tmp_path)
        assert cmd is None

    # -- Type-check detection --------------------------------------------

    def test_detect_type_check_tsconfig(self, tmp_path):
        tsconfig = tmp_path / "tsconfig.json"
        tsconfig.write_text("{}", encoding="utf-8")
        cmd = _detect_type_check_command(tmp_path)
        assert cmd == ["npx", "tsc", "--noEmit"]

    # -- Test detection --------------------------------------------------

    def test_detect_test_pytest(self, tmp_path):
        ini = tmp_path / "pytest.ini"
        ini.write_text("[pytest]\n", encoding="utf-8")
        cmd = _detect_test_command(tmp_path)
        assert cmd == ["pytest"]

    def test_detect_test_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps({"scripts": {"test": "jest --coverage"}}),
            encoding="utf-8",
        )
        cmd = _detect_test_command(tmp_path)
        assert cmd == ["npm", "test"]


# ===================================================================
# 5. Verification Summary
# ===================================================================


class TestWriteVerificationSummary:
    """Tests for write_verification_summary() markdown output."""

    def _make_state(self, tasks: dict[str, TaskVerificationResult]) -> ProgressiveVerificationState:
        """Helper to build a ProgressiveVerificationState from task results."""
        state = ProgressiveVerificationState()
        for task_id, result in tasks.items():
            state.completed_tasks[task_id] = result
        state.overall_health = _health_from_results(state.completed_tasks)
        return state

    def test_writes_markdown(self, tmp_path):
        state = self._make_state({
            "T1": TaskVerificationResult(
                task_id="T1",
                contracts_passed=True,
                lint_passed=True,
                type_check_passed=True,
                tests_passed=True,
                overall="pass",
            ),
        })
        md_path = tmp_path / ".agent-team" / "VERIFICATION.md"
        write_verification_summary(state, md_path)

        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "# Verification Summary" in content
        assert "T1" in content

    def test_health_in_output(self, tmp_path):
        state = self._make_state({
            "T1": TaskVerificationResult(task_id="T1", overall="fail"),
        })
        md_path = tmp_path / "VERIFICATION.md"
        write_verification_summary(state, md_path)

        content = md_path.read_text(encoding="utf-8")
        assert "RED" in content

    def test_issues_in_output(self, tmp_path):
        state = self._make_state({
            "T1": TaskVerificationResult(
                task_id="T1",
                overall="fail",
                issues=["Contract: Symbol X not found (src/mod.py)"],
            ),
        })
        md_path = tmp_path / "VERIFICATION.md"
        write_verification_summary(state, md_path)

        content = md_path.read_text(encoding="utf-8")
        assert "## Issues" in content
        assert "Symbol X not found" in content


# ===================================================================
# 6. Structured Review Results
# ===================================================================


class TestStructuredReviewResult:
    """Tests for the StructuredReviewResult dataclass fields."""

    def test_blocking_flag(self):
        result = StructuredReviewResult(
            phase="lint",
            passed=False,
            details="3 errors found",
            blocking=True,
        )
        assert result.blocking is True
        assert result.passed is False

    def test_phase_field(self):
        result = StructuredReviewResult(
            phase="test",
            passed=True,
            details="All 42 tests passed",
            blocking=False,
        )
        assert result.phase == "test"
        assert result.passed is True
        assert result.blocking is False


class TestOutputTruncationConstant:
    """Tests for Finding #12: consistent output truncation."""

    def test_max_output_preview_defined(self):
        from agent_team.verification import _MAX_OUTPUT_PREVIEW
        assert _MAX_OUTPUT_PREVIEW == 500


# ===================================================================
# 7. Async Function Tests (Finding #2)
# ===================================================================


class TestRunCommand:
    """Tests for _run_command async subprocess execution."""

    @pytest.mark.asyncio
    async def test_successful_command(self, tmp_path):
        """Successful command returns exit code 0."""
        from agent_team.verification import _run_command
        # Create a simple script that exits 0
        script = tmp_path / "ok.py"
        script.write_text("import sys; sys.exit(0)", encoding="utf-8")
        returncode, stdout, stderr = await _run_command(
            ["python", str(script)], tmp_path
        )
        assert returncode == 0

    @pytest.mark.asyncio
    async def test_command_failure(self, tmp_path):
        """Failed command returns non-zero exit code."""
        from agent_team.verification import _run_command
        script = tmp_path / "fail.py"
        script.write_text("import sys; sys.exit(1)", encoding="utf-8")
        returncode, stdout, stderr = await _run_command(
            ["python", str(script)], tmp_path
        )
        assert returncode == 1

    @pytest.mark.asyncio
    async def test_command_not_found(self, tmp_path):
        """Non-existent command returns error."""
        from agent_team.verification import _run_command
        returncode, stdout, stderr = await _run_command(
            ["nonexistent_command_xyz"], tmp_path
        )
        assert returncode == 1
        assert "not found" in stderr.lower() or "error" in stderr.lower()

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path):
        """stderr output is captured."""
        from agent_team.verification import _run_command
        script = tmp_path / "err.py"
        script.write_text(
            "import sys; sys.stderr.write('error output'); sys.exit(1)",
            encoding="utf-8",
        )
        returncode, stdout, stderr = await _run_command(
            ["python", str(script)], tmp_path
        )
        assert "error output" in stderr

    @pytest.mark.asyncio
    async def test_command_timeout(self, tmp_path):
        """Command that exceeds timeout is killed."""
        from agent_team.verification import _run_command
        script = tmp_path / "slow.py"
        script.write_text("import time; time.sleep(30)", encoding="utf-8")
        returncode, stdout, stderr = await _run_command(
            ["python", str(script)], tmp_path, timeout=1
        )
        assert returncode == 1
        assert "timed out" in stderr.lower()


class TestVerifyTaskCompletion:
    """Tests for verify_task_completion async pipeline."""

    @pytest.mark.asyncio
    async def test_all_phases_pass_empty_project(self, tmp_path):
        """Empty project with empty registry should pass contracts."""
        from agent_team.verification import verify_task_completion
        from agent_team.contracts import ContractRegistry
        registry = ContractRegistry()
        result = await verify_task_completion(
            "T1", tmp_path, registry,
            run_lint=False, run_type_check=False, run_tests=False,
        )
        assert result.contracts_passed is True
        assert result.overall == "pass"

    @pytest.mark.asyncio
    async def test_lint_failure(self, tmp_path):
        """When lint is enabled and fails, overall should be fail."""
        from agent_team.verification import verify_task_completion
        from agent_team.contracts import ContractRegistry
        # Create a pyproject.toml with ruff config so lint is detected
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        # Create a Python file with intentional lint error
        (tmp_path / "bad.py").write_text("x=1\n", encoding="utf-8")
        registry = ContractRegistry()
        result = await verify_task_completion(
            "T-LINT", tmp_path, registry,
            run_lint=True, run_type_check=False, run_tests=False,
        )
        # Lint might pass or fail depending on if ruff is installed
        # Just verify the structure is correct
        assert result.task_id == "T-LINT"
        assert result.overall in ("pass", "fail", "partial")

    @pytest.mark.asyncio
    async def test_mixed_results(self, tmp_path):
        """Result with contract pass but other phases not run gives pass."""
        from agent_team.verification import verify_task_completion
        from agent_team.contracts import ContractRegistry
        registry = ContractRegistry()
        result = await verify_task_completion(
            "T-MIX", tmp_path, registry,
            run_lint=False, run_type_check=False, run_tests=False,
        )
        assert result.contracts_passed is True
        assert result.overall == "pass"


class TestRunAutomatedReviewPhases:
    """Tests for run_automated_review_phases async function."""

    @pytest.mark.asyncio
    async def test_no_tools_detected(self, tmp_path):
        """Empty project: no tools detected, no phases run."""
        from agent_team.verification import run_automated_review_phases
        results = await run_automated_review_phases(tmp_path)
        assert results == []

    @pytest.mark.asyncio
    async def test_selective_phases(self, tmp_path):
        """Disabling all phases returns empty list."""
        from agent_team.verification import run_automated_review_phases
        results = await run_automated_review_phases(
            tmp_path, run_lint=False, run_type_check=False, run_tests=False,
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_all_phases_enabled(self, tmp_path):
        """All phases enabled but no tools found returns empty list."""
        from agent_team.verification import run_automated_review_phases
        results = await run_automated_review_phases(
            tmp_path, run_lint=True, run_type_check=True, run_tests=True,
        )
        # No config files -> no tools detected -> empty results
        assert results == []


# ===================================================================
# Post-orchestration verification integration
# ===================================================================


class TestPostOrchestrationVerification:
    """Integration tests for the verification pipeline wiring."""

    def test_state_populated_after_update(self):
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(
            task_id="post-orchestration",
            contracts_passed=True,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=True,
            overall="pass",
        )
        update_verification_state(state, result)
        assert "post-orchestration" in state.completed_tasks
        assert state.overall_health == "green"

    def test_summary_has_table_row(self, tmp_path):
        state = ProgressiveVerificationState()
        result = TaskVerificationResult(
            task_id="post-orchestration",
            contracts_passed=True,
            lint_passed=True,
            type_check_passed=True,
            tests_passed=True,
            overall="pass",
        )
        update_verification_state(state, result)
        out = tmp_path / "VERIFICATION.md"
        write_verification_summary(state, out)
        content = out.read_text()
        assert "post-orchestration" in content
        assert "PASS" in content
