"""Tests for agent_team.contracts — serialization, symbol detection, and verification."""

from __future__ import annotations

import json

import pytest

from agent_team.contracts import (
    ContractRegistry,
    ContractViolation,
    ExportedSymbol,
    ModuleContract,
    VerificationResult,
    WiringContract,
    _symbol_present_py,
    _symbol_present_ts,
    load_contracts,
    save_contracts,
    verify_all_contracts,
    verify_module_contract,
    verify_wiring_contract,
)


# ===================================================================
# 1. JSON Serialization / Deserialization
# ===================================================================


class TestContractSerialization:
    """Round-trip persistence through save_contracts / load_contracts."""

    def test_save_load_roundtrip(self, tmp_path):
        """A populated registry survives a save-then-load cycle."""
        registry = ContractRegistry()
        registry.modules["src/auth.py"] = ModuleContract(
            module_path="src/auth.py",
            exports=[
                ExportedSymbol(name="AuthService", kind="class", signature=None),
                ExportedSymbol(name="login", kind="function", signature="(user: str) -> bool"),
            ],
            created_by_task="TASK-001",
        )
        registry.wirings.append(
            WiringContract(
                source_module="src/routes/auth.py",
                target_module="src/auth.py",
                imports=["AuthService"],
                created_by_task="TASK-001",
            )
        )

        path = tmp_path / "CONTRACTS.json"
        save_contracts(registry, path)
        loaded = load_contracts(path)

        assert "src/auth.py" in loaded.modules
        mod = loaded.modules["src/auth.py"]
        assert len(mod.exports) == 2
        assert mod.exports[0].name == "AuthService"
        assert mod.exports[0].kind == "class"
        assert mod.exports[1].signature == "(user: str) -> bool"
        assert mod.created_by_task == "TASK-001"

        assert len(loaded.wirings) == 1
        assert loaded.wirings[0].imports == ["AuthService"]

    def test_empty_registry_roundtrip(self, tmp_path):
        """An empty registry round-trips without error."""
        registry = ContractRegistry()
        path = tmp_path / "CONTRACTS.json"

        save_contracts(registry, path)
        loaded = load_contracts(path)

        assert loaded.modules == {}
        assert loaded.wirings == []

    def test_version_field_present(self, tmp_path):
        """The serialized JSON must contain a top-level 'version' key."""
        registry = ContractRegistry()
        path = tmp_path / "CONTRACTS.json"
        save_contracts(registry, path)

        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "version" in raw
        assert raw["version"] == "1.0"

    def test_load_nonexistent_returns_empty(self, tmp_path):
        """Loading a missing file returns a fresh empty registry."""
        path = tmp_path / "nonexistent" / "CONTRACTS.json"
        registry = load_contracts(path)

        assert isinstance(registry, ContractRegistry)
        assert registry.modules == {}
        assert registry.wirings == []

    def test_load_malformed_json_raises(self, tmp_path):
        """Malformed JSON must propagate a JSONDecodeError."""
        path = tmp_path / "CONTRACTS.json"
        path.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_contracts(path)


# ===================================================================
# 2. Symbol Presence — Python
# ===================================================================


class TestSymbolPresentPython:
    """Unit tests for _symbol_present_py() against various Python constructs."""

    def test_function_found(self):
        src = "def hello():\n    pass\n"
        sym = ExportedSymbol(name="hello", kind="function")
        assert _symbol_present_py(src, sym) is True

    def test_async_function_found(self):
        src = "async def fetch_data():\n    pass\n"
        sym = ExportedSymbol(name="fetch_data", kind="function")
        assert _symbol_present_py(src, sym) is True

    def test_class_found(self):
        src = "class MyService:\n    pass\n"
        sym = ExportedSymbol(name="MyService", kind="class")
        assert _symbol_present_py(src, sym) is True

    def test_constant_found(self):
        src = "MAX_RETRIES = 5\n"
        sym = ExportedSymbol(name="MAX_RETRIES", kind="const")
        assert _symbol_present_py(src, sym) is True

    def test_annotated_assignment_found(self):
        src = "DEFAULT_TIMEOUT: int = 30\n"
        sym = ExportedSymbol(name="DEFAULT_TIMEOUT", kind="const")
        assert _symbol_present_py(src, sym) is True

    def test_all_dunder_takes_priority(self):
        """When __all__ is present, only names listed there are considered exported."""
        src = (
            "__all__ = ['public_func']\n"
            "\n"
            "def public_func():\n"
            "    pass\n"
            "\n"
            "def _helper():\n"
            "    pass\n"
        )
        sym_public = ExportedSymbol(name="public_func", kind="function")
        sym_helper = ExportedSymbol(name="_helper", kind="function")

        assert _symbol_present_py(src, sym_public) is True
        assert _symbol_present_py(src, sym_helper) is False

    def test_symbol_in_all_not_in_body(self):
        """A symbol listed in __all__ but not defined in the top-level body
        is still treated as exported (it may be imported from elsewhere)."""
        src = "__all__ = ['ExternalWidget']\n"
        sym = ExportedSymbol(name="ExternalWidget", kind="class")
        assert _symbol_present_py(src, sym) is True

    def test_symbol_not_in_all(self):
        """A top-level definition that is NOT in __all__ is not exported."""
        src = (
            "__all__ = ['kept']\n"
            "\n"
            "def kept():\n    pass\n"
            "def excluded():\n    pass\n"
        )
        sym = ExportedSymbol(name="excluded", kind="function")
        assert _symbol_present_py(src, sym) is False

    def test_missing_symbol(self):
        src = "def something_else():\n    pass\n"
        sym = ExportedSymbol(name="nonexistent", kind="function")
        assert _symbol_present_py(src, sym) is False

    def test_syntax_error_returns_false(self):
        src = "def broken(\n"
        sym = ExportedSymbol(name="broken", kind="function")
        assert _symbol_present_py(src, sym) is False

    def test_private_not_found(self):
        """Private names (underscore-prefixed) are not in __all__ and do not
        match via body scan when __all__ is authoritative."""
        src = (
            "__all__ = ['PublicAPI']\n"
            "\n"
            "class PublicAPI:\n    pass\n"
            "\n"
            "def _internal_helper():\n    pass\n"
        )
        sym = ExportedSymbol(name="_internal_helper", kind="function")
        assert _symbol_present_py(src, sym) is False


# ===================================================================
# 3. Symbol Presence — TypeScript
# ===================================================================


class TestSymbolPresentTS:
    """Unit tests for _symbol_present_ts() against TS/JS export forms."""

    def test_export_function(self):
        src = "export function greet(name: string): void {}\n"
        sym = ExportedSymbol(name="greet", kind="function")
        assert _symbol_present_ts(src, sym) is True

    def test_export_class(self):
        src = "export class UserService {}\n"
        sym = ExportedSymbol(name="UserService", kind="class")
        assert _symbol_present_ts(src, sym) is True

    def test_export_const(self):
        src = "export const API_URL = 'https://api.example.com';\n"
        sym = ExportedSymbol(name="API_URL", kind="const")
        assert _symbol_present_ts(src, sym) is True

    def test_export_default(self):
        src = "export default class AppRouter {}\n"
        sym = ExportedSymbol(name="AppRouter", kind="class")
        assert _symbol_present_ts(src, sym) is True

    def test_export_type(self):
        src = "export type UserID = string;\n"
        sym = ExportedSymbol(name="UserID", kind="type")
        assert _symbol_present_ts(src, sym) is True

    def test_export_interface(self):
        src = "export interface Config {\n  host: string;\n}\n"
        sym = ExportedSymbol(name="Config", kind="interface")
        assert _symbol_present_ts(src, sym) is True

    def test_export_enum(self):
        src = "export enum Color { Red, Green, Blue }\n"
        sym = ExportedSymbol(name="Color", kind="type")
        assert _symbol_present_ts(src, sym) is True

    def test_named_export_in_braces(self):
        """Re-export via `export { Foo }` form."""
        src = "class Foo {}\nexport { Foo }\n"
        sym = ExportedSymbol(name="Foo", kind="class")
        assert _symbol_present_ts(src, sym) is True

    def test_missing_symbol(self):
        src = "export function other(): void {}\n"
        sym = ExportedSymbol(name="missing", kind="function")
        assert _symbol_present_ts(src, sym) is False


# ===================================================================
# 4. Module Contract Verification
# ===================================================================


class TestVerifyModuleContract:
    """Integration tests for verify_module_contract() using real files."""

    def test_all_symbols_present(self, tmp_path):
        """No violations when every declared symbol exists."""
        py_file = tmp_path / "src" / "service.py"
        py_file.parent.mkdir(parents=True, exist_ok=True)
        py_file.write_text(
            "class UserService:\n    pass\n\n"
            "def get_user():\n    pass\n",
            encoding="utf-8",
        )

        contract = ModuleContract(
            module_path="src/service.py",
            exports=[
                ExportedSymbol(name="UserService", kind="class"),
                ExportedSymbol(name="get_user", kind="function"),
            ],
        )
        violations = verify_module_contract(contract, tmp_path)
        assert violations == []

    def test_missing_symbol_violation(self, tmp_path):
        """A violation is raised for each missing symbol."""
        py_file = tmp_path / "src" / "service.py"
        py_file.parent.mkdir(parents=True, exist_ok=True)
        py_file.write_text("def get_user():\n    pass\n", encoding="utf-8")

        contract = ModuleContract(
            module_path="src/service.py",
            exports=[
                ExportedSymbol(name="get_user", kind="function"),
                ExportedSymbol(name="MissingClass", kind="class"),
            ],
        )
        violations = verify_module_contract(contract, tmp_path)
        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "MissingClass" in violations[0].description

    def test_file_not_found_violation(self, tmp_path):
        """A missing file produces a single 'file not found' violation."""
        contract = ModuleContract(
            module_path="src/does_not_exist.py",
            exports=[ExportedSymbol(name="X", kind="class")],
        )
        violations = verify_module_contract(contract, tmp_path)
        assert len(violations) == 1
        assert "not found" in violations[0].description
        assert violations[0].severity == "error"

    def test_python_module(self, tmp_path):
        """Verify a Python file with __all__."""
        py_file = tmp_path / "mod.py"
        py_file.write_text(
            "__all__ = ['create_app']\n\n"
            "def create_app():\n    pass\n\n"
            "def _internal():\n    pass\n",
            encoding="utf-8",
        )

        contract = ModuleContract(
            module_path="mod.py",
            exports=[ExportedSymbol(name="create_app", kind="function")],
        )
        violations = verify_module_contract(contract, tmp_path)
        assert violations == []

    def test_typescript_module(self, tmp_path):
        """Verify a TypeScript file with export declarations."""
        ts_file = tmp_path / "index.ts"
        ts_file.write_text(
            "export interface AppConfig {\n  port: number;\n}\n\n"
            "export function startServer(config: AppConfig): void {}\n",
            encoding="utf-8",
        )

        contract = ModuleContract(
            module_path="index.ts",
            exports=[
                ExportedSymbol(name="AppConfig", kind="interface"),
                ExportedSymbol(name="startServer", kind="function"),
            ],
        )
        violations = verify_module_contract(contract, tmp_path)
        assert violations == []


# ===================================================================
# 5. Wiring Contract Verification
# ===================================================================


class TestVerifyWiringContract:
    """Integration tests for verify_wiring_contract() using real files."""

    def test_happy_path(self, tmp_path):
        """No violations when target exports and source imports the symbol."""
        target = tmp_path / "lib" / "db.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "class Database:\n    pass\n\n"
            "def connect():\n    pass\n",
            encoding="utf-8",
        )

        source = tmp_path / "app" / "main.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "from lib.db import Database, connect\n\n"
            "db = Database()\n",
            encoding="utf-8",
        )

        wiring = WiringContract(
            source_module="app/main.py",
            target_module="lib/db.py",
            imports=["Database", "connect"],
        )
        violations = verify_wiring_contract(wiring, tmp_path)
        assert violations == []

    def test_missing_export_in_target(self, tmp_path):
        """Violation when target does not export a declared symbol."""
        target = tmp_path / "lib" / "db.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def connect():\n    pass\n", encoding="utf-8")

        source = tmp_path / "app" / "main.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "from lib.db import Database\n",
            encoding="utf-8",
        )

        wiring = WiringContract(
            source_module="app/main.py",
            target_module="lib/db.py",
            imports=["Database"],
        )
        violations = verify_wiring_contract(wiring, tmp_path)
        # At least one violation for missing export
        export_violations = [
            v for v in violations if "does not export" in v.description
        ]
        assert len(export_violations) >= 1

    def test_file_not_found(self, tmp_path):
        """Violation when either source or target file is missing."""
        wiring = WiringContract(
            source_module="missing/source.py",
            target_module="missing/target.py",
            imports=["SomeSymbol"],
        )
        violations = verify_wiring_contract(wiring, tmp_path)
        assert len(violations) >= 2  # both files missing
        descriptions = " ".join(v.description for v in violations)
        assert "not found" in descriptions


# ===================================================================
# 6. Full Registry Verification
# ===================================================================


class TestVerifyAllContracts:
    """End-to-end tests for verify_all_contracts()."""

    def test_all_pass(self, tmp_path):
        """A clean codebase produces a passing result with zero violations."""
        py_file = tmp_path / "utils.py"
        py_file.write_text(
            "def parse(data: str) -> dict:\n    return {}\n\n"
            "MAX_SIZE = 100\n",
            encoding="utf-8",
        )

        registry = ContractRegistry()
        registry.modules["utils.py"] = ModuleContract(
            module_path="utils.py",
            exports=[
                ExportedSymbol(name="parse", kind="function"),
                ExportedSymbol(name="MAX_SIZE", kind="const"),
            ],
        )

        result = verify_all_contracts(registry, tmp_path)
        assert result.passed is True
        assert result.violations == []
        assert result.checked_modules == 1
        assert result.checked_wirings == 0

    def test_mixed_results(self, tmp_path):
        """Registry with one passing and one failing module."""
        good = tmp_path / "good.py"
        good.write_text("def hello():\n    pass\n", encoding="utf-8")

        registry = ContractRegistry()
        registry.modules["good.py"] = ModuleContract(
            module_path="good.py",
            exports=[ExportedSymbol(name="hello", kind="function")],
        )
        registry.modules["bad.py"] = ModuleContract(
            module_path="bad.py",
            exports=[ExportedSymbol(name="missing_fn", kind="function")],
        )

        result = verify_all_contracts(registry, tmp_path)
        assert result.passed is False
        assert len(result.violations) >= 1
        assert result.checked_modules == 2

    def test_empty_registry(self, tmp_path):
        """An empty registry passes vacuously."""
        registry = ContractRegistry()
        result = verify_all_contracts(registry, tmp_path)

        assert result.passed is True
        assert result.violations == []
        assert result.checked_modules == 0
        assert result.checked_wirings == 0


# ===================================================================
# 7. _read_file_safe Error Handling Tests
# ===================================================================


class TestReadFileSafeErrors:
    """Tests for file reading error handling in contracts."""

    def test_binary_file_handled(self, tmp_path):
        """Binary file should not crash contract verification."""
        bin_file = tmp_path / "binary.py"
        bin_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")
        registry = ContractRegistry()
        registry.modules["binary.py"] = ModuleContract(
            module_path="binary.py",
            exports=[ExportedSymbol(name="X", kind="class")],
        )
        # Should not raise, just report violations
        result = verify_all_contracts(registry, tmp_path)
        assert result.passed is False


# ===================================================================
# 8. Shared Language Detection (Finding #11)
# ===================================================================


class TestLanguageDetectionShared:
    """Tests for Finding #11: shared language detection via _lang module."""

    def test_python_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("foo.py") == "python"

    def test_python_pyw_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("script.pyw") == "python"

    def test_typescript_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("bar.ts") == "typescript"

    def test_typescript_tsx_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("component.tsx") == "typescript"

    def test_javascript_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("index.js") == "javascript"

    def test_javascript_jsx_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("page.jsx") == "javascript"

    def test_javascript_mjs_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("config.mjs") == "javascript"

    def test_javascript_cjs_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("legacy.cjs") == "javascript"

    def test_unknown_extension(self):
        from agent_team._lang import detect_language
        assert detect_language("file.xyz") == "unknown"

    def test_go_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("main.go") == "go"

    def test_rust_detected(self):
        from agent_team._lang import detect_language
        assert detect_language("lib.rs") == "rust"

    def test_case_insensitive_via_posix_suffix(self):
        from agent_team._lang import detect_language
        assert detect_language("Module.PY") == "python"

    def test_contracts_uses_shared_detect(self):
        """Verify contracts._detect_language is the shared implementation."""
        from agent_team._lang import detect_language
        from agent_team.contracts import _detect_language
        assert _detect_language is detect_language
