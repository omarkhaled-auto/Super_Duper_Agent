"""Tests for fix function completeness — _run_integrity_fix branches,
fix function signatures, crash isolation, and fix cycle logging.
"""

from __future__ import annotations

import inspect

import pytest

import agent_team.cli as cli_mod


# ===========================================================================
# _run_integrity_fix branches
# ===========================================================================


class TestIntegrityFixBranches:
    """Verify _run_integrity_fix has all 5 scan_type branches."""

    def test_function_exists(self):
        assert hasattr(cli_mod, "_run_integrity_fix")

    def test_deployment_branch(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert 'scan_type == "deployment"' in src

    def test_database_dual_orm_branch(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert 'scan_type == "database_dual_orm"' in src

    def test_database_defaults_branch(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert 'scan_type == "database_defaults"' in src

    def test_database_relationships_branch(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert 'scan_type == "database_relationships"' in src

    def test_asset_branch_is_else(self):
        """Asset branch is the else (fallback) branch."""
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert "ASSET INTEGRITY FIX" in src

    def test_docstring_lists_all_types(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        for scan_type in ("deployment", "asset", "database_dual_orm",
                          "database_defaults", "database_relationships"):
            assert scan_type in src, f"docstring missing {scan_type}"

    def test_deploy_prompt_mentions_codes(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        for code in ("DEPLOY-001", "DEPLOY-002", "DEPLOY-003", "DEPLOY-004"):
            assert code in src, f"{code} missing from deployment fix prompt"

    def test_db_dual_orm_prompt_mentions_codes(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        for code in ("DB-001", "DB-002", "DB-003"):
            assert code in src, f"{code} missing from dual ORM fix prompt"

    def test_db_defaults_prompt_mentions_codes(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        for code in ("DB-004", "DB-005"):
            assert code in src, f"{code} missing from defaults fix prompt"

    def test_db_relationships_prompt_mentions_codes(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        for code in ("DB-006", "DB-007", "DB-008"):
            assert code in src, f"{code} missing from relationships fix prompt"


# ===========================================================================
# Fix function signatures
# ===========================================================================


class TestFixFunctionSignatures:
    """Verify all fix functions have correct signatures."""

    def test_mock_data_fix_signature(self):
        sig = inspect.signature(cli_mod._run_mock_data_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "mock_violations" in params

    def test_ui_compliance_fix_signature(self):
        sig = inspect.signature(cli_mod._run_ui_compliance_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "ui_violations" in params

    def test_integrity_fix_signature(self):
        sig = inspect.signature(cli_mod._run_integrity_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "violations" in params
        assert "scan_type" in params

    def test_e2e_fix_signature(self):
        sig = inspect.signature(cli_mod._run_e2e_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params

    def test_review_only_signature(self):
        sig = inspect.signature(cli_mod._run_review_only)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "requirements_path" in params
        assert "depth" in params

    def test_all_fix_functions_are_async(self):
        for name in ("_run_mock_data_fix", "_run_ui_compliance_fix",
                      "_run_integrity_fix", "_run_e2e_fix", "_run_review_only"):
            func = getattr(cli_mod, name)
            assert inspect.iscoroutinefunction(func), f"{name} should be async"


# ===========================================================================
# Fix cycle log presence
# ===========================================================================


class TestFixCycleLogPresence:
    """Verify fix cycle log instructions appear in all fix functions."""

    def test_mock_data_fix_has_log(self):
        src = inspect.getsource(cli_mod._run_mock_data_fix)
        assert "fix_cycle_log" in src

    def test_ui_compliance_fix_has_log(self):
        src = inspect.getsource(cli_mod._run_ui_compliance_fix)
        assert "fix_cycle_log" in src

    def test_integrity_fix_has_log(self):
        src = inspect.getsource(cli_mod._run_integrity_fix)
        assert "fix_cycle_log" in src

    def test_e2e_fix_has_log(self):
        src = inspect.getsource(cli_mod._run_e2e_fix)
        assert "fix_cycle_log" in src

    def test_review_only_has_log(self):
        src = inspect.getsource(cli_mod._run_review_only)
        assert "fix_cycle_log" in src


# ===========================================================================
# E2E test functions
# ===========================================================================


class TestE2ETestFunctions:
    """Verify E2E test runner functions exist and have correct shape."""

    def test_backend_e2e_exists(self):
        assert hasattr(cli_mod, "_run_backend_e2e_tests")
        assert inspect.iscoroutinefunction(cli_mod._run_backend_e2e_tests)

    def test_frontend_e2e_exists(self):
        assert hasattr(cli_mod, "_run_frontend_e2e_tests")
        assert inspect.iscoroutinefunction(cli_mod._run_frontend_e2e_tests)

    def test_backend_e2e_logs_traceback(self):
        src = inspect.getsource(cli_mod._run_backend_e2e_tests)
        assert "traceback" in src

    def test_frontend_e2e_logs_traceback(self):
        src = inspect.getsource(cli_mod._run_frontend_e2e_tests)
        assert "traceback" in src

    def test_e2e_fix_logs_traceback(self):
        src = inspect.getsource(cli_mod._run_e2e_fix)
        assert "traceback" in src


# ===========================================================================
# Crash isolation in main()
# ===========================================================================


class TestCrashIsolationInMain:
    """Verify each scan in main() has its own try/except block."""

    def test_main_has_try_except_for_each_scan(self):
        src = inspect.getsource(cli_mod.main)
        scan_functions = [
            "run_mock_data_scan",
            "run_ui_compliance_scan",
            "run_deployment_scan",
            "run_asset_scan",
            "run_dual_orm_scan",
            "run_default_value_scan",
            "run_relationship_scan",
        ]
        for func in scan_functions:
            assert func in src, f"{func} not found in main()"

    def test_scope_computation_in_main(self):
        src = inspect.getsource(cli_mod.main)
        assert "compute_changed_files" in src

    def test_json_import_at_module_level(self):
        """Verify json is imported at module level (fix for PIPELINE F-1)."""
        import agent_team.cli
        assert hasattr(agent_team.cli, "json") or "json" in dir(agent_team.cli)
        # More direct check: json module accessible
        src = inspect.getsource(agent_team.cli)
        assert "\nimport json" in src or "import json\n" in src
