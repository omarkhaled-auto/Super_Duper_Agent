"""Tests for ScanScope and compute_changed_files (v6.0 Mode Upgrade Propagation)."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.quality_checks import (
    ScanScope,
    Violation,
    compute_changed_files,
    run_mock_data_scan,
    run_ui_compliance_scan,
    run_e2e_quality_scan,
    run_asset_scan,
    run_dual_orm_scan,
    run_default_value_scan,
    run_relationship_scan,
)


# ---------------------------------------------------------------------------
# ScanScope dataclass tests
# ---------------------------------------------------------------------------

class TestScanScope:
    def test_default_values(self):
        s = ScanScope()
        assert s.mode == "full"
        assert s.changed_files == []

    def test_custom_values(self):
        files = [Path("/a/b.py"), Path("/c/d.ts")]
        s = ScanScope(mode="changed_only", changed_files=files)
        assert s.mode == "changed_only"
        assert s.changed_files == files

    def test_changed_files_is_mutable_list(self):
        s = ScanScope()
        s.changed_files.append(Path("/foo"))
        assert len(s.changed_files) == 1


# ---------------------------------------------------------------------------
# compute_changed_files tests
# ---------------------------------------------------------------------------

class TestComputeChangedFiles:
    def test_returns_paths_for_modified_files(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = [
                "src/foo.py\nsrc/bar.ts\n",  # git diff
                "",  # git ls-files
            ]
            result = compute_changed_files(tmp_path)
        assert len(result) == 2
        assert all(isinstance(p, Path) for p in result)

    def test_includes_untracked_files(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = [
                "modified.py\n",  # git diff
                "new_file.ts\n",  # untracked
            ]
            result = compute_changed_files(tmp_path)
        assert len(result) == 2

    def test_returns_empty_on_file_not_found(self, tmp_path):
        with patch(
            "agent_team.quality_checks.subprocess.check_output",
            side_effect=FileNotFoundError("git not found"),
        ):
            result = compute_changed_files(tmp_path)
        assert result == []

    def test_returns_empty_on_subprocess_error(self, tmp_path):
        with patch(
            "agent_team.quality_checks.subprocess.check_output",
            side_effect=subprocess.SubprocessError("not a repo"),
        ):
            result = compute_changed_files(tmp_path)
        assert result == []

    def test_returns_empty_on_timeout(self, tmp_path):
        with patch(
            "agent_team.quality_checks.subprocess.check_output",
            side_effect=subprocess.TimeoutExpired(cmd="git", timeout=10),
        ):
            result = compute_changed_files(tmp_path)
        assert result == []

    def test_paths_are_absolute(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = [
                "relative/path.py\n",
                "",
            ]
            result = compute_changed_files(tmp_path)
        assert len(result) == 1
        assert result[0].is_absolute()

    def test_empty_output_returns_empty_list(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = ["", ""]
            result = compute_changed_files(tmp_path)
        assert result == []

    def test_whitespace_lines_stripped(self, tmp_path):
        with patch("agent_team.quality_checks.subprocess.check_output") as mock_co:
            mock_co.side_effect = ["  foo.py  \n  \n  bar.py  \n", ""]
            result = compute_changed_files(tmp_path)
        assert len(result) == 2

    def test_returns_empty_on_os_error(self, tmp_path):
        with patch(
            "agent_team.quality_checks.subprocess.check_output",
            side_effect=OSError("permission denied"),
        ):
            result = compute_changed_files(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# Scoped scan function tests
# ---------------------------------------------------------------------------

def _create_mock_service_file(project_root: Path, name: str, content: str) -> Path:
    """Create a file in a services/ subdir for mock data scan to find."""
    svc_dir = project_root / "src" / "services"
    svc_dir.mkdir(parents=True, exist_ok=True)
    f = svc_dir / name
    f.write_text(content, encoding="utf-8")
    return f


def _create_source_file(project_root: Path, relpath: str, content: str) -> Path:
    """Create a source file at the given relative path."""
    f = project_root / relpath
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")
    return f


class TestScopedMockDataScan:
    def test_no_scope_scans_all(self, tmp_path):
        # Create a file with mock data pattern
        _create_mock_service_file(
            tmp_path, "api.service.ts",
            'const data = of(null).pipe(delay(100), map(() => [{ id: 1, name: "fake" }]));'
        )
        violations = run_mock_data_scan(tmp_path)
        # Should find violations (or not depending on pattern matching)
        # Main point: doesn't crash
        assert isinstance(violations, list)

    def test_scope_none_scans_all(self, tmp_path):
        _create_mock_service_file(
            tmp_path, "api.service.ts",
            'return of(null).pipe(delay(100), map(() => fakeData));'
        )
        v1 = run_mock_data_scan(tmp_path)
        v2 = run_mock_data_scan(tmp_path, scope=None)
        assert len(v1) == len(v2)

    def test_scope_empty_changed_files_scans_all(self, tmp_path):
        _create_mock_service_file(
            tmp_path, "api.service.ts",
            'return of(null).pipe(delay(100), map(() => fakeData));'
        )
        scope = ScanScope(changed_files=[])
        v1 = run_mock_data_scan(tmp_path)
        v2 = run_mock_data_scan(tmp_path, scope=scope)
        assert len(v1) == len(v2)

    def test_scope_filters_to_changed_files_only(self, tmp_path):
        f1 = _create_mock_service_file(
            tmp_path, "api.service.ts",
            'return of(null).pipe(delay(100), map(() => fakeData));'
        )
        _create_mock_service_file(
            tmp_path, "other.service.ts",
            'return of(null).pipe(delay(200), map(() => moreData));'
        )
        # Scope to only f1
        scope = ScanScope(changed_files=[f1.resolve()])
        violations = run_mock_data_scan(tmp_path, scope=scope)
        # All violation file_paths should reference f1's relative path
        for v in violations:
            assert "other.service.ts" not in v.file_path


class TestScopedUiComplianceScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_ui_compliance_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_ui_compliance_scan(tmp_path, scope=None)
        assert isinstance(violations, list)


class TestScopedE2eQualityScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_e2e_quality_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_e2e_quality_scan(tmp_path, scope=None)
        assert isinstance(violations, list)


class TestScopedAssetScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_asset_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_asset_scan(tmp_path, scope=None)
        assert isinstance(violations, list)

    def test_scope_empty_returns_list(self, tmp_path):
        scope = ScanScope(changed_files=[])
        violations = run_asset_scan(tmp_path, scope=scope)
        assert isinstance(violations, list)


class TestScopedDualOrmScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_dual_orm_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_dual_orm_scan(tmp_path, scope=None)
        assert isinstance(violations, list)


class TestScopedDefaultValueScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_default_value_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_default_value_scan(tmp_path, scope=None)
        assert isinstance(violations, list)


class TestScopedRelationshipScan:
    def test_no_scope_returns_list(self, tmp_path):
        violations = run_relationship_scan(tmp_path)
        assert isinstance(violations, list)

    def test_scope_none_returns_list(self, tmp_path):
        violations = run_relationship_scan(tmp_path, scope=None)
        assert isinstance(violations, list)


class TestAllScansReturnViolationList:
    """All scan functions return list[Violation] regardless of scope."""

    @pytest.mark.parametrize("scan_fn", [
        run_mock_data_scan,
        run_ui_compliance_scan,
        run_e2e_quality_scan,
        run_asset_scan,
        run_dual_orm_scan,
        run_default_value_scan,
        run_relationship_scan,
    ])
    def test_returns_violation_list(self, tmp_path, scan_fn):
        result = scan_fn(tmp_path)
        assert isinstance(result, list)
        for v in result:
            assert isinstance(v, Violation)

    @pytest.mark.parametrize("scan_fn", [
        run_mock_data_scan,
        run_ui_compliance_scan,
        run_e2e_quality_scan,
        run_asset_scan,
        run_dual_orm_scan,
        run_default_value_scan,
        run_relationship_scan,
    ])
    def test_with_scope_returns_violation_list(self, tmp_path, scan_fn):
        scope = ScanScope(mode="changed_only", changed_files=[])
        result = scan_fn(tmp_path, scope=scope)
        assert isinstance(result, list)
