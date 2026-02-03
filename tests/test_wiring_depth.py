"""Tests for wiring depth verification (Agents 10, 15)."""
from __future__ import annotations

import pytest
from pathlib import Path

from agent_team.contracts import (
    ContractRegistry,
    WiringContract,
    verify_wiring_contract,
)
from agent_team.wiring import detect_wiring_deps, build_wiring_schedule_hint


class TestSymbolUsageVerification:
    """Test that imported-but-unused symbols are caught (Root Cause #7)."""

    def test_used_symbol_passes(self, tmp_path):
        # Target exports, source imports AND uses
        target = tmp_path / "service.ts"
        target.write_text("export function fetchUser() { return {} }", encoding="utf-8")
        source = tmp_path / "page.ts"
        source.write_text(
            'import { fetchUser } from "./service"\n'
            'const data = fetchUser()\n',
            encoding="utf-8",
        )
        contract = WiringContract(
            source_module="page.ts",
            target_module="service.ts",
            imports=["fetchUser"],
        )
        violations = verify_wiring_contract(contract, tmp_path)
        assert len(violations) == 0

    def test_imported_but_unused_caught(self, tmp_path):
        target = tmp_path / "service.ts"
        target.write_text("export function fetchUser() { return {} }", encoding="utf-8")
        source = tmp_path / "page.ts"
        source.write_text(
            'import { fetchUser } from "./service"\n'
            '// the symbol is never called\n'
            'console.log("hello")\n',
            encoding="utf-8",
        )
        contract = WiringContract(
            source_module="page.ts",
            target_module="service.ts",
            imports=["fetchUser"],
        )
        violations = verify_wiring_contract(contract, tmp_path)
        assert any("imported but never used" in v.description for v in violations)
        assert any(v.severity == "warning" for v in violations)

    def test_missing_import_still_error(self, tmp_path):
        target = tmp_path / "service.ts"
        target.write_text("export function fetchUser() { return {} }", encoding="utf-8")
        source = tmp_path / "page.ts"
        source.write_text('console.log("no import")\n', encoding="utf-8")
        contract = WiringContract(
            source_module="page.ts",
            target_module="service.ts",
            imports=["fetchUser"],
        )
        violations = verify_wiring_contract(contract, tmp_path)
        assert any("does not import" in v.description for v in violations)
        assert any(v.severity == "error" for v in violations)


class TestDetectWiringDeps:
    def test_empty_content(self):
        assert detect_wiring_deps("") == {}
        assert detect_wiring_deps("   ") == {}

    def test_no_wire_tasks(self):
        md = (
            "### TASK-001: Create service\n"
            "- Parent: REQ-001\n"
            "- Dependencies: none\n"
            "- Files: src/service.ts\n"
            "- Status: PENDING\n"
        )
        assert detect_wiring_deps(md) == {}

    def test_wire_task_detected(self):
        md = (
            "### TASK-001: Create auth\n"
            "- Parent: REQ-001\n"
            "- Dependencies: none\n"
            "- Files: src/auth.ts\n"
            "- Status: PENDING\n\n"
            "### TASK-002: Wire auth to routes\n"
            "- Parent: WIRE-001\n"
            "- Dependencies: TASK-001\n"
            "- Files: src/routes.ts\n"
            "- Status: PENDING\n"
        )
        result = detect_wiring_deps(md)
        assert "WIRE-001" in result
        assert "TASK-001" in result["WIRE-001"]

    def test_multiple_wire_deps(self):
        md = (
            "### TASK-001: Create auth\n"
            "- Parent: REQ-001\n"
            "- Dependencies: none\n- Files: src/auth.ts\n- Status: PENDING\n\n"
            "### TASK-002: Create users\n"
            "- Parent: REQ-002\n"
            "- Dependencies: none\n- Files: src/users.ts\n- Status: PENDING\n\n"
            "### TASK-003: Wire both\n"
            "- Parent: WIRE-001\n"
            "- Dependencies: TASK-001, TASK-002\n"
            "- Files: src/app.ts\n- Status: PENDING\n"
        )
        result = detect_wiring_deps(md)
        assert set(result["WIRE-001"]) == {"TASK-001", "TASK-002"}


class TestBuildWiringScheduleHint:
    def test_empty_returns_message(self):
        hint = build_wiring_schedule_hint("")
        assert "No wiring" in hint or "empty" in hint.lower()

    def test_no_wire_tasks(self):
        md = "### TASK-001: Do stuff\n- Parent: REQ-001\n- Status: PENDING\n"
        hint = build_wiring_schedule_hint(md)
        assert "No wiring" in hint

    def test_hint_includes_wire_id(self):
        md = (
            "### TASK-001: Create auth\n"
            "- Parent: REQ-001\n- Dependencies: none\n- Status: PENDING\n\n"
            "### TASK-002: Wire auth\n"
            "- Parent: WIRE-001\n- Dependencies: TASK-001\n- Status: PENDING\n"
        )
        hint = build_wiring_schedule_hint(md)
        assert "WIRE-001" in hint
        assert "TASK-001" in hint
