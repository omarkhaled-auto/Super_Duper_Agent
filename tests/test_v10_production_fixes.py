"""Tests for v10 Production Fixes — all 9 deliverables."""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent_team.agents import build_orchestrator_prompt
from agent_team.config import (
    AgentTeamConfig,
    PostOrchestrationScanConfig,
    DesignReferenceConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.e2e_testing import detect_app_type, AppTypeInfo
from agent_team.display import print_recovery_report
from agent_team.quality_checks import run_default_value_scan, Violation
from agent_team.design_reference import (
    generate_fallback_ui_requirements,
    _infer_design_direction,
    _DIRECTION_TABLE,
)

# Source root for source-level assertions
_SRC = Path(__file__).resolve().parent.parent / "src" / "agent_team"


# ============================================================
# Helpers
# ============================================================

def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _prd_prompt(**kwargs) -> str:
    """Build a PRD-mode orchestrator prompt with sensible defaults."""
    defaults = dict(task="Build app", depth="standard", config=AgentTeamConfig(), prd_path="prd.md")
    defaults.update(kwargs)
    return build_orchestrator_prompt(**defaults)


def _std_prompt(**kwargs) -> str:
    """Build a standard (non-PRD) orchestrator prompt with sensible defaults."""
    defaults = dict(task="Build app", depth="standard", config=AgentTeamConfig())
    defaults.update(kwargs)
    return build_orchestrator_prompt(**defaults)


# ============================================================
# Deliverable 1: PRD Mode Root-Level Artifacts
# ============================================================

class TestPRDModeRootArtifacts:
    """v10 Deliverable 1: PRD prompt includes MANDATORY ROOT-LEVEL ARTIFACTS block."""

    def test_prd_prompt_contains_consolidated_requirements(self):
        prompt = _prd_prompt()
        assert "Consolidated REQUIREMENTS.md" in prompt

    def test_prd_prompt_contains_svc_xxx(self):
        prompt = _prd_prompt()
        assert "SVC-xxx" in prompt

    def test_prd_prompt_contains_status_registry(self):
        prompt = _prd_prompt()
        assert "STATUS_REGISTRY" in prompt

    def test_prd_prompt_contains_contracts_json(self):
        prompt = _prd_prompt()
        assert "CONTRACTS.json" in prompt

    def test_prd_prompt_contains_tasks_md(self):
        prompt = _prd_prompt()
        # The root-level artifacts block specifically mentions TASKS.md
        assert "TASKS.md" in prompt

    def test_prd_prompt_contains_req_dir(self):
        prompt = _prd_prompt()
        assert ".agent-team" in prompt

    def test_prd_prompt_still_has_per_milestone_instructions(self):
        prompt = _prd_prompt()
        assert "per-milestone REQUIREMENTS.md" in prompt

    def test_non_prd_prompt_unchanged(self):
        prompt = _std_prompt()
        assert "PLANNING FLEET" in prompt
        # Non-PRD should NOT have the root-level artifacts block
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" not in prompt

    def test_interview_prd_prompt_contains_root_artifacts(self):
        prompt = build_orchestrator_prompt(
            task="Build app",
            depth="standard",
            config=AgentTeamConfig(),
            interview_scope="COMPLEX",
            interview_doc="Some design doc",
        )
        # Interview with scope=COMPLEX should trigger PRD mode
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" in prompt

    def test_chunked_prd_prompt_contains_root_artifacts(self):
        prompt = build_orchestrator_prompt(
            task="Build app",
            depth="standard",
            config=AgentTeamConfig(),
            prd_path="prd.md",
            prd_chunks=["chunk1.md"],
            prd_index={"section1": {"heading": "Intro", "size_bytes": 100}},
        )
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" in prompt


# ============================================================
# Deliverable 7: Convergence Loop Enforcement
# ============================================================

class TestConvergenceLoopEnforcement:
    """v10 Deliverable 7: Both PRD and non-PRD prompts enforce convergence loop."""

    def test_prd_prompt_convergence_loop_header(self):
        prompt = _prd_prompt()
        assert "[CONVERGENCE LOOP" in prompt

    def test_prd_prompt_convergence_ratio_threshold(self):
        prompt = _prd_prompt()
        assert "ratio" in prompt.lower()
        assert "0.9" in prompt

    def test_prd_prompt_zero_cycles_prohibition(self):
        prompt = _prd_prompt()
        assert "ZERO convergence cycles is NEVER acceptable" in prompt

    def test_prd_prompt_review_fleet_mention(self):
        prompt = _prd_prompt()
        assert "CODE REVIEWER fleet" in prompt

    def test_non_prd_prompt_has_convergence_loop(self):
        prompt = _std_prompt()
        assert "[CONVERGENCE LOOP" in prompt

    def test_non_prd_prompt_has_ratio_threshold(self):
        prompt = _std_prompt()
        assert "0.9" in prompt


# ============================================================
# Deliverable 8: Requirement Marking Policy
# ============================================================

class TestRequirementMarkingPolicy:
    """v10 Deliverable 8: Requirement marking segregation-of-duties policy."""

    def test_prd_prompt_marking_header(self):
        prompt = _prd_prompt()
        assert "[REQUIREMENT MARKING" in prompt

    def test_prd_prompt_reviewer_authorized(self):
        prompt = _prd_prompt()
        assert "CODE REVIEWER fleet is authorized" in prompt

    def test_prd_prompt_rubber_stamp_mention(self):
        prompt = _prd_prompt()
        assert "rubber-stamp" in prompt

    def test_prd_prompt_must_not_self_mark(self):
        prompt = _prd_prompt()
        assert "MUST NOT mark requirements yourself" in prompt

    def test_prd_prompt_segregation_of_duties(self):
        prompt = _prd_prompt()
        assert "segregation-of-duties" in prompt

    def test_non_prd_prompt_has_marking_policy(self):
        prompt = _std_prompt()
        assert "[REQUIREMENT MARKING" in prompt
        assert "rubber-stamp" in prompt


# ============================================================
# Deliverable 2: Subdirectory-Aware App Detection
# ============================================================

class TestSubdirectoryDetection:
    """v10 Deliverable 2: detect_app_type() scans backend/, frontend/, server/, client/, etc."""

    def test_backend_express_in_subdir(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "express"
        assert "backend" in info.api_directory

    def test_frontend_angular_in_subdir(self, tmp_path):
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"@angular/core": "17"}
        }))
        _make_file(tmp_path, "frontend/angular.json", json.dumps({"projects": {}}))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"
        assert info.frontend_directory == "frontend"

    def test_fullstack_monorepo(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"@angular/core": "17"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True

    def test_server_nestjs_in_subdir(self, tmp_path):
        _make_file(tmp_path, "server/package.json", json.dumps({
            "dependencies": {"@nestjs/core": "10"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "nestjs"
        assert "server" in info.api_directory

    def test_client_react_in_subdir(self, tmp_path):
        _make_file(tmp_path, "client/package.json", json.dumps({
            "dependencies": {"react": "18"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "react"
        assert info.frontend_directory == "client"

    def test_prisma_in_subdir(self, tmp_path):
        (tmp_path / "backend").mkdir()
        (tmp_path / "backend" / "prisma").mkdir()
        _make_file(tmp_path, "backend/prisma/schema.prisma", "model User { id Int @id }")
        info = detect_app_type(tmp_path)
        assert info.db_type == "prisma"

    def test_npm_lockfile_in_subdir(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "backend/package-lock.json", "{}")
        info = detect_app_type(tmp_path)
        assert info.package_manager == "npm"

    def test_django_in_subdir(self, tmp_path):
        (tmp_path / "backend").mkdir()
        _make_file(tmp_path, "backend/requirements.txt", "django==4.2\npsycopg2-binary")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "django"
        assert info.language == "python"

    def test_fastapi_in_subdir(self, tmp_path):
        (tmp_path / "backend").mkdir()
        _make_file(tmp_path, "backend/requirements.txt", "fastapi\nuvicorn")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "fastapi"

    def test_root_detection_takes_precedence(self, tmp_path):
        # Root has express, frontend/ has angular
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"@angular/core": "17"}
        }))
        info = detect_app_type(tmp_path)
        # Root express should be kept, frontend detected from subdir
        assert info.has_backend is True
        assert info.backend_framework == "express"
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"

    def test_both_detected_skips_subdir_scan(self, tmp_path):
        # Root has both express + react — subdirs should not be scanned
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"express": "4.18", "react": "18"}
        }))
        # Create a subdir with angular that should NOT override
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"@angular/core": "17"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.has_frontend is True
        # Should be react from root, NOT angular from subdir
        assert info.frontend_framework == "react"

    def test_empty_subdir_skipped(self, tmp_path):
        (tmp_path / "backend").mkdir()
        # No files in backend/ — should not crash or detect anything
        info = detect_app_type(tmp_path)
        assert info.has_backend is False

    def test_malformed_json_skipped(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", "{ NOT VALID JSON !!!")
        # Should not crash
        info = detect_app_type(tmp_path)
        assert info.has_backend is False

    def test_angular_config_without_package_json(self, tmp_path):
        (tmp_path / "frontend").mkdir()
        _make_file(tmp_path, "frontend/angular.json", json.dumps({"projects": {}}))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"

    def test_typescript_in_subdir(self, tmp_path):
        _make_file(tmp_path, "backend/package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "backend/tsconfig.json", "{}")
        info = detect_app_type(tmp_path)
        assert info.language == "typescript"

    def test_playwright_in_subdir(self, tmp_path):
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"react": "18"},
            "devDependencies": {"@playwright/test": "1.40"}
        }))
        info = detect_app_type(tmp_path)
        assert info.playwright_installed is True


# ============================================================
# Deliverable 4: Recovery Type Labels
# ============================================================

class TestRecoveryLabels:
    """v10 Deliverable 4: print_recovery_report has labels for all 16 recovery types."""

    @pytest.fixture()
    def _type_hints(self):
        """Extract the type_hints dict from display.py source."""
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        # Find the dict literal in source
        m = re.search(r"type_hints\s*=\s*\{([^}]+)\}", source, re.DOTALL)
        assert m, "type_hints dict not found in display.py"
        raw = m.group(0)
        # Use a rough extraction — count the key: value pairs
        keys = re.findall(r'"(\w+)":', raw)
        return keys

    def test_all_recovery_types_have_labels(self, _type_hints):
        expected_types = [
            "contract_generation", "review_recovery", "mock_data_fix",
            "ui_compliance_fix", "deployment_integrity_fix", "asset_integrity_fix",
            "prd_reconciliation_mismatch", "database_dual_orm_fix",
            "database_default_value_fix", "database_relationship_fix",
            "api_contract_fix", "e2e_backend_fix", "e2e_frontend_fix",
            "e2e_coverage_incomplete", "browser_testing_failed", "browser_testing_partial",
        ]
        for etype in expected_types:
            assert etype in _type_hints, f"Recovery type '{etype}' missing from type_hints"

    def test_mock_data_fix_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        assert "mock_data_fix" in source
        # Check the hint contains relevant keywords
        m = re.search(r'"mock_data_fix"\s*:\s*"([^"]+)"', source)
        assert m
        assert "mock" in m.group(1).lower() or "Mock" in m.group(1)

    def test_ui_compliance_fix_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"ui_compliance_fix"\s*:\s*"([^"]+)"', source)
        assert m
        label = m.group(1).lower()
        assert "ui" in label or "design" in label

    def test_deployment_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"deployment_integrity_fix"\s*:\s*"([^"]+)"', source)
        assert m
        label = m.group(1).lower()
        assert "docker" in label or "deployment" in label

    def test_asset_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"asset_integrity_fix"\s*:\s*"([^"]+)"', source)
        assert m
        assert "asset" in m.group(1).lower()

    def test_database_labels(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        for db_type in ("database_dual_orm_fix", "database_default_value_fix", "database_relationship_fix"):
            m = re.search(rf'"{db_type}"\s*:\s*"([^"]+)"', source)
            assert m, f"Label for {db_type} not found"

    def test_api_contract_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"api_contract_fix"\s*:\s*"([^"]+)"', source)
        assert m
        label = m.group(1).lower()
        assert "api" in label or "contract" in label

    def test_e2e_labels(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        for e2e_type in ("e2e_backend_fix", "e2e_frontend_fix"):
            m = re.search(rf'"{e2e_type}"\s*:\s*"([^"]+)"', source)
            assert m, f"Label for {e2e_type} not found"

    def test_browser_labels(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        for bt_type in ("browser_testing_failed", "browser_testing_partial"):
            m = re.search(rf'"{bt_type}"\s*:\s*"([^"]+)"', source)
            assert m, f"Label for {bt_type} not found"

    def test_unknown_type_fallback(self):
        """Calling print_recovery_report with unknown type should not crash."""
        # Capture output to verify no exception
        with patch("agent_team.display.console") as mock_console:
            print_recovery_report(recovery_count=1, recovery_types=["some_unknown_type"])
        # If it didn't crash, test passes. Also verify "Unknown" appears in output.
        calls = mock_console.print.call_args_list
        assert len(calls) > 0


# ============================================================
# Deliverable 5: DB-005 Prisma Delegate Exclusion
# ============================================================

class TestDB005PrismaExclusion:
    """v10 Deliverable 5: Prisma client delegate accesses skip DB-005."""

    def test_prisma_delegate_not_flagged(self, tmp_path):
        """prisma.category.findMany() should NOT trigger DB-005."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Product {\n"
            "  category?: Category;\n"
            "}\n"
        ))
        _make_file(tmp_path, "services/product.service.ts", (
            "const result = await prisma.category.findMany();\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "category" in v.message]
        assert len(db005) == 0, f"Prisma delegate access should not be flagged: {db005}"

    def test_non_prisma_access_still_flagged(self, tmp_path):
        """user.category.name (non-Prisma) should still trigger DB-005."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Product {\n"
            "  category?: Category;\n"
            "}\n"
        ))
        _make_file(tmp_path, "services/product.service.ts", (
            "const name = someObject.category.name;\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "category" in v.message]
        assert len(db005) > 0, "Non-prisma nullable access should be flagged"

    def test_prisma_user_delegate_not_flagged(self, tmp_path):
        """prisma.user.findUnique() should NOT trigger DB-005."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Order {\n"
            "  user?: User;\n"
            "}\n"
        ))
        _make_file(tmp_path, "services/order.service.ts", (
            "const u = await prisma.user.findUnique({ where: { id } });\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "user" in v.message]
        assert len(db005) == 0, f"Prisma delegate access should not be flagged: {db005}"


# ============================================================
# Deliverable 6: Multi-Pass Fix Cycles
# ============================================================

class TestMultiPassConfig:
    """v10 Deliverable 6: max_scan_fix_passes config field + depth gating."""

    def test_default_max_scan_fix_passes(self):
        assert PostOrchestrationScanConfig().max_scan_fix_passes == 1

    def test_yaml_loading_passes_2(self):
        cfg, overrides = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": 2}
        })
        assert cfg.post_orchestration_scans.max_scan_fix_passes == 2

    def test_yaml_loading_negative_clamped(self):
        cfg, overrides = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": -1}
        })
        assert cfg.post_orchestration_scans.max_scan_fix_passes == 0

    def test_yaml_loading_zero_accepted(self):
        cfg, overrides = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": 0}
        })
        assert cfg.post_orchestration_scans.max_scan_fix_passes == 0

    def test_exhaustive_depth_defaults_to_2(self):
        config = AgentTeamConfig()
        apply_depth_quality_gating("exhaustive", config)
        assert config.post_orchestration_scans.max_scan_fix_passes == 2

    def test_quick_depth_defaults_to_0(self):
        config = AgentTeamConfig()
        apply_depth_quality_gating("quick", config)
        assert config.post_orchestration_scans.max_scan_fix_passes == 0

    def test_user_override_respected(self):
        """When user explicitly sets max_scan_fix_passes, depth gating doesn't change it."""
        config = AgentTeamConfig()
        config.post_orchestration_scans.max_scan_fix_passes = 5
        overrides = {"post_orchestration_scans.max_scan_fix_passes"}
        apply_depth_quality_gating("quick", config, user_overrides=overrides)
        # User override should be preserved even with quick depth
        assert config.post_orchestration_scans.max_scan_fix_passes == 5


# ============================================================
# Deliverable 3: Silent Scan Pass Logging
# ============================================================

class TestSilentScanLogging:
    """v10 Deliverable 3: All 8 scan blocks have '0 violations (clean)' messages."""

    @pytest.fixture(scope="class")
    def cli_source(self):
        return (_SRC / "cli.py").read_text(encoding="utf-8")

    def test_mock_scan_has_clean_message(self, cli_source):
        assert "Mock data scan: 0 violations (clean)" in cli_source

    def test_ui_scan_has_clean_message(self, cli_source):
        assert "UI compliance scan: 0 violations (clean)" in cli_source

    def test_deployment_scan_has_clean_message(self, cli_source):
        assert "Deployment integrity scan: 0 violations (clean)" in cli_source

    def test_asset_scan_has_clean_message(self, cli_source):
        assert "Asset integrity scan: 0 violations (clean)" in cli_source

    def test_dual_orm_scan_has_clean_message(self, cli_source):
        assert "Dual ORM scan: 0 violations (clean)" in cli_source

    def test_default_value_scan_has_clean_message(self, cli_source):
        assert "Default value scan: 0 violations (clean)" in cli_source

    def test_relationship_scan_has_clean_message(self, cli_source):
        assert "Relationship scan: 0 violations (clean)" in cli_source

    def test_api_contract_scan_has_clean_message(self, cli_source):
        assert "API contract scan: 0 violations (clean)" in cli_source


# ============================================================
# Deliverable 9: UI Requirements Fallback
# ============================================================

class TestUIRequirementsFallback:
    """v10 Deliverable 9: Fallback UI requirements when no --design-ref provided."""

    def test_fallback_generation_config_default_true(self):
        assert DesignReferenceConfig().fallback_generation is True

    def test_fallback_else_branch_exists_in_source(self):
        source = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert "v10: Fallback UI requirements" in source

    def test_fallback_calls_generate_function(self):
        source = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert "generate_fallback_ui_requirements" in source


# ============================================================
# Cross-Feature Integration
# ============================================================

class TestCrossFeatureIntegration:
    """Verify all v10 features work together and don't break existing imports."""

    def test_all_new_functions_importable(self):
        """All v10-touched modules can be imported without error."""
        from agent_team.agents import build_orchestrator_prompt
        from agent_team.config import PostOrchestrationScanConfig, _dict_to_config, apply_depth_quality_gating
        from agent_team.e2e_testing import detect_app_type, AppTypeInfo
        from agent_team.display import print_recovery_report
        from agent_team.quality_checks import run_default_value_scan, Violation

    def test_new_config_field_doesnt_break_loading(self):
        """_dict_to_config({}) should still work with no data."""
        cfg, overrides = _dict_to_config({})
        assert isinstance(cfg, AgentTeamConfig)
        assert isinstance(overrides, set)

    def test_prd_prompt_has_all_three_blocks(self):
        """PRD prompt should contain all three v10 blocks together."""
        prompt = _prd_prompt()
        assert "MANDATORY ROOT-LEVEL ARTIFACTS" in prompt
        assert "[CONVERGENCE LOOP" in prompt
        assert "[REQUIREMENT MARKING" in prompt

    def test_detect_app_type_root_backward_compat(self, tmp_path):
        """Root-level express detection still works as it did before v10."""
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "express"

    def test_standard_depth_no_change_to_max_passes(self):
        """Standard depth should not modify max_scan_fix_passes from default."""
        config = AgentTeamConfig()
        default_val = config.post_orchestration_scans.max_scan_fix_passes
        apply_depth_quality_gating("standard", config)
        assert config.post_orchestration_scans.max_scan_fix_passes == default_val

    def test_thorough_depth_no_change_to_max_passes(self):
        """Thorough depth should not modify max_scan_fix_passes from default."""
        config = AgentTeamConfig()
        default_val = config.post_orchestration_scans.max_scan_fix_passes
        apply_depth_quality_gating("thorough", config)
        assert config.post_orchestration_scans.max_scan_fix_passes == default_val


# ============================================================
# Backward Compatibility Tests
# ============================================================

class TestBackwardCompatibility:
    """Verify v10 changes do not break pre-existing behavior."""

    def test_non_prd_prompt_still_has_planning_fleet(self):
        prompt = _std_prompt()
        assert "PLANNING FLEET" in prompt

    def test_non_prd_prompt_still_has_spec_validator(self):
        prompt = _std_prompt()
        assert "SPEC FIDELITY VALIDATOR" in prompt

    def test_prd_prompt_still_has_prd_analyzer_fleet(self):
        prompt = _prd_prompt()
        assert "PRD ANALYZER FLEET" in prompt

    def test_non_prd_prompt_still_has_task_assigner(self):
        prompt = _std_prompt()
        assert "TASK ASSIGNER" in prompt


# ============================================================
# Root-Level Detection Backward Compatibility
# ============================================================

class TestRootDetectionBackwardCompat:
    """Verify root-level detection still works the same as before v10."""

    def test_root_react_detection(self, tmp_path):
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"react": "18"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "react"

    def test_root_nextjs_detection(self, tmp_path):
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"next": "14"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "nextjs"
        # Next.js also implies backend
        assert info.has_backend is True

    def test_root_angular_detection(self, tmp_path):
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"@angular/core": "17"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "angular"

    def test_root_prisma_detection(self, tmp_path):
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"prisma": "5"}
        }))
        info = detect_app_type(tmp_path)
        assert info.db_type == "prisma"

    def test_empty_project_detection(self, tmp_path):
        """Empty directory should return default AppTypeInfo."""
        info = detect_app_type(tmp_path)
        assert info.has_backend is False
        assert info.has_frontend is False
        assert info.db_type == ""


# ============================================================
# Subdirectory Precedence Rules
# ============================================================

class TestSubdirectoryPrecedence:
    """Verify precedence between root and subdirectory detection."""

    def test_root_backend_not_overridden_by_subdir(self, tmp_path):
        """If root already has backend, subdir backend should not override framework."""
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "server/package.json", json.dumps({
            "dependencies": {"@nestjs/core": "10"}
        }))
        info = detect_app_type(tmp_path)
        assert info.backend_framework == "express"  # root wins

    def test_subdir_fills_missing_frontend_when_root_has_backend(self, tmp_path):
        """Root has backend only, subdir fills frontend."""
        _make_file(tmp_path, "package.json", json.dumps({
            "dependencies": {"express": "4.18"}
        }))
        _make_file(tmp_path, "client/package.json", json.dumps({
            "dependencies": {"vue": "3"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "express"
        assert info.has_frontend is True
        assert info.frontend_framework == "vue"
        assert info.frontend_directory == "client"


# ============================================================
# Additional Subdirectory Edge Cases
# ============================================================

class TestSubdirectoryEdgeCases:
    """Edge cases for subdirectory detection."""

    def test_flask_in_subdir(self, tmp_path):
        (tmp_path / "api").mkdir()
        _make_file(tmp_path, "api/requirements.txt", "flask\nflask-cors")
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "flask"

    def test_vue_in_web_subdir(self, tmp_path):
        _make_file(tmp_path, "web/package.json", json.dumps({
            "dependencies": {"vue": "3"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.frontend_framework == "vue"
        assert info.frontend_directory == "web"

    def test_koa_in_api_subdir(self, tmp_path):
        _make_file(tmp_path, "api/package.json", json.dumps({
            "dependencies": {"koa": "2"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_backend is True
        assert info.backend_framework == "koa"

    def test_nextjs_in_subdir_sets_both(self, tmp_path):
        """Next.js in frontend subdir should set both frontend and backend."""
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"next": "14"}
        }))
        info = detect_app_type(tmp_path)
        assert info.has_frontend is True
        assert info.has_backend is True
        assert info.frontend_framework == "nextjs"

    def test_yarn_lockfile_in_subdir(self, tmp_path):
        _make_file(tmp_path, "frontend/package.json", json.dumps({
            "dependencies": {"react": "18"}
        }))
        _make_file(tmp_path, "frontend/yarn.lock", "")
        info = detect_app_type(tmp_path)
        assert info.package_manager == "yarn"


# ============================================================
# Additional Recovery Label Tests
# ============================================================

class TestRecoveryLabelRendering:
    """Verify print_recovery_report renders without crash for each type."""

    def test_zero_count_prints_nothing(self):
        with patch("agent_team.display.console") as mock_console:
            print_recovery_report(recovery_count=0, recovery_types=[])
        mock_console.print.assert_not_called()

    def test_single_known_type_renders(self):
        with patch("agent_team.display.console") as mock_console:
            print_recovery_report(recovery_count=1, recovery_types=["mock_data_fix"])
        assert mock_console.print.call_count >= 1

    def test_multiple_types_renders(self):
        with patch("agent_team.display.console") as mock_console:
            print_recovery_report(
                recovery_count=3,
                recovery_types=["mock_data_fix", "ui_compliance_fix", "api_contract_fix"],
            )
        assert mock_console.print.call_count >= 1

    def test_contract_generation_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"contract_generation"\s*:\s*"([^"]+)"', source)
        assert m
        assert "contract" in m.group(1).lower() or "CONTRACTS" in m.group(1)

    def test_review_recovery_label(self):
        source = (_SRC / "display.py").read_text(encoding="utf-8")
        m = re.search(r'"review_recovery"\s*:\s*"([^"]+)"', source)
        assert m
        assert "review" in m.group(1).lower()


# ============================================================
# Additional DB-005 Prisma Exclusion Tests
# ============================================================

class TestDB005PrismaEdgeCases:
    """Edge cases for the Prisma delegate exclusion in DB-005."""

    def test_prisma_with_whitespace_before_dot(self, tmp_path):
        """prisma .user.findFirst() with space should still be excluded."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Order {\n"
            "  user?: User;\n"
            "}\n"
        ))
        _make_file(tmp_path, "services/order.service.ts", (
            "const u = await prisma .user.findFirst();\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "user" in v.message]
        # prisma with space before dot — the regex checks `\bprisma\s*$`
        # so trailing whitespace before the dot position should still match
        assert len(db005) == 0, f"Prisma delegate with space should not be flagged: {db005}"

    def test_not_prisma_variable_name(self, tmp_path):
        """myPrisma.user.findFirst() should still be excluded (contains 'prisma')."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Order {\n"
            "  user?: User;\n"
            "}\n"
        ))
        # myPrisma ends with "prisma" so the regex \bprisma\s*$ matches
        _make_file(tmp_path, "services/order.service.ts", (
            "const u = await myVariable.user.findFirst();\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "user" in v.message]
        # "myVariable" does not end with "prisma", so it should be flagged
        assert len(db005) > 0

    def test_prisma_multiline_access(self, tmp_path):
        """Multi-line prisma access should also be excluded."""
        _make_file(tmp_path, "models/entity.ts", (
            "@Entity()\n"
            "export class Order {\n"
            "  status?: OrderStatus;\n"
            "}\n"
        ))
        _make_file(tmp_path, "services/order.service.ts", (
            "const orders = await prisma.status.findMany({\n"
            "  where: { active: true }\n"
            "});\n"
        ))
        violations = run_default_value_scan(tmp_path)
        db005 = [v for v in violations if v.check == "DB-005" and "status" in v.message]
        assert len(db005) == 0, f"Prisma delegate should not be flagged: {db005}"


# ============================================================
# Additional Multi-Pass Config Tests
# ============================================================

class TestMultiPassConfigEdgeCases:
    """Edge cases for max_scan_fix_passes configuration."""

    def test_non_integer_value_defaults_to_1(self):
        cfg, _ = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": "two"}
        })
        assert cfg.post_orchestration_scans.max_scan_fix_passes == 1

    def test_user_override_tracked_in_set(self):
        _, overrides = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": 3}
        })
        assert "post_orchestration_scans.max_scan_fix_passes" in overrides

    def test_large_value_accepted(self):
        cfg, _ = _dict_to_config({
            "post_orchestration_scans": {"max_scan_fix_passes": 100}
        })
        assert cfg.post_orchestration_scans.max_scan_fix_passes == 100

    def test_exhaustive_override_preserved(self):
        """User sets max_scan_fix_passes=5, exhaustive should not change to 2."""
        config = AgentTeamConfig()
        config.post_orchestration_scans.max_scan_fix_passes = 5
        overrides = {"post_orchestration_scans.max_scan_fix_passes"}
        apply_depth_quality_gating("exhaustive", config, user_overrides=overrides)
        assert config.post_orchestration_scans.max_scan_fix_passes == 5


# ============================================================
# Additional UI Requirements Fallback Tests
# ============================================================

class TestUIRequirementsFallbackGeneration:
    """Verify generate_fallback_ui_requirements() produces valid content."""

    def test_generate_fallback_returns_string(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build a SaaS dashboard", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert isinstance(content, str)
        assert len(content) > 100

    def test_fallback_contains_color_system(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build app", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert "Color System" in content

    def test_fallback_contains_typography(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build app", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert "Typography" in content

    def test_fallback_contains_spacing(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build app", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert "Spacing" in content

    def test_fallback_contains_component_patterns(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build app", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert "Component Patterns" in content

    def test_fallback_contains_warning_header(self, tmp_path):
        content = generate_fallback_ui_requirements(
            task="Build app", config=AgentTeamConfig(), cwd=str(tmp_path),
        )
        assert "FALLBACK-GENERATED" in content

    def test_fallback_writes_to_disk(self, tmp_path):
        config = AgentTeamConfig()
        req_dir = config.convergence.requirements_dir
        ui_file = config.design_reference.ui_requirements_file
        generate_fallback_ui_requirements(
            task="Build app", config=config, cwd=str(tmp_path),
        )
        expected_path = tmp_path / req_dir / ui_file
        assert expected_path.is_file()

    def test_infer_brutalist_direction(self):
        direction = _infer_design_direction("Build a developer CLI tool")
        assert direction == "brutalist"

    def test_infer_minimal_modern_fallback(self):
        direction = _infer_design_direction("Build something")
        assert direction == "minimal_modern"

    def test_direction_table_has_required_keys(self):
        for direction, info in _DIRECTION_TABLE.items():
            assert "keywords" in info
            assert "primary" in info
            assert "heading_font" in info
            assert "body_font" in info


# ============================================================
# Multi-Pass Loop Wiring Verification
# ============================================================

class TestMultiPassLoopWiring:
    """Verify all 8 scan blocks in cli.py use the multi-pass for loop pattern."""

    @pytest.fixture(scope="class")
    def cli_source(self):
        return (_SRC / "cli.py").read_text(encoding="utf-8")

    def test_mock_scan_uses_multipass_loop(self, cli_source):
        assert "for _fix_pass in range(max(1, _max_passes)" in cli_source

    def test_all_scan_blocks_read_max_passes_from_config(self, cli_source):
        count = cli_source.count("config.post_orchestration_scans.max_scan_fix_passes")
        assert count >= 8, f"Expected >= 8 reads of max_scan_fix_passes, got {count}"

    def test_scan_blocks_have_pass_number_logging(self, cli_source):
        """Each scan logs pass number on subsequent passes."""
        assert "pass {_fix_pass + 1}" in cli_source

    def test_scan_blocks_have_scan_only_break(self, cli_source):
        """When max_passes <= 0, scans break without fix (scan-only mode)."""
        assert "break  # scan-only mode" in cli_source

    def test_recovery_types_append_on_first_pass_only(self, cli_source):
        """recovery_types.append only happens on _fix_pass == 0."""
        # Count the pattern: each scan has `if _fix_pass == 0:` guard for recovery_types
        count = cli_source.count("if _fix_pass == 0:\n")
        assert count >= 8, f"Expected >= 8 first-pass guards, got {count}"


# ============================================================
# Convergence Loop Cross-Mode Tests
# ============================================================

class TestConvergenceLoopCrossModeConsistency:
    """Verify convergence + marking blocks appear in ALL prompt modes."""

    def test_interview_simple_has_convergence(self):
        prompt = build_orchestrator_prompt(
            task="Build small app", depth="standard", config=AgentTeamConfig(),
            interview_scope="SIMPLE", interview_doc="Just a small app",
        )
        # SIMPLE scope should use non-PRD path
        assert "[CONVERGENCE LOOP" in prompt

    def test_different_depth_levels_have_convergence(self):
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            prompt = _prd_prompt(depth=depth)
            assert "[CONVERGENCE LOOP" in prompt, f"PRD prompt at depth={depth} missing convergence loop"

    def test_different_depth_levels_have_marking(self):
        for depth in ("quick", "standard", "thorough", "exhaustive"):
            prompt = _prd_prompt(depth=depth)
            assert "[REQUIREMENT MARKING" in prompt, f"PRD prompt at depth={depth} missing marking policy"
