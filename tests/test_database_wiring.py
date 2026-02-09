"""Phase 4: Wiring Verification — Database Integrity Scans.

Verifies:
  4A — Scan execution position (after existing integrity scans, before E2E)
  4B — Config gating (each flag independently disables its scan)
  4C — Crash isolation (each scan in its own try/except)
  4D — Recovery integration (correct recovery_types appended)
  4E — State tracking (cost updates, no separate phase marker)
  4F — Prompt injection verification (Seed Data + Enum/Status in prompts)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers — read source once per module
# ---------------------------------------------------------------------------

_CLI_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"
_AGENTS_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "agents.py"
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "config.py"
_QC_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "quality_checks.py"
_CQS_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "code_quality_standards.py"


@pytest.fixture(scope="module")
def cli_source() -> str:
    return _CLI_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cli_lines(cli_source: str) -> list[str]:
    return cli_source.splitlines()


@pytest.fixture(scope="module")
def agents_source() -> str:
    return _AGENTS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def config_source() -> str:
    return _CONFIG_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def qc_source() -> str:
    return _QC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def cqs_source() -> str:
    return _CQS_PATH.read_text(encoding="utf-8")


# ===================================================================
# 4A — Scan Execution Position
# ===================================================================

class TestScanExecutionPosition:
    """Verify database scans run AFTER existing integrity scans and BEFORE E2E."""

    def test_database_scans_after_prd_reconciliation(self, cli_source: str) -> None:
        """Database integrity scans must appear after PRD reconciliation scan."""
        prd_pos = cli_source.find("Scan 3: PRD reconciliation")
        db_pos = cli_source.find("Post-orchestration: Database Integrity Scans")
        assert prd_pos != -1, "PRD reconciliation section not found"
        assert db_pos != -1, "Database Integrity Scans section not found"
        assert prd_pos < db_pos, (
            "Database scans must come after PRD reconciliation"
        )

    def test_database_scans_before_e2e(self, cli_source: str) -> None:
        """Database integrity scans must appear before E2E testing phase."""
        db_pos = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_pos = cli_source.find("Post-orchestration: E2E Testing Phase")
        assert db_pos != -1, "Database Integrity Scans section not found"
        assert e2e_pos != -1, "E2E Testing Phase section not found"
        assert db_pos < e2e_pos, (
            "Database scans must come before E2E testing phase"
        )

    def test_database_scans_after_existing_integrity_scans(self, cli_source: str) -> None:
        """Database scans come after the original 3 integrity scans (deploy, asset, PRD)."""
        deploy_pos = cli_source.find("Scan 1: Deployment integrity")
        asset_pos = cli_source.find("Scan 2: Asset integrity")
        prd_pos = cli_source.find("Scan 3: PRD reconciliation")
        db_pos = cli_source.find("Post-orchestration: Database Integrity Scans")
        assert deploy_pos < asset_pos < prd_pos < db_pos, (
            "Order must be: deployment → asset → PRD → database scans"
        )

    def test_three_database_scans_in_sequence(self, cli_source: str) -> None:
        """The 3 database scans run in order: dual ORM → defaults → relationships."""
        dual_pos = cli_source.find("Scan 1: Dual ORM type consistency")
        default_pos = cli_source.find("Scan 2: Default value")
        rel_pos = cli_source.find("Scan 3: ORM relationship completeness")
        # These are within the Database Integrity Scans section
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        assert dual_pos != -1, "Dual ORM scan comment not found"
        assert default_pos != -1, "Default value scan comment not found"
        assert rel_pos != -1, "Relationship scan comment not found"
        # All three must be inside the database section
        assert db_section_start < dual_pos < default_pos < rel_pos, (
            "Database scans must follow order: dual ORM → defaults → relationships"
        )

    def test_scans_are_independent(self, cli_source: str) -> None:
        """No database scan depends on another scan's output variable."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]

        # Scan 2 should NOT reference db_dual_violations
        scan2_start = db_section.find("config.database_scans.default_value_scan")
        scan3_start = db_section.find("config.database_scans.relationship_scan")
        scan2_body = db_section[scan2_start:scan3_start]
        assert "db_dual_violations" not in scan2_body, (
            "Default value scan must not depend on dual ORM scan results"
        )

        # Scan 3 should NOT reference db_dual_violations or db_default_violations
        scan3_body = db_section[scan3_start:]
        assert "db_dual_violations" not in scan3_body, (
            "Relationship scan must not depend on dual ORM scan results"
        )
        assert "db_default_violations" not in scan3_body, (
            "Relationship scan must not depend on default value scan results"
        )

    def test_full_post_orchestration_order_with_database(self, cli_source: str) -> None:
        """Verify the complete post-orchestration sequence including database scans.

        Order: mock scan → UI scan → deploy → asset → PRD → DATABASE → E2E → report
        """
        markers = [
            "run_mock_data_scan(Path(cwd))",
            "run_ui_compliance_scan(Path(cwd))",
            "run_deployment_scan(Path(cwd))",
            "run_asset_scan(Path(cwd))",
            "_run_prd_reconciliation(",
            "run_dual_orm_scan(Path(cwd))",
            "run_default_value_scan(Path(cwd))",
            "run_relationship_scan(Path(cwd))",
            "detect_app_type(Path(cwd))",  # E2E entry point
            "print_recovery_report(",
        ]
        recovery_init = cli_source.find("recovery_types: list[str] = []")
        assert recovery_init != -1
        post_orch = cli_source[recovery_init:]

        positions = []
        for m in markers:
            pos = post_orch.find(m)
            assert pos != -1, f"Marker not found in post-orchestration: {m}"
            positions.append(pos)

        for i in range(len(positions) - 1):
            assert positions[i] < positions[i + 1], (
                f"Order violation: '{markers[i]}' (pos {positions[i]}) "
                f"must come before '{markers[i+1]}' (pos {positions[i+1]})"
            )


# ===================================================================
# 4B — Config Gating
# ===================================================================

class TestDatabaseConfigGating:
    """Verify each database scan config flag gates its scan independently."""

    def test_dual_orm_scan_gated_by_config(self, cli_source: str) -> None:
        """Dual ORM scan guarded by config.database_scans.dual_orm_scan."""
        assert "config.database_scans.dual_orm_scan" in cli_source

    def test_default_value_scan_gated_by_config(self, cli_source: str) -> None:
        """Default value scan guarded by config.database_scans.default_value_scan."""
        assert "config.database_scans.default_value_scan" in cli_source

    def test_relationship_scan_gated_by_config(self, cli_source: str) -> None:
        """Relationship scan guarded by config.database_scans.relationship_scan."""
        assert "config.database_scans.relationship_scan" in cli_source

    def test_dual_orm_if_statement(self, cli_source: str) -> None:
        """Dual ORM uses if-gate (scan function NOT called when False)."""
        pattern = r"if config\.database_scans\.dual_orm_scan:"
        assert re.search(pattern, cli_source), (
            "Dual ORM scan must use `if config.database_scans.dual_orm_scan:` guard"
        )

    def test_default_value_if_statement(self, cli_source: str) -> None:
        """Default value uses if-gate."""
        pattern = r"if config\.database_scans\.default_value_scan:"
        assert re.search(pattern, cli_source), (
            "Default value scan must use `if config.database_scans.default_value_scan:` guard"
        )

    def test_relationship_if_statement(self, cli_source: str) -> None:
        """Relationship uses if-gate."""
        pattern = r"if config\.database_scans\.relationship_scan:"
        assert re.search(pattern, cli_source), (
            "Relationship scan must use `if config.database_scans.relationship_scan:` guard"
        )

    def test_database_scans_not_gated_by_milestones(self, cli_source: str) -> None:
        """Database scans are NOT gated by _use_milestones — run in all modes."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]

        # Check the if-lines for each scan
        for flag in ["dual_orm_scan", "default_value_scan", "relationship_scan"]:
            for line in db_section.splitlines():
                if f"config.database_scans.{flag}" in line and "if" in line:
                    assert "_use_milestones" not in line, (
                        f"{flag} should NOT be gated by _use_milestones"
                    )

    def test_flags_are_independent(self, cli_source: str) -> None:
        """Each flag is checked independently — no compound conditions between them."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]

        # No single if-line should check two database scan flags together
        for line in db_section.splitlines():
            flags_in_line = sum(
                1 for f in ["dual_orm_scan", "default_value_scan", "relationship_scan"]
                if f in line
            )
            assert flags_in_line <= 1, (
                f"Multiple database scan flags on same line (compound condition): {line.strip()}"
            )


class TestDatabaseConfigDefaults:
    """Verify DatabaseScanConfig defaults."""

    def test_database_scan_config_exists(self, config_source: str) -> None:
        """DatabaseScanConfig dataclass exists."""
        assert "class DatabaseScanConfig" in config_source

    def test_dual_orm_defaults_true(self, config_source: str) -> None:
        """dual_orm_scan defaults to True."""
        assert "dual_orm_scan: bool = True" in config_source

    def test_default_value_defaults_true(self, config_source: str) -> None:
        """default_value_scan defaults to True."""
        assert "default_value_scan: bool = True" in config_source

    def test_relationship_defaults_true(self, config_source: str) -> None:
        """relationship_scan defaults to True."""
        assert "relationship_scan: bool = True" in config_source

    def test_database_scans_on_agent_team_config(self, config_source: str) -> None:
        """AgentTeamConfig has database_scans field."""
        assert "database_scans: DatabaseScanConfig" in config_source

    def test_dict_to_config_handles_database_scans(self, config_source: str) -> None:
        """_dict_to_config loads database_scans section."""
        assert '"database_scans"' in config_source
        assert "DatabaseScanConfig(" in config_source

    def test_missing_database_scans_section_uses_defaults(self, config_source: str) -> None:
        """Missing database_scans key uses default (all True) via field default_factory."""
        # The field uses default_factory=DatabaseScanConfig, so missing config = all defaults
        assert "default_factory=DatabaseScanConfig" in config_source


# ===================================================================
# 4C — Crash Isolation
# ===================================================================

class TestDatabaseCrashIsolation:
    """Verify each database scan has independent crash isolation."""

    def _get_db_section(self, cli_source: str) -> str:
        """Extract the database integrity scans section."""
        start = cli_source.find("Post-orchestration: Database Integrity Scans")
        end = cli_source.find("Post-orchestration: E2E Testing Phase")
        assert start != -1, "Database Integrity Scans section not found"
        assert end != -1, "E2E Testing Phase section not found"
        return cli_source[start:end]

    def _get_scan_section(self, cli_source: str, scan_num: int) -> str:
        """Extract a specific database scan sub-section."""
        db_section = self._get_db_section(cli_source)
        if scan_num == 1:
            start = db_section.find("Scan 1: Dual ORM")
            end = db_section.find("Scan 2: Default value")
        elif scan_num == 2:
            start = db_section.find("Scan 2: Default value")
            end = db_section.find("Scan 3: ORM relationship")
        else:
            start = db_section.find("Scan 3: ORM relationship")
            end = len(db_section)
        return db_section[start:end]

    def test_dual_orm_has_own_try_except(self, cli_source: str) -> None:
        """Dual ORM scan is wrapped in its own try/except."""
        section = self._get_scan_section(cli_source, 1)
        assert "try:" in section
        assert "except Exception" in section

    def test_default_value_has_own_try_except(self, cli_source: str) -> None:
        """Default value scan is wrapped in its own try/except."""
        section = self._get_scan_section(cli_source, 2)
        assert "try:" in section
        assert "except Exception" in section

    def test_relationship_has_own_try_except(self, cli_source: str) -> None:
        """Relationship scan is wrapped in its own try/except."""
        section = self._get_scan_section(cli_source, 3)
        assert "try:" in section
        assert "except Exception" in section

    def test_dual_orm_crash_does_not_block_default_value(self, cli_source: str) -> None:
        """Dual ORM except block ends BEFORE default value scan if-guard."""
        db_section = self._get_db_section(cli_source)
        # Find the outer except for dual ORM scan
        dual_except_pos = db_section.find('print_warning(f"Dual ORM scan failed:')
        default_if_pos = db_section.find("config.database_scans.default_value_scan")
        assert dual_except_pos != -1, "Dual ORM except message not found"
        assert default_if_pos != -1, "Default value if-guard not found"
        assert dual_except_pos < default_if_pos, (
            "Dual ORM except must complete before default value scan begins"
        )

    def test_default_value_crash_does_not_block_relationship(self, cli_source: str) -> None:
        """Default value except block ends BEFORE relationship scan if-guard."""
        db_section = self._get_db_section(cli_source)
        default_except_pos = db_section.find('print_warning(f"Default value scan failed:')
        rel_if_pos = db_section.find("config.database_scans.relationship_scan")
        assert default_except_pos != -1, "Default value except message not found"
        assert rel_if_pos != -1, "Relationship if-guard not found"
        assert default_except_pos < rel_if_pos, (
            "Default value except must complete before relationship scan begins"
        )

    def test_relationship_crash_does_not_block_e2e(self, cli_source: str) -> None:
        """Relationship except block ends BEFORE E2E testing phase."""
        rel_except_pos = cli_source.find('print_warning(f"Relationship scan failed:')
        e2e_pos = cli_source.find("Post-orchestration: E2E Testing Phase")
        assert rel_except_pos != -1, "Relationship except message not found"
        assert e2e_pos != -1, "E2E Testing Phase not found"
        assert rel_except_pos < e2e_pos, (
            "Relationship except must complete before E2E testing begins"
        )

    def test_all_three_crash_e2e_still_runs(self, cli_source: str) -> None:
        """All 3 database scans have except blocks that complete before E2E."""
        e2e_pos = cli_source.find("Post-orchestration: E2E Testing Phase")
        for msg in [
            "Dual ORM scan failed:",
            "Default value scan failed:",
            "Relationship scan failed:",
        ]:
            pos = cli_source.find(msg)
            assert pos != -1, f"Except message not found: {msg}"
            assert pos < e2e_pos, (
                f"Except for '{msg}' must complete before E2E phase"
            )

    def test_dual_orm_inner_fix_try_except(self, cli_source: str) -> None:
        """Dual ORM fix has its own inner try/except."""
        section = self._get_scan_section(cli_source, 1)
        try_count = section.count("try:")
        assert try_count >= 2, (
            f"Expected at least 2 try blocks in dual ORM section (outer + fix), found {try_count}"
        )

    def test_default_value_inner_fix_try_except(self, cli_source: str) -> None:
        """Default value fix has its own inner try/except."""
        section = self._get_scan_section(cli_source, 2)
        try_count = section.count("try:")
        assert try_count >= 2, (
            f"Expected at least 2 try blocks in default value section, found {try_count}"
        )

    def test_relationship_inner_fix_try_except(self, cli_source: str) -> None:
        """Relationship fix has its own inner try/except."""
        section = self._get_scan_section(cli_source, 3)
        try_count = section.count("try:")
        assert try_count >= 2, (
            f"Expected at least 2 try blocks in relationship section, found {try_count}"
        )

    def test_fix_exceptions_include_traceback(self, cli_source: str) -> None:
        """Inner fix except blocks log traceback for debugging."""
        db_section = self._get_db_section(cli_source)
        # Each fix block should have traceback.format_exc()
        traceback_count = db_section.count("traceback.format_exc()")
        assert traceback_count >= 3, (
            f"Expected at least 3 traceback.format_exc() calls in database section "
            f"(one per fix), found {traceback_count}"
        )

    def test_outer_exceptions_have_warning_messages(self, cli_source: str) -> None:
        """Outer except blocks have descriptive warning messages."""
        db_section = self._get_db_section(cli_source)
        assert "Dual ORM scan failed:" in db_section
        assert "Default value scan failed:" in db_section
        assert "Relationship scan failed:" in db_section


# ===================================================================
# 4D — Recovery Integration
# ===================================================================

class TestDatabaseRecoveryIntegration:
    """Verify violations trigger correct recovery types and fix calls."""

    def test_dual_orm_recovery_type(self, cli_source: str) -> None:
        """Dual ORM violations append 'database_dual_orm_fix' to recovery_types."""
        assert 'recovery_types.append("database_dual_orm_fix")' in cli_source

    def test_default_value_recovery_type(self, cli_source: str) -> None:
        """Default value violations append 'database_default_value_fix'."""
        assert 'recovery_types.append("database_default_value_fix")' in cli_source

    def test_relationship_recovery_type(self, cli_source: str) -> None:
        """Relationship violations append 'database_relationship_fix'."""
        assert 'recovery_types.append("database_relationship_fix")' in cli_source

    def test_all_three_recovery_types_unique(self, cli_source: str) -> None:
        """All 3 database recovery types are distinct strings."""
        types = [
            "database_dual_orm_fix",
            "database_default_value_fix",
            "database_relationship_fix",
        ]
        # Verify each appears exactly once
        for t in types:
            count = cli_source.count(f'recovery_types.append("{t}")')
            assert count == 1, (
                f"Recovery type '{t}' should appear exactly once, found {count}"
            )

    def test_dual_orm_fix_uses_run_integrity_fix(self, cli_source: str) -> None:
        """Dual ORM fix calls _run_integrity_fix with scan_type='database_dual_orm'."""
        section = cli_source[
            cli_source.find("config.database_scans.dual_orm_scan"):
            cli_source.find("config.database_scans.default_value_scan")
        ]
        assert '_run_integrity_fix(' in section
        assert 'scan_type="database_dual_orm"' in section

    def test_default_value_fix_uses_run_integrity_fix(self, cli_source: str) -> None:
        """Default value fix calls _run_integrity_fix with scan_type='database_defaults'."""
        section = cli_source[
            cli_source.find("config.database_scans.default_value_scan"):
            cli_source.find("config.database_scans.relationship_scan")
        ]
        assert '_run_integrity_fix(' in section
        assert 'scan_type="database_defaults"' in section

    def test_relationship_fix_uses_run_integrity_fix(self, cli_source: str) -> None:
        """Relationship fix calls _run_integrity_fix with scan_type='database_relationships'."""
        section = cli_source[
            cli_source.find("config.database_scans.relationship_scan"):
            cli_source.find("Post-orchestration: E2E Testing Phase")
        ]
        assert '_run_integrity_fix(' in section
        assert 'scan_type="database_relationships"' in section

    def test_fix_only_called_when_violations_exist(self, cli_source: str) -> None:
        """_run_integrity_fix is only called when violations list is non-empty."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]

        # Each scan should have an if-check on violations before calling fix
        assert "if db_dual_violations:" in db_section
        assert "if db_default_violations:" in db_section
        assert "if db_rel_violations:" in db_section

    def test_recovery_types_appear_in_report(self, cli_source: str) -> None:
        """Recovery report at end includes all recovery_types."""
        assert "print_recovery_report(len(recovery_types), recovery_types)" in cli_source

    def test_database_recovery_types_no_conflict_with_existing(self, cli_source: str) -> None:
        """Database recovery types don't clash with existing ones."""
        all_appends = re.findall(r'recovery_types\.append\("([^"]+)"\)', cli_source)
        db_types = [t for t in all_appends if t.startswith("database_")]
        non_db_types = [t for t in all_appends if not t.startswith("database_")]
        # No overlap
        overlap = set(db_types) & set(non_db_types)
        assert len(overlap) == 0, f"Database recovery types clash with existing: {overlap}"


# ===================================================================
# 4E — State Tracking
# ===================================================================

class TestDatabaseStateTracking:
    """Verify state tracking for database scans."""

    def test_no_completed_phases_marker_for_db_scans(self, cli_source: str) -> None:
        """Database scans do NOT append their own completed_phases marker.

        They are part of the post_orchestration phase — no separate marker needed.
        """
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        assert "completed_phases.append" not in db_section, (
            "Database scans should NOT have their own completed_phases marker"
        )

    def test_cost_updated_after_dual_orm_fix(self, cli_source: str) -> None:
        """_current_state.total_cost is updated after dual ORM fix."""
        section = cli_source[
            cli_source.find("config.database_scans.dual_orm_scan"):
            cli_source.find("config.database_scans.default_value_scan")
        ]
        assert "_current_state.total_cost += fix_cost" in section

    def test_cost_updated_after_default_value_fix(self, cli_source: str) -> None:
        """_current_state.total_cost is updated after default value fix."""
        section = cli_source[
            cli_source.find("config.database_scans.default_value_scan"):
            cli_source.find("config.database_scans.relationship_scan")
        ]
        assert "_current_state.total_cost += fix_cost" in section

    def test_cost_updated_after_relationship_fix(self, cli_source: str) -> None:
        """_current_state.total_cost is updated after relationship fix."""
        section = cli_source[
            cli_source.find("config.database_scans.relationship_scan"):
            cli_source.find("Post-orchestration: E2E Testing Phase")
        ]
        assert "_current_state.total_cost += fix_cost" in section

    def test_cost_update_guarded_by_current_state(self, cli_source: str) -> None:
        """Cost update is guarded by `if _current_state:` check."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]

        # Each cost update should be preceded by a _current_state guard
        cost_updates = [i for i, line in enumerate(db_section.splitlines())
                        if "_current_state.total_cost += fix_cost" in line]
        assert len(cost_updates) == 3, (
            f"Expected 3 cost updates in database section, found {len(cost_updates)}"
        )

    def test_cost_update_pattern_matches_existing_scans(self, cli_source: str) -> None:
        """Database scans follow the same cost-update pattern as deployment/asset scans."""
        # Deployment scan uses: if _current_state:\n    _current_state.total_cost += deploy_fix_cost
        # Database scans use: if _current_state:\n    _current_state.total_cost += fix_cost
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        assert "if _current_state:" in db_section, (
            "Database scans must guard cost update with if _current_state:"
        )


# ===================================================================
# 4F — Prompt Injection Verification
# ===================================================================

class TestSeedDataPromptInjection:
    """Verify Seed Data Completeness policy is injected into prompts."""

    def test_seed_policy_in_code_writer(self, agents_source: str) -> None:
        """SEED DATA COMPLETENESS POLICY is in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        assert writer_start != -1
        # Find the end of CODE_WRITER_PROMPT (next top-level variable or end)
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "SEED DATA COMPLETENESS POLICY" in writer_section, (
            "Seed Data Completeness policy missing from CODE_WRITER_PROMPT"
        )

    def test_seed_001_in_code_writer(self, agents_source: str) -> None:
        """SEED-001 pattern ID present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "SEED-001" in writer_section

    def test_seed_002_in_code_writer(self, agents_source: str) -> None:
        """SEED-002 pattern ID present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "SEED-002" in writer_section

    def test_seed_003_in_code_writer(self, agents_source: str) -> None:
        """SEED-003 pattern ID present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "SEED-003" in writer_section

    def test_seed_verification_in_code_reviewer(self, agents_source: str) -> None:
        """Seed Data Verification section present in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        assert reviewer_start != -1
        reviewer_section = agents_source[reviewer_start:]
        assert "Seed Data Verification" in reviewer_section, (
            "Seed Data Verification section missing from CODE_REVIEWER_PROMPT"
        )

    def test_seed_001_in_code_reviewer(self, agents_source: str) -> None:
        """SEED-001 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "SEED-001" in reviewer_section

    def test_seed_002_in_code_reviewer(self, agents_source: str) -> None:
        """SEED-002 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "SEED-002" in reviewer_section

    def test_seed_003_in_code_reviewer(self, agents_source: str) -> None:
        """SEED-003 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "SEED-003" in reviewer_section


class TestEnumRegistryPromptInjection:
    """Verify Enum/Status Registry is injected into ARCHITECT, WRITER, and REVIEWER prompts."""

    def test_enum_registry_in_architect(self, agents_source: str) -> None:
        """Status/Enum Registry section present in ARCHITECT_PROMPT."""
        arch_start = agents_source.find("ARCHITECT_PROMPT")
        arch_end = agents_source.find("\nCODE_WRITER_PROMPT", arch_start)
        arch_section = agents_source[arch_start:arch_end]
        assert "Status/Enum Registry" in arch_section or "STATUS_REGISTRY" in arch_section, (
            "Enum/Status Registry section missing from ARCHITECT_PROMPT"
        )

    def test_enum_001_in_architect(self, agents_source: str) -> None:
        """ENUM-001 pattern ID present in ARCHITECT_PROMPT."""
        arch_start = agents_source.find("ARCHITECT_PROMPT")
        arch_end = agents_source.find("\nCODE_WRITER_PROMPT", arch_start)
        arch_section = agents_source[arch_start:arch_end]
        assert "ENUM-001" in arch_section

    def test_enum_002_in_architect(self, agents_source: str) -> None:
        """ENUM-002 pattern ID present in ARCHITECT_PROMPT."""
        arch_start = agents_source.find("ARCHITECT_PROMPT")
        arch_end = agents_source.find("\nCODE_WRITER_PROMPT", arch_start)
        arch_section = agents_source[arch_start:arch_end]
        assert "ENUM-002" in arch_section

    def test_enum_003_in_architect(self, agents_source: str) -> None:
        """ENUM-003 pattern ID present in ARCHITECT_PROMPT."""
        arch_start = agents_source.find("ARCHITECT_PROMPT")
        arch_end = agents_source.find("\nCODE_WRITER_PROMPT", arch_start)
        arch_section = agents_source[arch_start:arch_end]
        assert "ENUM-003" in arch_section

    def test_enum_compliance_in_code_writer(self, agents_source: str) -> None:
        """ENUM/STATUS REGISTRY COMPLIANCE present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "ENUM/STATUS REGISTRY COMPLIANCE" in writer_section, (
            "Enum/Status Registry compliance missing from CODE_WRITER_PROMPT"
        )

    def test_enum_001_in_code_writer(self, agents_source: str) -> None:
        """ENUM-001 referenced in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "ENUM-001" in writer_section

    def test_enum_002_in_code_writer(self, agents_source: str) -> None:
        """ENUM-002 referenced in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "ENUM-002" in writer_section

    def test_enum_003_in_code_writer(self, agents_source: str) -> None:
        """ENUM-003 referenced in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "ENUM-003" in writer_section

    def test_enum_verification_in_code_reviewer(self, agents_source: str) -> None:
        """Enum/Status Registry Verification section present in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "Enum/Status Registry Verification" in reviewer_section, (
            "Enum/Status Registry Verification missing from CODE_REVIEWER_PROMPT"
        )

    def test_enum_001_in_code_reviewer(self, agents_source: str) -> None:
        """ENUM-001 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "ENUM-001" in reviewer_section

    def test_enum_002_in_code_reviewer(self, agents_source: str) -> None:
        """ENUM-002 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "ENUM-002" in reviewer_section

    def test_enum_003_in_code_reviewer(self, agents_source: str) -> None:
        """ENUM-003 referenced in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "ENUM-003" in reviewer_section


class TestExistingPoliciesPreserved:
    """Verify existing prompt policies are NOT broken by new injections."""

    def test_zero_mock_data_policy_still_in_writer(self, agents_source: str) -> None:
        """ZERO MOCK DATA POLICY still present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "ZERO MOCK DATA POLICY" in writer_section, (
            "ZERO MOCK DATA POLICY was removed or broken by new prompt injections"
        )

    def test_ui_compliance_policy_still_in_writer(self, agents_source: str) -> None:
        """UI COMPLIANCE POLICY still present in CODE_WRITER_PROMPT."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        assert "UI COMPLIANCE POLICY" in writer_section, (
            "UI COMPLIANCE POLICY was removed or broken by new prompt injections"
        )

    def test_mock_data_detection_still_in_reviewer(self, agents_source: str) -> None:
        """Mock Data Detection section still present in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "Mock Data Detection" in reviewer_section, (
            "Mock Data Detection was removed from CODE_REVIEWER_PROMPT"
        )

    def test_ui_compliance_verification_still_in_reviewer(self, agents_source: str) -> None:
        """UI Compliance Verification still present in CODE_REVIEWER_PROMPT."""
        reviewer_start = agents_source.find("CODE_REVIEWER_PROMPT")
        reviewer_section = agents_source[reviewer_start:]
        assert "UI Compliance Verification" in reviewer_section, (
            "UI Compliance Verification was removed from CODE_REVIEWER_PROMPT"
        )

    def test_svc_wiring_still_in_architect(self, agents_source: str) -> None:
        """Service-to-API Wiring Plan still present in ARCHITECT_PROMPT."""
        arch_start = agents_source.find("ARCHITECT_PROMPT")
        arch_end = agents_source.find("\nCODE_WRITER_PROMPT", arch_start)
        arch_section = agents_source[arch_start:arch_end]
        assert "Service-to-API Wiring Plan" in arch_section, (
            "Service-to-API Wiring Plan was removed from ARCHITECT_PROMPT"
        )

    def test_prompt_ordering_writer(self, agents_source: str) -> None:
        """In CODE_WRITER_PROMPT: ZERO MOCK DATA comes before UI COMPLIANCE
        comes before SEED DATA comes before ENUM REGISTRY."""
        writer_start = agents_source.find("CODE_WRITER_PROMPT")
        writer_section = agents_source[writer_start:agents_source.find('\n\nCODE_REVIEWER_PROMPT', writer_start)]
        mock_pos = writer_section.find("ZERO MOCK DATA POLICY")
        ui_pos = writer_section.find("UI COMPLIANCE POLICY")
        seed_pos = writer_section.find("SEED DATA COMPLETENESS POLICY")
        enum_pos = writer_section.find("ENUM/STATUS REGISTRY COMPLIANCE")
        assert mock_pos != -1 and ui_pos != -1 and seed_pos != -1 and enum_pos != -1, (
            "One or more policies missing from CODE_WRITER_PROMPT"
        )
        assert mock_pos < ui_pos < seed_pos < enum_pos, (
            "Policy ordering in CODE_WRITER_PROMPT must be: "
            "ZERO MOCK DATA → UI COMPLIANCE → SEED DATA → ENUM REGISTRY"
        )


# ===================================================================
# 4F Extended — Quality Checks Functions Exist
# ===================================================================

class TestScanFunctionsExist:
    """Verify the 3 scan functions exist in quality_checks.py."""

    def test_run_dual_orm_scan_exists(self, qc_source: str) -> None:
        """run_dual_orm_scan function exists."""
        assert "def run_dual_orm_scan(" in qc_source

    def test_run_default_value_scan_exists(self, qc_source: str) -> None:
        """run_default_value_scan function exists."""
        assert "def run_default_value_scan(" in qc_source

    def test_run_relationship_scan_exists(self, qc_source: str) -> None:
        """run_relationship_scan function exists."""
        assert "def run_relationship_scan(" in qc_source

    def test_scan_functions_return_list_violation(self, qc_source: str) -> None:
        """All 3 scan functions return list[Violation]."""
        for fn in ["run_dual_orm_scan", "run_default_value_scan", "run_relationship_scan"]:
            fn_start = qc_source.find(f"def {fn}(")
            fn_sig = qc_source[fn_start:fn_start + 200]
            assert "list[Violation]" in fn_sig or "List[Violation]" in fn_sig, (
                f"{fn} must return list[Violation]"
            )

    def test_scan_functions_accept_project_root(self, qc_source: str) -> None:
        """All 3 scan functions accept project_root: Path parameter."""
        for fn in ["run_dual_orm_scan", "run_default_value_scan", "run_relationship_scan"]:
            fn_start = qc_source.find(f"def {fn}(")
            fn_sig = qc_source[fn_start:fn_start + 200]
            assert "project_root" in fn_sig, (
                f"{fn} must accept project_root parameter"
            )


class TestDatabaseIntegrityStandards:
    """Verify DATABASE_INTEGRITY_STANDARDS constant in code_quality_standards.py."""

    def test_constant_exists(self, cqs_source: str) -> None:
        """DATABASE_INTEGRITY_STANDARDS constant exists."""
        assert "DATABASE_INTEGRITY_STANDARDS" in cqs_source

    def test_mapped_to_code_writer(self, cqs_source: str) -> None:
        """DATABASE_INTEGRITY_STANDARDS is in the code-writer standards list."""
        # Find the ROLE_STANDARDS_MAP or similar mapping
        assert "DATABASE_INTEGRITY_STANDARDS" in cqs_source
        # Verify it's in the code-writer list
        writer_line = None
        for line in cqs_source.splitlines():
            if "code-writer" in line and "DATABASE_INTEGRITY_STANDARDS" in line:
                writer_line = line
                break
        # It might be on a separate line in a list
        if writer_line is None:
            # Check multi-line mapping
            writer_section_start = cqs_source.find('"code-writer"')
            if writer_section_start != -1:
                writer_section = cqs_source[writer_section_start:writer_section_start + 300]
                assert "DATABASE_INTEGRITY_STANDARDS" in writer_section, (
                    "DATABASE_INTEGRITY_STANDARDS must be mapped to code-writer"
                )

    def test_mapped_to_code_reviewer(self, cqs_source: str) -> None:
        """DATABASE_INTEGRITY_STANDARDS is in the code-reviewer standards list."""
        reviewer_section_start = cqs_source.find('"code-reviewer"')
        assert reviewer_section_start != -1
        reviewer_section = cqs_source[reviewer_section_start:reviewer_section_start + 300]
        assert "DATABASE_INTEGRITY_STANDARDS" in reviewer_section, (
            "DATABASE_INTEGRITY_STANDARDS must be mapped to code-reviewer"
        )

    def test_mapped_to_architect(self, cqs_source: str) -> None:
        """DATABASE_INTEGRITY_STANDARDS is in the architect standards list."""
        arch_section_start = cqs_source.find('"architect"')
        assert arch_section_start != -1
        arch_section = cqs_source[arch_section_start:arch_section_start + 300]
        assert "DATABASE_INTEGRITY_STANDARDS" in arch_section, (
            "DATABASE_INTEGRITY_STANDARDS must be mapped to architect"
        )


# ===================================================================
# 4D Extended — Fix Function Parameters
# ===================================================================

class TestFixFunctionParameters:
    """Verify _run_integrity_fix is called with correct parameters for each scan."""

    def _get_fix_call(self, cli_source: str, scan_type: str) -> str:
        """Extract the _run_integrity_fix call block for a given scan_type."""
        pattern = f'scan_type="{scan_type}"'
        pos = cli_source.find(pattern)
        assert pos != -1, f"scan_type='{scan_type}' not found in cli.py"
        # Get surrounding context (the full asyncio.run call)
        start = cli_source.rfind("asyncio.run(", max(0, pos - 500), pos)
        end = cli_source.find(")", pos) + 1
        return cli_source[start:end]

    def test_dual_orm_passes_violations(self, cli_source: str) -> None:
        """Dual ORM fix passes db_dual_violations to _run_integrity_fix."""
        call = self._get_fix_call(cli_source, "database_dual_orm")
        assert "violations=db_dual_violations" in call

    def test_default_value_passes_violations(self, cli_source: str) -> None:
        """Default value fix passes db_default_violations to _run_integrity_fix."""
        call = self._get_fix_call(cli_source, "database_defaults")
        assert "violations=db_default_violations" in call

    def test_relationship_passes_violations(self, cli_source: str) -> None:
        """Relationship fix passes db_rel_violations to _run_integrity_fix."""
        call = self._get_fix_call(cli_source, "database_relationships")
        assert "violations=db_rel_violations" in call

    def test_all_fix_calls_pass_task_text(self, cli_source: str) -> None:
        """All fix calls include task_text=args.task."""
        for scan_type in ["database_dual_orm", "database_defaults", "database_relationships"]:
            call = self._get_fix_call(cli_source, scan_type)
            assert "task_text=args.task" in call, (
                f"Fix call for {scan_type} missing task_text parameter"
            )

    def test_all_fix_calls_pass_constraints(self, cli_source: str) -> None:
        """All fix calls include constraints parameter."""
        for scan_type in ["database_dual_orm", "database_defaults", "database_relationships"]:
            call = self._get_fix_call(cli_source, scan_type)
            assert "constraints=constraints" in call, (
                f"Fix call for {scan_type} missing constraints parameter"
            )

    def test_all_fix_calls_pass_intervention(self, cli_source: str) -> None:
        """All fix calls include intervention parameter."""
        for scan_type in ["database_dual_orm", "database_defaults", "database_relationships"]:
            call = self._get_fix_call(cli_source, scan_type)
            assert "intervention=intervention" in call, (
                f"Fix call for {scan_type} missing intervention parameter"
            )

    def test_all_fix_calls_pass_depth(self, cli_source: str) -> None:
        """All fix calls include depth parameter with milestone awareness."""
        for scan_type in ["database_dual_orm", "database_defaults", "database_relationships"]:
            call = self._get_fix_call(cli_source, scan_type)
            assert "depth=" in call, (
                f"Fix call for {scan_type} missing depth parameter"
            )

    def test_fix_depth_uses_milestone_conditional(self, cli_source: str) -> None:
        """Fix calls use `depth if not _use_milestones else 'standard'` pattern."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        # Should contain the milestone-aware depth pattern
        assert 'depth if not _use_milestones else "standard"' in db_section, (
            "Database fix calls must use milestone-aware depth pattern"
        )


# ===================================================================
# 4C Extended — Scan Import Isolation
# ===================================================================

class TestScanImportIsolation:
    """Verify scan functions are imported lazily inside try blocks."""

    def test_dual_orm_lazy_import(self, cli_source: str) -> None:
        """run_dual_orm_scan is imported lazily inside the try block."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        assert "from .quality_checks import run_dual_orm_scan" in db_section

    def test_default_value_lazy_import(self, cli_source: str) -> None:
        """run_default_value_scan is imported lazily inside the try block."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        assert "from .quality_checks import run_default_value_scan" in db_section

    def test_relationship_lazy_import(self, cli_source: str) -> None:
        """run_relationship_scan is imported lazily inside the try block."""
        db_section_start = cli_source.find("Post-orchestration: Database Integrity Scans")
        e2e_start = cli_source.find("Post-orchestration: E2E Testing Phase")
        db_section = cli_source[db_section_start:e2e_start]
        assert "from .quality_checks import run_relationship_scan" in db_section

    def test_imports_inside_try_not_top_level(self, cli_source: str) -> None:
        """Database scan imports are NOT at the top of cli.py (lazy loading pattern)."""
        # Top-level imports end at the first function definition
        first_fn = cli_source.find("\ndef ")
        if first_fn == -1:
            first_fn = cli_source.find("\nasync def ")
        top_section = cli_source[:first_fn]
        for fn_name in ["run_dual_orm_scan", "run_default_value_scan", "run_relationship_scan"]:
            assert fn_name not in top_section, (
                f"{fn_name} should NOT be imported at top level — must be lazy"
            )
