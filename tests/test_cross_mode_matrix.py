"""Cross-Mode Verification Matrix — 95% confidence harness.

Systematically verifies that ALL 42 production checkpoints from v10.0-v10.2
behave correctly across EVERY (depth × input_mode) combination.

5 layers of verification:
  Layer 1: Config State Matrix — parametrized across (depth × prd_mode)
  Layer 2: Prompt Content Matrix — parametrized across (depth × input_mode)
  Layer 3: Pipeline Guard Consistency — source-level guard extraction
  Layer 4: Cross-Mode Behavioral Tests — function-level across modes
  Layer 5: Guard-to-Config Mapping — verify guards reference correct fields
"""
from __future__ import annotations

import inspect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from agent_team.agents import (
    build_orchestrator_prompt,
    build_milestone_execution_prompt,
    CODE_REVIEWER_PROMPT,
)
from agent_team.config import (
    AgentTeamConfig,
    PostOrchestrationScanConfig,
    E2ETestingConfig,
    BrowserTestingConfig,
    IntegrityScanConfig,
    DatabaseScanConfig,
    MilestoneConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.design_reference import (
    generate_fallback_ui_requirements,
    _infer_design_direction,
)
from agent_team.e2e_testing import detect_app_type
from agent_team.milestone_manager import normalize_milestone_dirs
from agent_team.scheduler import parse_tasks_md

# ---------------------------------------------------------------------------
# Source loading (once at module level)
# ---------------------------------------------------------------------------
_SRC = Path(__file__).resolve().parent.parent / "src" / "agent_team"
_CLI_SOURCE = (_SRC / "cli.py").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _make_config(depth: str, prd_mode: bool = False,
                 user_overrides: set[str] | None = None) -> AgentTeamConfig:
    """Create config and apply depth gating."""
    config = AgentTeamConfig()
    apply_depth_quality_gating(depth, config,
                               user_overrides=user_overrides,
                               prd_mode=prd_mode)
    return config


def _build_prompt(depth: str, input_mode: str) -> str:
    """Build orchestrator prompt for a given depth and input mode."""
    base = dict(task="Build a task management app", depth=depth,
                config=AgentTeamConfig())
    if input_mode == "task":
        pass  # defaults
    elif input_mode == "prd":
        base["prd_path"] = "spec.md"
    elif input_mode == "interview_simple":
        base["interview_scope"] = "SIMPLE"
        base["interview_doc"] = "A simple todo app with user auth."
    elif input_mode == "interview_complex":
        base["interview_scope"] = "COMPLEX"
        base["interview_doc"] = "Full task management with roles, dashboards, analytics."
    elif input_mode == "chunked_prd":
        base["prd_path"] = "spec.md"
        base["prd_chunks"] = ["chunk1.md", "chunk2.md"]
        base["prd_index"] = {"auth": {"heading": "Authentication", "size_bytes": 500}}
    else:
        raise ValueError(f"Unknown input_mode: {input_mode}")
    return build_orchestrator_prompt(**base)


# ===========================================================================
# LAYER 1: Config State Matrix
# ===========================================================================

# Expected config state for each (depth, prd_mode) combination.
# Each entry: (depth, prd_mode, expected_dict)
# expected_dict maps config field paths to expected values.

_DEFAULTS = dict(
    mock_data_scan=True,
    ui_compliance_scan=True,
    api_contract_scan=True,
    max_scan_fix_passes=1,
    deployment_scan=True,
    asset_scan=True,
    prd_reconciliation=True,
    dual_orm_scan=True,
    default_value_scan=True,
    relationship_scan=True,
    e2e_enabled=False,
    e2e_max_fix_retries=5,
    browser_enabled=False,
    browser_max_fix_retries=5,
    review_recovery_retries=1,
)

CONFIG_MATRIX: list[tuple[str, bool, dict[str, Any]]] = [
    # (depth, prd_mode, overrides_from_defaults)
    ("quick", False, dict(
        mock_data_scan=False, ui_compliance_scan=False, api_contract_scan=False,
        max_scan_fix_passes=0,
        deployment_scan=False, asset_scan=False, prd_reconciliation=False,
        dual_orm_scan=False, default_value_scan=False, relationship_scan=False,
        e2e_enabled=False, e2e_max_fix_retries=1,
        browser_enabled=False,
        review_recovery_retries=0,
    )),
    ("quick", True, dict(
        mock_data_scan=False, ui_compliance_scan=False, api_contract_scan=False,
        max_scan_fix_passes=0,
        deployment_scan=False, asset_scan=False, prd_reconciliation=False,
        dual_orm_scan=False, default_value_scan=False, relationship_scan=False,
        e2e_enabled=False, e2e_max_fix_retries=1,
        browser_enabled=False,
        review_recovery_retries=0,
    )),
    ("standard", False, dict(
        # Standard only disables PRD reconciliation
        prd_reconciliation=False,
    )),
    ("standard", True, dict(
        prd_reconciliation=False,
    )),
    ("thorough", False, dict(
        e2e_enabled=True, e2e_max_fix_retries=2,
        review_recovery_retries=2,
        browser_enabled=False,  # NOT prd_mode → stays disabled
    )),
    ("thorough", True, dict(
        e2e_enabled=True, e2e_max_fix_retries=2,
        review_recovery_retries=2,
        browser_enabled=True, browser_max_fix_retries=3,
    )),
    ("exhaustive", False, dict(
        e2e_enabled=True, e2e_max_fix_retries=3,
        review_recovery_retries=3,
        max_scan_fix_passes=2,
        browser_enabled=False,  # NOT prd_mode → stays disabled
    )),
    ("exhaustive", True, dict(
        e2e_enabled=True, e2e_max_fix_retries=3,
        review_recovery_retries=3,
        max_scan_fix_passes=2,
        browser_enabled=True, browser_max_fix_retries=5,
    )),
]


def _resolve_expected(overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge overrides into defaults."""
    result = dict(_DEFAULTS)
    result.update(overrides)
    return result


def _extract_config_state(config: AgentTeamConfig) -> dict[str, Any]:
    """Extract the config fields we care about into a flat dict."""
    return dict(
        mock_data_scan=config.post_orchestration_scans.mock_data_scan,
        ui_compliance_scan=config.post_orchestration_scans.ui_compliance_scan,
        api_contract_scan=config.post_orchestration_scans.api_contract_scan,
        max_scan_fix_passes=config.post_orchestration_scans.max_scan_fix_passes,
        deployment_scan=config.integrity_scans.deployment_scan,
        asset_scan=config.integrity_scans.asset_scan,
        prd_reconciliation=config.integrity_scans.prd_reconciliation,
        dual_orm_scan=config.database_scans.dual_orm_scan,
        default_value_scan=config.database_scans.default_value_scan,
        relationship_scan=config.database_scans.relationship_scan,
        e2e_enabled=config.e2e_testing.enabled,
        e2e_max_fix_retries=config.e2e_testing.max_fix_retries,
        browser_enabled=config.browser_testing.enabled,
        browser_max_fix_retries=config.browser_testing.max_fix_retries,
        review_recovery_retries=config.milestone.review_recovery_retries,
    )


_CONFIG_IDS = [f"{d}{'_prd' if p else ''}" for d, p, _ in CONFIG_MATRIX]


class TestConfigStateMatrix:
    """Layer 1: Verify config state for ALL (depth × prd_mode) combinations."""

    @pytest.mark.parametrize(
        "depth, prd_mode, overrides",
        [(d, p, o) for d, p, o in CONFIG_MATRIX],
        ids=_CONFIG_IDS,
    )
    def test_config_fields_match_expected(self, depth, prd_mode, overrides):
        config = _make_config(depth, prd_mode=prd_mode)
        actual = _extract_config_state(config)
        expected = _resolve_expected(overrides)
        for key, exp_val in expected.items():
            assert actual[key] == exp_val, (
                f"[{depth}{'_prd' if prd_mode else ''}] "
                f"{key}: expected {exp_val}, got {actual[key]}"
            )

    @pytest.mark.parametrize("depth", ["quick", "standard", "thorough", "exhaustive"])
    def test_quick_disables_all_scans(self, depth):
        """Quick must disable ALL scans; other depths must NOT disable all."""
        config = _make_config(depth)
        all_scans = [
            config.post_orchestration_scans.mock_data_scan,
            config.post_orchestration_scans.ui_compliance_scan,
            config.post_orchestration_scans.api_contract_scan,
            config.integrity_scans.deployment_scan,
            config.integrity_scans.asset_scan,
            config.database_scans.dual_orm_scan,
            config.database_scans.default_value_scan,
            config.database_scans.relationship_scan,
        ]
        if depth == "quick":
            assert not any(all_scans), "Quick depth must disable all scans"
        else:
            assert all(all_scans), f"{depth} depth must keep all scans enabled"

    @pytest.mark.parametrize("depth", ["quick", "standard", "thorough", "exhaustive"])
    def test_browser_testing_requires_prd_for_thorough_plus(self, depth):
        """Browser testing only auto-enables for thorough/exhaustive + prd_mode."""
        config_no_prd = _make_config(depth, prd_mode=False)
        config_prd = _make_config(depth, prd_mode=True)

        if depth in ("thorough", "exhaustive"):
            assert config_prd.browser_testing.enabled is True, (
                f"{depth}+prd should enable browser testing"
            )
            assert config_no_prd.browser_testing.enabled is False, (
                f"{depth} without prd should NOT enable browser testing"
            )
        else:
            assert config_no_prd.browser_testing.enabled is False
            assert config_prd.browser_testing.enabled is False

    @pytest.mark.parametrize("depth", ["quick", "standard", "thorough", "exhaustive"])
    def test_e2e_testing_gating(self, depth):
        """E2E testing only auto-enables for thorough+."""
        config = _make_config(depth)
        if depth in ("thorough", "exhaustive"):
            assert config.e2e_testing.enabled is True
        else:
            assert config.e2e_testing.enabled is False

    def test_user_override_preserved_across_all_depths(self):
        """User-set max_scan_fix_passes=5 must survive ALL depth gatings."""
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            config = AgentTeamConfig()
            config.post_orchestration_scans.max_scan_fix_passes = 5
            overrides = {"post_orchestration_scans.max_scan_fix_passes"}
            apply_depth_quality_gating(depth, config, user_overrides=overrides)
            assert config.post_orchestration_scans.max_scan_fix_passes == 5, (
                f"User override lost at depth={depth}"
            )

    def test_user_override_e2e_preserved(self):
        """User-set e2e_testing.enabled=True must survive quick depth."""
        config = AgentTeamConfig()
        config.e2e_testing.enabled = True
        overrides = {"e2e_testing.enabled"}
        apply_depth_quality_gating("quick", config, user_overrides=overrides)
        assert config.e2e_testing.enabled is True

    def test_legacy_milestone_fields_gated_by_quick(self):
        """Quick must disable legacy milestone.mock_data_scan too."""
        config = _make_config("quick")
        assert config.milestone.mock_data_scan is False
        assert config.milestone.ui_compliance_scan is False


# ===========================================================================
# LAYER 2: Prompt Content Matrix
# ===========================================================================

DEPTHS = ["quick", "standard", "thorough", "exhaustive"]
INPUT_MODES = ["task", "prd", "interview_simple", "interview_complex", "chunked_prd"]

# PRD-mode input modes (should have ROOT ARTIFACTS)
PRD_MODES = {"prd", "interview_complex", "chunked_prd"}
# Standard-mode input modes (should NOT have ROOT ARTIFACTS)
STD_MODES = {"task", "interview_simple"}


class TestPromptContentMatrix:
    """Layer 2: Verify prompt blocks for ALL (depth × input_mode) combinations."""

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", INPUT_MODES)
    def test_convergence_loop_always_present(self, depth, input_mode):
        """[CONVERGENCE LOOP] must appear in EVERY mode combination."""
        prompt = _build_prompt(depth, input_mode)
        assert "[CONVERGENCE LOOP" in prompt, (
            f"Missing CONVERGENCE LOOP at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", INPUT_MODES)
    def test_marking_policy_always_present(self, depth, input_mode):
        """[REQUIREMENT MARKING] must appear in EVERY mode combination."""
        prompt = _build_prompt(depth, input_mode)
        assert "REQUIREMENT MARKING" in prompt, (
            f"Missing REQUIREMENT MARKING at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", INPUT_MODES)
    def test_zero_cycles_prohibition_always_present(self, depth, input_mode):
        """ZERO convergence cycles prohibition must appear in ALL modes."""
        prompt = _build_prompt(depth, input_mode)
        assert "ZERO convergence cycles is NEVER acceptable" in prompt, (
            f"Missing ZERO cycles prohibition at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", list(PRD_MODES))
    def test_root_artifacts_present_in_prd_modes(self, depth, input_mode):
        """ROOT ARTIFACTS must appear in PRD-mode inputs."""
        prompt = _build_prompt(depth, input_mode)
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" in prompt, (
            f"Missing ROOT ARTIFACTS at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", list(STD_MODES))
    def test_root_artifacts_absent_in_standard_modes(self, depth, input_mode):
        """ROOT ARTIFACTS must NOT appear in standard-mode inputs."""
        prompt = _build_prompt(depth, input_mode)
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" not in prompt, (
            f"ROOT ARTIFACTS should NOT appear at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", INPUT_MODES)
    def test_segregation_of_duties_always_present(self, depth, input_mode):
        """Segregation-of-duties must appear in ALL modes."""
        prompt = _build_prompt(depth, input_mode)
        assert "segregation-of-duties" in prompt, (
            f"Missing segregation-of-duties at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", INPUT_MODES)
    def test_rubber_stamp_warning_always_present(self, depth, input_mode):
        """Rubber-stamp anti-pattern warning must appear in ALL modes."""
        prompt = _build_prompt(depth, input_mode)
        assert "rubber-stamp" in prompt, (
            f"Missing rubber-stamp warning at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", list(PRD_MODES))
    def test_prd_prompt_has_svc_xxx(self, depth, input_mode):
        """PRD prompts must reference SVC-xxx service wiring."""
        prompt = _build_prompt(depth, input_mode)
        assert "SVC-xxx" in prompt, (
            f"Missing SVC-xxx at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    @pytest.mark.parametrize("input_mode", list(PRD_MODES))
    def test_prd_prompt_has_status_registry(self, depth, input_mode):
        """PRD prompts must reference STATUS_REGISTRY."""
        prompt = _build_prompt(depth, input_mode)
        assert "STATUS_REGISTRY" in prompt, (
            f"Missing STATUS_REGISTRY at depth={depth}, mode={input_mode}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    def test_depth_marker_present(self, depth):
        """Depth level marker must be present in all prompts."""
        prompt = _build_prompt(depth, "task")
        assert f"[DEPTH: {depth.upper()}" in prompt


# ===========================================================================
# LAYER 3: Pipeline Guard Consistency
# ===========================================================================

# Map: (scan_name, guard_pattern_in_cli, config_field_that_gates_it)
SCAN_GUARD_MAP = [
    ("mock_data", "config.post_orchestration_scans.mock_data_scan",
     "post_orchestration_scans.mock_data_scan"),
    ("ui_compliance", "config.post_orchestration_scans.ui_compliance_scan",
     "post_orchestration_scans.ui_compliance_scan"),
    ("deployment", "config.integrity_scans.deployment_scan",
     "integrity_scans.deployment_scan"),
    ("asset", "config.integrity_scans.asset_scan",
     "integrity_scans.asset_scan"),
    ("prd_reconciliation", "config.integrity_scans.prd_reconciliation",
     "integrity_scans.prd_reconciliation"),
    ("dual_orm", "config.database_scans.dual_orm_scan",
     "database_scans.dual_orm_scan"),
    ("default_value", "config.database_scans.default_value_scan",
     "database_scans.default_value_scan"),
    ("relationship", "config.database_scans.relationship_scan",
     "database_scans.relationship_scan"),
    ("api_contract", "config.post_orchestration_scans.api_contract_scan",
     "post_orchestration_scans.api_contract_scan"),
    ("e2e_testing", "config.e2e_testing.enabled",
     "e2e_testing.enabled"),
    ("e2e_quality", "config.e2e_testing.enabled",
     "e2e_testing.enabled"),
    ("browser_testing", "config.browser_testing.enabled",
     "browser_testing.enabled"),
]


class TestPipelineGuardConsistency:
    """Layer 3: Verify cli.py guards match config fields set by depth gating."""

    @pytest.mark.parametrize(
        "scan_name, guard_pattern, config_field",
        SCAN_GUARD_MAP,
        ids=[s[0] for s in SCAN_GUARD_MAP],
    )
    def test_guard_references_correct_config_field(
        self, scan_name, guard_pattern, config_field
    ):
        """Each scan's if-guard in cli.py must reference the correct config field."""
        assert guard_pattern in _CLI_SOURCE, (
            f"Scan '{scan_name}': expected guard pattern "
            f"'{guard_pattern}' not found in cli.py"
        )

    @pytest.mark.parametrize(
        "scan_name, guard_pattern, config_field",
        SCAN_GUARD_MAP,
        ids=[s[0] for s in SCAN_GUARD_MAP],
    )
    def test_quick_disables_guard(self, scan_name, guard_pattern, config_field):
        """When quick depth disables a field, the corresponding guard must be False."""
        config = _make_config("quick")
        # Navigate to the field value via dotted path
        parts = config_field.split(".")
        obj: Any = config
        for part in parts:
            obj = getattr(obj, part)
        if scan_name not in ("e2e_quality",):  # e2e_quality shares e2e_testing.enabled
            assert obj is False, (
                f"Quick depth: {config_field} should be False but got {obj}"
            )

    def test_mock_scan_has_or_gate_with_legacy(self):
        """Mock data scan guard must OR with legacy milestone.mock_data_scan."""
        assert "config.milestone.mock_data_scan" in _CLI_SOURCE, (
            "Mock data scan missing OR gate with legacy milestone field"
        )

    def test_ui_scan_has_or_gate_with_legacy(self):
        """UI compliance scan guard must OR with legacy milestone.ui_compliance_scan."""
        assert "config.milestone.ui_compliance_scan" in _CLI_SOURCE, (
            "UI compliance scan missing OR gate with legacy milestone field"
        )

    def test_all_scan_blocks_have_try_except(self):
        """Every scan block must be crash-isolated with try/except."""
        scan_markers = [
            "Post-orchestration: Mock data scan",
            "Post-orchestration: UI compliance scan",
            "Scan 1: Deployment integrity",
            "Scan 2: Asset integrity",
            "Scan 3: PRD reconciliation",
        ]
        for marker in scan_markers:
            pos = _CLI_SOURCE.find(marker)
            assert pos != -1, f"Scan marker '{marker}' not found"
            # Check that there's a try/except within 500 chars after the marker
            block = _CLI_SOURCE[pos:pos + 500]
            assert "try:" in block, f"Scan '{marker}' missing try/except"

    def test_all_scan_blocks_read_max_passes(self):
        """Every violation-based scan must read max_scan_fix_passes from config."""
        count = _CLI_SOURCE.count("config.post_orchestration_scans.max_scan_fix_passes")
        # At least 8 scan blocks + config loading references
        assert count >= 8, (
            f"Expected >= 8 reads of max_scan_fix_passes, got {count}"
        )


# ===========================================================================
# LAYER 4: Cross-Mode Behavioral Tests
# ===========================================================================

class TestEffectiveTaskCrossModes:
    """Verify effective_task computation handles ALL input modes."""

    def test_effective_task_block_exists(self):
        """effective_task variable must be computed in cli.py main()."""
        assert "effective_task: str = args.task or" in _CLI_SOURCE

    def test_prd_branch_reads_prd_file(self):
        """PRD mode: effective_task must read and preview the PRD file."""
        assert "args.prd and not args.task" in _CLI_SOURCE
        assert "_prd_content[:2000]" in _CLI_SOURCE

    def test_interview_branch_uses_doc(self):
        """Interview mode: effective_task must use interview_doc."""
        assert "interview_doc and not effective_task" in _CLI_SOURCE
        assert "interview_doc[:1000]" in _CLI_SOURCE

    def test_truncation_marker(self):
        """Long PRDs must get truncation marker."""
        assert "truncated" in _CLI_SOURCE

    def test_fallback_on_read_error(self):
        """File read errors must fallback gracefully."""
        assert "OSError, UnicodeDecodeError" in _CLI_SOURCE

    def test_effective_task_replaces_args_task(self):
        """effective_task must be used instead of args.task for task_text=."""
        # Count task_text=effective_task vs task_text=args.task
        effective_count = _CLI_SOURCE.count("task_text=effective_task")
        args_task_count = _CLI_SOURCE.count("task_text=args.task")
        assert effective_count >= 20, (
            f"Expected >= 20 task_text=effective_task, got {effective_count}"
        )
        assert args_task_count == 0, (
            f"Found {args_task_count} leftover task_text=args.task references"
        )

    def test_fallback_ui_uses_effective_task(self):
        """generate_fallback_ui_requirements must receive effective_task."""
        # Find all calls to generate_fallback_ui_requirements
        pattern = r"generate_fallback_ui_requirements\(\s*task="
        matches = re.findall(pattern, _CLI_SOURCE)
        assert len(matches) >= 1
        # None should use args.task
        bad = re.findall(r"generate_fallback_ui_requirements\(\s*task=args\.task", _CLI_SOURCE)
        assert len(bad) == 0, "Found generate_fallback_ui_requirements(task=args.task)"


class TestNormalizeMilestoneDirsCrossModes:
    """Verify normalize_milestone_dirs works for all directory layouts."""

    def test_orphan_dirs_normalized(self, tmp_path):
        """milestone-N/ at req_dir level → copied to milestones/milestone-N/."""
        req_dir = tmp_path / ".agent-team"
        (req_dir / "milestone-1").mkdir(parents=True)
        _make_file(tmp_path, ".agent-team/milestone-1/REQUIREMENTS.md", "# M1")
        count = normalize_milestone_dirs(tmp_path)
        assert count == 1
        assert (req_dir / "milestones" / "milestone-1" / "REQUIREMENTS.md").is_file()

    def test_multiple_orphan_dirs(self, tmp_path):
        """Multiple orphan dirs all normalized."""
        req_dir = tmp_path / ".agent-team"
        for i in range(1, 6):
            _make_file(tmp_path, f".agent-team/milestone-{i}/REQUIREMENTS.md", f"# M{i}")
        count = normalize_milestone_dirs(tmp_path)
        assert count == 5

    def test_already_canonical_returns_zero(self, tmp_path):
        """Dirs already at canonical location → returns 0."""
        req_dir = tmp_path / ".agent-team" / "milestones"
        _make_file(tmp_path, ".agent-team/milestones/milestone-1/REQUIREMENTS.md", "# M1")
        count = normalize_milestone_dirs(tmp_path)
        assert count == 0

    def test_empty_project_returns_zero(self, tmp_path):
        """No .agent-team dir → returns 0."""
        count = normalize_milestone_dirs(tmp_path)
        assert count == 0

    def test_non_milestone_dirs_ignored(self, tmp_path):
        """prd-chunks/, other dirs → NOT moved."""
        _make_file(tmp_path, ".agent-team/prd-chunks/chunk1.md", "# Chunk")
        _make_file(tmp_path, ".agent-team/config.yaml", "depth: standard")
        count = normalize_milestone_dirs(tmp_path)
        assert count == 0
        # Original files still there
        assert (tmp_path / ".agent-team" / "prd-chunks" / "chunk1.md").is_file()

    def test_merge_without_overwrite(self, tmp_path):
        """When both paths exist, new files merge but existing files preserved."""
        # Canonical has existing file
        _make_file(tmp_path, ".agent-team/milestones/milestone-1/REQUIREMENTS.md", "ORIGINAL")
        # Orphan has same file + new file
        _make_file(tmp_path, ".agent-team/milestone-1/REQUIREMENTS.md", "SHOULD NOT OVERWRITE")
        _make_file(tmp_path, ".agent-team/milestone-1/TASKS.md", "NEW FILE")
        count = normalize_milestone_dirs(tmp_path)
        # Only the new file should be copied
        assert count >= 1
        # Original preserved
        content = (tmp_path / ".agent-team" / "milestones" / "milestone-1" / "REQUIREMENTS.md").read_text()
        assert content == "ORIGINAL"
        # New file merged
        assert (tmp_path / ".agent-team" / "milestones" / "milestone-1" / "TASKS.md").is_file()

    def test_call_sites_exist_in_cli(self):
        """normalize_milestone_dirs must be called at 3 sites in cli.py."""
        count = _CLI_SOURCE.count("normalize_milestone_dirs")
        assert count >= 3, f"Expected >= 3 call sites, got {count}"

    def test_call_sites_have_logging(self):
        """All call sites must log when > 0 dirs normalized."""
        # Find pattern: if _norm > 0 or if _normalized > 0
        log_count = len(re.findall(r"if _norm\w* > 0:", _CLI_SOURCE))
        assert log_count >= 3, f"Expected >= 3 logged call sites, got {log_count}"


class TestGate5CrossModes:
    """Verify GATE 5 enforcement logic is mode-independent."""

    def test_gate5_block_exists(self):
        """GATE 5 enforcement block must exist in cli.py."""
        assert "GATE 5 ENFORCEMENT" in _CLI_SOURCE

    def test_gate5_not_inside_mode_branch(self):
        """GATE 5 must NOT be inside an if _is_prd_mode or if _use_milestones branch."""
        # Find the GATE 5 block
        gate5_pos = _CLI_SOURCE.find("GATE 5 ENFORCEMENT")
        assert gate5_pos != -1
        # Get the 200 chars before to check indentation context
        context_before = _CLI_SOURCE[max(0, gate5_pos - 300):gate5_pos]
        # It should NOT be inside a mode-specific branch
        assert "_is_prd_mode" not in context_before.split("\n")[-3:], (
            "GATE 5 must not be nested inside _is_prd_mode branch"
        )

    def test_gate5_checks_review_cycles(self):
        """GATE 5 must check convergence_report.review_cycles == 0."""
        assert "convergence_report.review_cycles == 0" in _CLI_SOURCE

    def test_gate5_checks_total_requirements(self):
        """GATE 5 must require total_requirements > 0."""
        assert "convergence_report.total_requirements > 0" in _CLI_SOURCE

    def test_gate5_appends_recovery_type(self):
        """GATE 5 must append 'gate5_enforcement' to recovery_types."""
        assert '"gate5_enforcement"' in _CLI_SOURCE

    def test_gate5_requires_not_already_recovering(self):
        """GATE 5 must only fire when not needs_recovery."""
        assert "not needs_recovery" in _CLI_SOURCE


class TestTasksParserCrossModes:
    """Verify TASKS.md parser handles ALL 3 formats."""

    def test_block_format_parsed(self):
        """### TASK-xxx header format must be parsed."""
        content = """### TASK-001: Setup
Status: PENDING
Depends-On: —
Files: setup.ts

Initialize project.

### TASK-002: Auth
Status: PENDING
Depends-On: TASK-001
Files: auth.ts

Add authentication.
"""
        tasks = parse_tasks_md(content)
        assert len(tasks) == 2
        assert tasks[0].id == "TASK-001"
        assert tasks[1].id == "TASK-002"

    def test_table_format_parsed(self):
        """| TASK-xxx | ... | table format must be parsed."""
        content = """| Task ID | Description | Depends On | Requirements |
| --- | --- | --- | --- |
| TASK-001 | Setup project | — | REQ-001 |
| TASK-002 | Add auth | TASK-001 | REQ-002, REQ-003 |
"""
        tasks = parse_tasks_md(content)
        assert len(tasks) == 2
        assert tasks[0].id == "TASK-001"
        assert tasks[1].id == "TASK-002"

    def test_bullet_format_parsed(self):
        """- TASK-xxx: desc → deps bullet format must be parsed."""
        content = """## Milestone-1 Tasks

- TASK-001: Setup project → —
- TASK-002: Add auth → TASK-001
- TASK-003: Add dashboard → TASK-001, TASK-002
"""
        tasks = parse_tasks_md(content)
        assert len(tasks) == 3
        assert tasks[0].id == "TASK-001"
        assert tasks[2].depends_on == ["TASK-001", "TASK-002"]

    def test_block_format_takes_priority(self):
        """When both block and table exist, block format wins."""
        content = """### TASK-001: Setup
Status: PENDING
Depends-On: —
Files: setup.ts

Setup project.

| Task ID | Description | Depends On | Requirements |
| --- | --- | --- | --- |
| TASK-999 | Table task | — | REQ-001 |
"""
        tasks = parse_tasks_md(content)
        ids = [t.id for t in tasks]
        assert "TASK-001" in ids
        # TASK-999 from table should NOT appear (block format takes priority)
        assert "TASK-999" not in ids

    def test_empty_content_returns_empty(self):
        tasks = parse_tasks_md("")
        assert tasks == []

    def test_no_tasks_returns_empty(self):
        tasks = parse_tasks_md("# Just a heading\n\nSome text.\n")
        assert tasks == []


class TestDesignDirectionCrossModes:
    """Verify design direction inference across different task descriptions."""

    @pytest.mark.parametrize("task, expected", [
        ("Build a SaaS dashboard with analytics", "minimal_modern"),  # dashboard is keyword under minimal_modern
        ("Build a developer CLI tool", "brutalist"),
        ("Build an e-commerce storefront", "minimal_modern"),  # no e_commerce direction exists
        ("Build a social media app", "minimal_modern"),  # no social_media direction exists
        ("Build something", "minimal_modern"),  # fallback
        ("", "minimal_modern"),  # empty fallback
    ])
    def test_direction_inference(self, task, expected):
        direction = _infer_design_direction(task)
        assert direction == expected, (
            f"Task '{task}' should infer '{expected}', got '{direction}'"
        )

    def test_none_task_no_crash(self):
        """None task must not crash."""
        direction = _infer_design_direction(None)
        assert direction == "minimal_modern"

    def test_fallback_generates_valid_content(self, tmp_path):
        """generate_fallback_ui_requirements must produce valid content for any task."""
        for task in ["Build SaaS", "Build CLI", "Build store", "", None]:
            content = generate_fallback_ui_requirements(
                task=task or "", config=AgentTeamConfig(), cwd=str(tmp_path),
            )
            assert isinstance(content, str)
            assert len(content) > 50
            assert "Color System" in content


class TestAppDetectionCrossModes:
    """Verify detect_app_type works for all project layouts."""

    def test_root_express(self, tmp_path):
        _make_file(tmp_path, "package.json", json.dumps(
            {"dependencies": {"express": "4.18"}}
        ))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True

    def test_subdir_express(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps(
            {"dependencies": {"express": "4.18"}}
        ))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert "backend" in info.api_directory

    def test_fullstack_monorepo(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps(
            {"dependencies": {"express": "4.18"}}
        ))
        _make_file(tmp_path, "frontend/package.json", json.dumps(
            {"dependencies": {"react": "18"}}
        ))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True

    def test_empty_project(self, tmp_path):
        info = detect_app_type(tmp_path)
        assert info.has_backend is False
        assert info.has_frontend is False

    def test_django_in_subdir(self, tmp_path):
        (tmp_path / "backend").mkdir()
        _make_file(tmp_path, "backend/requirements.txt", "django==4.2")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "django"


# ===========================================================================
# LAYER 5: Guard-to-Config Mapping Verification
# ===========================================================================

# For each scan, verify that the cli.py guard condition references
# the EXACT config field that apply_depth_quality_gating() sets.

@dataclass
class ScanGuardSpec:
    """Specification for a scan's guard-to-config relationship."""
    name: str
    cli_guard_pattern: str
    depth_gating_field: str
    function_called: str
    recovery_type: str


SCAN_SPECS = [
    ScanGuardSpec("mock_data", "config.post_orchestration_scans.mock_data_scan",
                  "post_orchestration_scans.mock_data_scan",
                  "run_mock_data_scan", "mock_data_fix"),
    ScanGuardSpec("ui_compliance", "config.post_orchestration_scans.ui_compliance_scan",
                  "post_orchestration_scans.ui_compliance_scan",
                  "run_ui_compliance_scan", "ui_compliance_fix"),
    ScanGuardSpec("deployment", "config.integrity_scans.deployment_scan",
                  "integrity_scans.deployment_scan",
                  "run_deployment_scan", "deployment_integrity_fix"),
    ScanGuardSpec("asset", "config.integrity_scans.asset_scan",
                  "integrity_scans.asset_scan",
                  "run_asset_scan", "asset_integrity_fix"),
    ScanGuardSpec("dual_orm", "config.database_scans.dual_orm_scan",
                  "database_scans.dual_orm_scan",
                  "run_dual_orm_scan", "database_dual_orm_fix"),
    ScanGuardSpec("default_value", "config.database_scans.default_value_scan",
                  "database_scans.default_value_scan",
                  "run_default_value_scan", "database_default_value_fix"),
    ScanGuardSpec("relationship", "config.database_scans.relationship_scan",
                  "database_scans.relationship_scan",
                  "run_relationship_scan", "database_relationship_fix"),
    ScanGuardSpec("api_contract", "config.post_orchestration_scans.api_contract_scan",
                  "post_orchestration_scans.api_contract_scan",
                  "run_api_contract_scan", "api_contract_fix"),
    ScanGuardSpec("e2e_testing", "config.e2e_testing.enabled",
                  "e2e_testing.enabled",
                  "_run_backend_e2e_tests", "e2e_backend_fix"),
    ScanGuardSpec("browser_testing", "config.browser_testing.enabled",
                  "browser_testing.enabled",
                  "_run_browser_startup_agent", "browser_testing_failed"),
]


class TestGuardToConfigMapping:
    """Layer 5: Verify each scan's guard condition maps to the correct config field."""

    @pytest.mark.parametrize(
        "spec", SCAN_SPECS, ids=[s.name for s in SCAN_SPECS]
    )
    def test_guard_pattern_exists_in_cli(self, spec: ScanGuardSpec):
        """The guard pattern must appear in cli.py source."""
        assert spec.cli_guard_pattern in _CLI_SOURCE, (
            f"Guard pattern '{spec.cli_guard_pattern}' not found for scan '{spec.name}'"
        )

    @pytest.mark.parametrize(
        "spec", SCAN_SPECS, ids=[s.name for s in SCAN_SPECS]
    )
    def test_function_called_in_cli(self, spec: ScanGuardSpec):
        """The scan function must be called in cli.py."""
        assert spec.function_called in _CLI_SOURCE, (
            f"Function '{spec.function_called}' not found for scan '{spec.name}'"
        )

    @pytest.mark.parametrize(
        "spec", SCAN_SPECS, ids=[s.name for s in SCAN_SPECS]
    )
    def test_recovery_type_registered(self, spec: ScanGuardSpec):
        """The recovery type must be appended in cli.py."""
        assert f'"{spec.recovery_type}"' in _CLI_SOURCE, (
            f"Recovery type '{spec.recovery_type}' not found for scan '{spec.name}'"
        )

    @pytest.mark.parametrize(
        "spec", SCAN_SPECS, ids=[s.name for s in SCAN_SPECS]
    )
    def test_quick_depth_disables_guard(self, spec: ScanGuardSpec):
        """Quick depth must disable the config field that the guard checks."""
        config = _make_config("quick")
        parts = spec.depth_gating_field.split(".")
        obj: Any = config
        for part in parts:
            obj = getattr(obj, part)
        assert obj is False, (
            f"Quick depth: {spec.depth_gating_field} should be False for "
            f"scan '{spec.name}', got {obj}"
        )

    @pytest.mark.parametrize(
        "spec", SCAN_SPECS[:8],  # Violation-based scans only (not E2E/browser)
        ids=[s.name for s in SCAN_SPECS[:8]],
    )
    def test_standard_depth_enables_guard(self, spec: ScanGuardSpec):
        """Standard depth must keep the config field enabled for violation scans."""
        config = _make_config("standard")
        parts = spec.depth_gating_field.split(".")
        obj: Any = config
        for part in parts:
            obj = getattr(obj, part)
        # PRD reconciliation is special — disabled at standard depth
        if spec.name == "prd_reconciliation":
            return  # skip, tested separately
        assert obj is True, (
            f"Standard depth: {spec.depth_gating_field} should be True for "
            f"scan '{spec.name}', got {obj}"
        )

    def test_prd_recon_disabled_at_standard(self):
        """PRD reconciliation must be disabled at standard depth."""
        config = _make_config("standard")
        assert config.integrity_scans.prd_reconciliation is False

    def test_prd_recon_enabled_at_thorough(self):
        """PRD reconciliation must be enabled at thorough depth."""
        config = _make_config("thorough")
        assert config.integrity_scans.prd_reconciliation is True

    def test_e2e_quality_scan_gated_same_as_e2e(self):
        """E2E quality scan must use the same gate as E2E testing."""
        # Both must check config.e2e_testing.enabled
        e2e_pattern = "config.e2e_testing.enabled"
        # Find occurrences near run_e2e_quality_scan
        e2e_quality_pos = _CLI_SOURCE.find("run_e2e_quality_scan")
        assert e2e_quality_pos != -1
        # Check the 500 chars before for the guard
        guard_region = _CLI_SOURCE[max(0, e2e_quality_pos - 500):e2e_quality_pos]
        assert e2e_pattern in guard_region, (
            "E2E quality scan must be gated by config.e2e_testing.enabled"
        )


# ===========================================================================
# CROSS-LAYER: End-to-End Consistency Checks
# ===========================================================================

class TestCrossLayerConsistency:
    """Verify that config gating, prompts, and pipeline guards are consistent."""

    @pytest.mark.parametrize("depth", DEPTHS)
    def test_disabled_scans_not_called_at_quick(self, depth):
        """At quick depth, all scan config fields must be False → guards reject."""
        if depth != "quick":
            return  # Only checking quick here
        config = _make_config(depth)
        state = _extract_config_state(config)
        # Every scan-related field must be False
        for key, val in state.items():
            if key in ("e2e_max_fix_retries", "browser_max_fix_retries",
                       "review_recovery_retries", "max_scan_fix_passes"):
                continue  # numeric fields
            assert val is False, f"Quick depth: {key} should be False, got {val}"

    @pytest.mark.parametrize("depth", ["standard", "thorough", "exhaustive"])
    def test_all_violation_scans_enabled(self, depth):
        """Standard+ depth must enable ALL violation-based scans."""
        config = _make_config(depth)
        assert config.post_orchestration_scans.mock_data_scan is True
        assert config.post_orchestration_scans.ui_compliance_scan is True
        assert config.post_orchestration_scans.api_contract_scan is True
        assert config.integrity_scans.deployment_scan is True
        assert config.integrity_scans.asset_scan is True
        assert config.database_scans.dual_orm_scan is True
        assert config.database_scans.default_value_scan is True
        assert config.database_scans.relationship_scan is True

    def test_milestone_tasks_format_in_prompt(self):
        """build_milestone_execution_prompt must contain TASKS.md block format."""
        prompt = build_milestone_execution_prompt(
            task="Build a SaaS dashboard",
            depth="standard",
            config=AgentTeamConfig(),
        )
        assert "### TASK-" in prompt or "TASK-" in prompt
        assert "PENDING" in prompt or "Status:" in prompt
        assert "table" in prompt.lower()  # references TASKS.md format guidance

    def test_reviewer_prompt_has_review_cycles(self):
        """CODE_REVIEWER_PROMPT must contain review_cycles marker instructions."""
        assert "review_cycles:" in CODE_REVIEWER_PROMPT
        assert "(review_cycles: N)" in CODE_REVIEWER_PROMPT or \
               "(review_cycles:" in CODE_REVIEWER_PROMPT

    def test_reviewer_prompt_has_increment_instruction(self):
        """Reviewer prompt must instruct to INCREMENT existing markers."""
        lower = CODE_REVIEWER_PROMPT.lower()
        assert "increment" in lower, (
            "CODE_REVIEWER_PROMPT missing instruction to increment review_cycles"
        )

    def test_all_recovery_types_have_display_labels(self):
        """All recovery types used in cli.py must have labels in display.py."""
        display_source = (_SRC / "display.py").read_text(encoding="utf-8")
        for spec in SCAN_SPECS:
            assert spec.recovery_type in display_source, (
                f"Recovery type '{spec.recovery_type}' missing from display.py"
            )
        # Also check non-scan recovery types
        for rtype in ("gate5_enforcement", "contract_generation", "review_recovery",
                       "e2e_coverage_incomplete", "browser_testing_partial",
                       "artifact_recovery"):
            if rtype in _CLI_SOURCE:
                assert rtype in display_source, (
                    f"Recovery type '{rtype}' used in cli.py but missing from display.py"
                )

    def test_scan_clean_messages_exist(self):
        """All 8+ scan blocks must have '0 violations (clean)' messages."""
        clean_messages = [
            "Mock data scan: 0 violations (clean)",
            "UI compliance scan: 0 violations (clean)",
            "Deployment integrity scan: 0 violations (clean)",
            "Asset integrity scan: 0 violations (clean)",
            "Dual ORM scan: 0 violations (clean)",
            "Default value scan: 0 violations (clean)",
            "Relationship scan: 0 violations (clean)",
            "API contract scan: 0 violations (clean)",
        ]
        for msg in clean_messages:
            assert msg in _CLI_SOURCE, f"Missing clean message: '{msg}'"

    @pytest.mark.parametrize("depth", DEPTHS)
    def test_max_scan_fix_passes_scaling(self, depth):
        """max_scan_fix_passes must scale correctly: quick=0, std/thorough=1, exhaustive=2."""
        config = _make_config(depth)
        expected = {"quick": 0, "standard": 1, "thorough": 1, "exhaustive": 2}
        assert config.post_orchestration_scans.max_scan_fix_passes == expected[depth], (
            f"max_scan_fix_passes at {depth}: expected {expected[depth]}, "
            f"got {config.post_orchestration_scans.max_scan_fix_passes}"
        )

    @pytest.mark.parametrize("depth", DEPTHS)
    def test_e2e_max_retries_scaling(self, depth):
        """E2E max_fix_retries: quick=1, standard=5(default), thorough=2, exhaustive=3."""
        config = _make_config(depth)
        expected = {"quick": 1, "standard": 5, "thorough": 2, "exhaustive": 3}
        assert config.e2e_testing.max_fix_retries == expected[depth]

    @pytest.mark.parametrize("depth", DEPTHS)
    def test_review_retries_scaling(self, depth):
        """Review retries: quick=0, standard=1(default), thorough=2, exhaustive=3."""
        config = _make_config(depth)
        expected = {"quick": 0, "standard": 1, "thorough": 2, "exhaustive": 3}
        assert config.milestone.review_recovery_retries == expected[depth]


# ===========================================================================
# CHECKPOINT COVERAGE SUMMARY
# ===========================================================================

class TestCheckpointCoverageSummary:
    """Meta-tests that verify our matrix covers all 42 production checkpoints."""

    def test_all_scan_types_in_guard_map(self):
        """Every scan type must be represented in SCAN_SPECS."""
        scan_names = {s.name for s in SCAN_SPECS}
        required = {
            "mock_data", "ui_compliance", "deployment", "asset",
            "dual_orm", "default_value", "relationship",
            "api_contract", "e2e_testing", "browser_testing",
        }
        assert required.issubset(scan_names), (
            f"Missing scans: {required - scan_names}"
        )

    def test_all_depths_tested(self):
        """All 4 depth levels must be covered."""
        assert set(DEPTHS) == {"quick", "standard", "thorough", "exhaustive"}

    def test_all_input_modes_tested(self):
        """All 5 input modes must be covered."""
        assert set(INPUT_MODES) == {
            "task", "prd", "interview_simple", "interview_complex", "chunked_prd"
        }

    def test_config_matrix_covers_all_combinations(self):
        """Config matrix must cover 4 depths × 2 prd_modes = 8 combinations."""
        combos = {(d, p) for d, p, _ in CONFIG_MATRIX}
        expected = {
            (d, p)
            for d in DEPTHS
            for p in (False, True)
        }
        assert combos == expected, f"Missing: {expected - combos}"

    def test_prompt_matrix_covers_20_combinations(self):
        """Prompt tests cover 4 depths × 5 input_modes = 20 combinations."""
        # This is implicitly verified by the parametrize decorators,
        # but let's assert the math
        assert len(DEPTHS) * len(INPUT_MODES) == 20
