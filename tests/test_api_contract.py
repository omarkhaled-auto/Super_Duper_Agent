"""Tests for API Contract Verification (Prevention + Detection + Guarantee)."""
from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_team.quality_checks import (
    ScanScope,
    Violation,
    _MAX_VIOLATIONS,
    _parse_field_schema,
    _parse_svc_table,
    _to_pascal_case,
    run_api_contract_scan,
    SvcContract,
)
from agent_team.config import (
    AgentTeamConfig,
    PostOrchestrationScanConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.code_quality_standards import (
    API_CONTRACT_STANDARDS,
    _AGENT_STANDARDS_MAP,
    get_standards_for_agent,
    FRONTEND_STANDARDS,
    BACKEND_STANDARDS,
    DATABASE_INTEGRITY_STANDARDS,
)

# Source root for prompt/standard assertions
_SRC = Path(__file__).resolve().parent.parent / "src" / "agent_team"


# ============================================================
# Helpers
# ============================================================
def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ============================================================
# Group 1: _parse_field_schema tests
# ============================================================
class TestParseFieldSchema:
    """Test _parse_field_schema() parsing logic."""

    def test_simple_schema(self):
        result = _parse_field_schema("{ id: number, title: string }")
        assert result == {"id": "number", "title": "string"}

    def test_nested_object(self):
        result = _parse_field_schema("{ user: { id: number, name: string } }")
        assert "user" in result
        # The nested object should be captured as a type string
        assert "id" in result["user"] or "{" in result["user"]

    def test_array_type(self):
        result = _parse_field_schema("{ items: Array<{ id: number }> }")
        assert "items" in result

    def test_class_name_only_returns_empty(self):
        """Class name without braces = legacy entry, returns empty dict."""
        result = _parse_field_schema("TenderListDto")
        assert result == {}

    def test_empty_string(self):
        assert _parse_field_schema("") == {}

    def test_dash_returns_empty(self):
        assert _parse_field_schema("-") == {}

    def test_multiple_fields(self):
        result = _parse_field_schema('{ id: number, name: string, status: "draft"|"active", createdAt: string }')
        assert len(result) == 4
        assert result["id"] == "number"
        assert result["name"] == "string"
        assert result["createdAt"] == "string"

    def test_enum_type(self):
        result = _parse_field_schema('{ status: "draft"|"active"|"closed" }')
        assert "status" in result

    def test_whitespace_handling(self):
        result = _parse_field_schema("{  id : number ,  name : string  }")
        assert result == {"id": "number", "name": "string"}


# ============================================================
# Group 2: _parse_svc_table tests
# ============================================================
class TestParseSvcTable:
    """Test SVC-xxx table parsing from REQUIREMENTS.md content."""

    def test_standard_table(self):
        text = textwrap.dedent("""\
            | SVC-ID | Frontend Service.Method | Backend Endpoint | HTTP Method | Request DTO | Response DTO |
            |--------|------------------------|------------------|-------------|-------------|--------------|
            | SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | { id: number, title: string, status: string } |
            | SVC-002 | AuthService.login() | POST /api/auth/login | POST | { email: string, password: string } | { token: string, userId: number } |
        """)
        contracts = _parse_svc_table(text)
        assert len(contracts) == 2
        assert contracts[0].svc_id == "SVC-001"
        assert contracts[0].response_fields["id"] == "number"
        assert contracts[0].response_fields["title"] == "string"
        assert contracts[1].request_fields["email"] == "string"

    def test_legacy_class_name_only(self):
        """Legacy SVC-xxx rows with class names should have empty field dicts."""
        text = "| SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | TenderListDto |"
        contracts = _parse_svc_table(text)
        assert len(contracts) == 1
        assert contracts[0].response_fields == {}

    def test_empty_requirements(self):
        assert _parse_svc_table("") == []

    def test_no_svc_table(self):
        text = "# Requirements\n- [ ] FUNC-001: Some feature"
        assert _parse_svc_table(text) == []

    def test_mixed_legacy_and_schema(self):
        text = textwrap.dedent("""\
            | SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | TenderListDto |
            | SVC-002 | BidService.submit() | POST /api/bids | POST | { amount: number } | { id: number, status: string } |
        """)
        contracts = _parse_svc_table(text)
        assert len(contracts) == 2
        assert contracts[0].response_fields == {}
        assert contracts[1].response_fields == {"id": "number", "status": "string"}

    def test_svc_id_extraction(self):
        text = "| SVC-042 | FooService.bar() | GET /api/foo | GET | - | { x: number } |"
        contracts = _parse_svc_table(text)
        assert len(contracts) == 1
        assert contracts[0].svc_id == "SVC-042"
        assert contracts[0].frontend_service_method == "FooService.bar()"
        assert contracts[0].http_method == "GET"

    def test_request_and_response_fields(self):
        text = "| SVC-001 | Svc.m() | POST /api/x | POST | { a: string, b: number } | { c: boolean } |"
        contracts = _parse_svc_table(text)
        assert len(contracts) == 1
        assert contracts[0].request_fields == {"a": "string", "b": "number"}
        assert contracts[0].response_fields == {"c": "boolean"}


# ============================================================
# Group 3: _to_pascal_case tests
# ============================================================
class TestToPascalCase:
    def test_camel_to_pascal(self):
        assert _to_pascal_case("tenderTitle") == "TenderTitle"

    def test_single_char(self):
        assert _to_pascal_case("x") == "X"

    def test_already_pascal(self):
        assert _to_pascal_case("TenderTitle") == "TenderTitle"

    def test_empty_string(self):
        assert _to_pascal_case("") == ""

    def test_id(self):
        assert _to_pascal_case("id") == "Id"

    def test_short_word(self):
        assert _to_pascal_case("ab") == "Ab"


# ============================================================
# Group 4: run_api_contract_scan integration tests
# ============================================================
class TestRunApiContractScan:
    """Integration tests for the full scan pipeline."""

    def test_no_requirements_returns_empty(self, tmp_path):
        violations = run_api_contract_scan(tmp_path)
        assert violations == []

    def test_legacy_svc_table_returns_zero(self, tmp_path):
        """Backward compat: class names only -> no violations."""
        req = tmp_path / "REQUIREMENTS.md"
        req.write_text(
            "| SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | TenderListDto |\n",
            encoding="utf-8",
        )
        violations = run_api_contract_scan(tmp_path)
        assert violations == []

    def test_matching_fields_no_violations(self, tmp_path):
        """When backend + frontend both have the fields, no violations."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | { id: number, title: string } |\n")
        # Use non-overlapping paths: controllers/ for backend, interfaces/ for frontend
        _make_file(tmp_path, "controllers/TenderController.cs",
            "public class TenderController { public int Id { get; set; } public string Title { get; set; } }")
        _make_file(tmp_path, "interfaces/tender.ts",
            "export interface Tender { id: number; title: string; }")
        violations = run_api_contract_scan(tmp_path)
        assert violations == []

    def test_backend_missing_field_api001(self, tmp_path):
        """API-001: backend DTO missing a field from the schema."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | { id: number, title: string, description: string } |\n")
        # controllers/ only matches backend pattern, not frontend
        _make_file(tmp_path, "controllers/TenderController.cs",
            "public class TenderController { public int Id { get; set; } public string Title { get; set; } }")
        # interfaces/ only matches frontend pattern, not backend
        _make_file(tmp_path, "interfaces/tender.ts",
            "export interface Tender { id: number; title: string; description: string; }")
        violations = run_api_contract_scan(tmp_path)
        api001 = [v for v in violations if v.check == "API-001"]
        assert len(api001) >= 1
        assert "description" in api001[0].message.lower() or "Description" in api001[0].message

    def test_frontend_missing_field_api002(self, tmp_path):
        """API-002: frontend model missing a field from the schema."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | TenderService.getAll() | GET /api/tenders | GET | - | { id: number, title: string, description: string } |\n")
        # handlers/ only matches backend pattern
        _make_file(tmp_path, "handlers/TenderHandler.cs",
            "public class TenderHandler { public int Id { get; set; } public string Title { get; set; } public string Description { get; set; } }")
        # interfaces/ only matches frontend pattern
        _make_file(tmp_path, "interfaces/tender.ts",
            "export interface Tender { id: number; title: string; }")
        violations = run_api_contract_scan(tmp_path)
        api002 = [v for v in violations if v.check == "API-002"]
        assert len(api002) >= 1
        assert "description" in api002[0].message.lower()

    def test_type_mismatch_api003(self, tmp_path):
        """API-003: unusual type triggers a warning."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: weirdtype, title: string } |\n")
        _make_file(tmp_path, "controllers/ItemController.cs",
            "public class ItemController { public int Id { get; set; } public string Title { get; set; } }")
        _make_file(tmp_path, "interfaces/item.ts",
            "export interface Item { id: number; title: string; }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        assert len(api003) >= 1
        assert api003[0].severity == "warning"
        assert "weirdtype" in api003[0].message

    def test_known_types_no_api003(self, tmp_path):
        """Known types (number, string, boolean) should NOT trigger API-003."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, name: string, active: boolean } |\n")
        _make_file(tmp_path, "controllers/Controller.cs",
            "public class Controller { public int Id { get; set; } public string Name { get; set; } public bool Active { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts",
            "export interface Model { id: number; name: string; active: boolean; }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        assert api003 == []

    def test_milestone_requirements(self, tmp_path):
        """Should also check milestone REQUIREMENTS.md files."""
        ms_dir = tmp_path / ".agent-team" / "milestones" / "m1"
        ms_dir.mkdir(parents=True)
        _make_file(tmp_path, ".agent-team/milestones/m1/REQUIREMENTS.md",
            "| SVC-001 | SomeService.get() | GET /api/items | GET | - | { id: number, name: string } |\n")
        _make_file(tmp_path, "controllers/ItemController.cs",
            "public class ItemController { public int Id { get; set; } public string Name { get; set; } }")
        _make_file(tmp_path, "interfaces/item.ts",
            "export interface Item { id: number; name: string; }")
        violations = run_api_contract_scan(tmp_path)
        assert violations == []

    def test_violations_capped_at_max(self, tmp_path):
        """Violations should be capped at _MAX_VIOLATIONS."""
        # Create a REQUIREMENTS.md with many SVC entries that will generate violations
        rows = []
        for i in range(60):
            rows.append(f"| SVC-{i:03d} | Svc.m{i}() | GET /api/x{i} | GET | - | {{ field{i}a: string, field{i}b: number }} |")
        _make_file(tmp_path, "REQUIREMENTS.md", "\n".join(rows))
        # Create minimal backend file (controllers/) to trigger API-001 violations
        _make_file(tmp_path, "controllers/Dummy.cs", "public class Dummy { }")
        # Create minimal frontend file (interfaces/) to trigger API-002 violations
        _make_file(tmp_path, "interfaces/dummy.ts", "export interface Dummy { }")
        violations = run_api_contract_scan(tmp_path)
        assert len(violations) <= _MAX_VIOLATIONS

    def test_violations_sorted_by_severity(self, tmp_path):
        """Violations should be sorted by severity (error before warning)."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: weirdtype, title: string, missingField: number } |\n")
        # controllers/ = backend only; interfaces/ = frontend only
        _make_file(tmp_path, "controllers/Ctrl.cs",
            "public class Ctrl { public string Title { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts",
            "export interface Model { title: string; }")
        violations = run_api_contract_scan(tmp_path)
        if len(violations) >= 2:
            severities = [v.severity for v in violations]
            error_indices = [i for i, s in enumerate(severities) if s == "error"]
            warning_indices = [i for i, s in enumerate(severities) if s == "warning"]
            if error_indices and warning_indices:
                assert max(error_indices) < min(warning_indices)

    def test_no_backend_files_no_api001(self, tmp_path):
        """If no backend files exist, API-001 should not be raised."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, name: string } |\n")
        # interfaces/ = frontend only, no backend patterns match
        _make_file(tmp_path, "interfaces/iface.ts",
            "export interface Model { id: number; name: string; }")
        violations = run_api_contract_scan(tmp_path)
        api001 = [v for v in violations if v.check == "API-001"]
        assert api001 == []

    def test_no_frontend_files_no_api002(self, tmp_path):
        """If no frontend files exist, API-002 should not be raised."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, name: string } |\n")
        # controllers/ = backend only
        _make_file(tmp_path, "controllers/Ctrl.cs",
            "public class Ctrl { public int Id { get; set; } public string Name { get; set; } }")
        violations = run_api_contract_scan(tmp_path)
        api002 = [v for v in violations if v.check == "API-002"]
        assert api002 == []

    def test_agent_team_requirements(self, tmp_path):
        """Should check .agent-team/REQUIREMENTS.md too."""
        _make_file(tmp_path, ".agent-team/REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs",
            "public class Ctrl { public int Id { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts",
            "export interface Model { id: number; }")
        violations = run_api_contract_scan(tmp_path)
        assert violations == []


# ============================================================
# Group 5: Config tests
# ============================================================
class TestApiContractConfig:
    """Test config.py changes for api_contract_scan."""

    def test_default_enabled(self):
        cfg = PostOrchestrationScanConfig()
        assert cfg.api_contract_scan is True

    def test_explicit_false(self):
        cfg = PostOrchestrationScanConfig(api_contract_scan=False)
        assert cfg.api_contract_scan is False

    def test_dict_to_config_loads(self, tmp_path):
        data = {
            "post_orchestration_scans": {
                "api_contract_scan": False,
            }
        }
        cfg, overrides = _dict_to_config(data)
        assert cfg.post_orchestration_scans.api_contract_scan is False
        assert "post_orchestration_scans.api_contract_scan" in overrides

    def test_dict_to_config_default(self):
        cfg, overrides = _dict_to_config({})
        assert cfg.post_orchestration_scans.api_contract_scan is True

    def test_quick_depth_disables(self):
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.post_orchestration_scans.api_contract_scan is False

    def test_standard_depth_keeps_enabled(self):
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("standard", cfg, overrides)
        assert cfg.post_orchestration_scans.api_contract_scan is True

    def test_user_override_survives_quick_depth(self):
        """User override should survive quick depth gating."""
        data = {
            "post_orchestration_scans": {
                "api_contract_scan": True,
            }
        }
        cfg, overrides = _dict_to_config(data)
        apply_depth_quality_gating("quick", cfg, overrides)
        # User explicitly set it to True, so it should survive
        assert cfg.post_orchestration_scans.api_contract_scan is True


# ============================================================
# Group 6: Prompt content verification
# ============================================================
class TestPromptContent:
    """Verify prompt injections exist in agents.py."""

    def test_architect_has_field_schema_instructions(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "EXACT FIELD SCHEMAS IN SVC-xxx TABLE" in content

    def test_architect_has_pascal_case_note(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "PascalCase" in content and "camelCase" in content

    def test_code_writer_has_api_contract_compliance(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "API CONTRACT COMPLIANCE" in content

    def test_code_writer_has_violation_reference(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "API-001" in content and "API-002" in content

    def test_code_reviewer_has_field_verification(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "API Contract Field Verification" in content

    def test_code_reviewer_has_api003(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "API-003" in content

    def test_code_reviewer_preserves_svc_xxx_verification(self):
        """Existing SVC-xxx verification must still be present."""
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "Service-to-API Verification" in content
        assert "MOCK DATA IS THE #1 ANTI-PATTERN" in content

    def test_code_reviewer_preserves_ui_compliance(self):
        """UI Compliance Verification must still be present."""
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "UI Compliance Verification" in content


# ============================================================
# Group 7: Quality standards verification
# ============================================================
class TestQualityStandards:
    def test_api_contract_standards_exists(self):
        assert "API-001" in API_CONTRACT_STANDARDS
        assert "API-002" in API_CONTRACT_STANDARDS
        assert "API-003" in API_CONTRACT_STANDARDS

    def test_standards_mapped_to_code_writer(self):
        assert API_CONTRACT_STANDARDS in _AGENT_STANDARDS_MAP["code-writer"]

    def test_standards_mapped_to_code_reviewer(self):
        assert API_CONTRACT_STANDARDS in _AGENT_STANDARDS_MAP["code-reviewer"]

    def test_get_standards_includes_api_contract(self):
        writer_standards = get_standards_for_agent("code-writer")
        assert "API-001" in writer_standards
        reviewer_standards = get_standards_for_agent("code-reviewer")
        assert "API-001" in reviewer_standards

    def test_standards_contain_severity_info(self):
        assert "error" in API_CONTRACT_STANDARDS.lower()
        assert "warning" in API_CONTRACT_STANDARDS.lower()

    def test_standards_describe_all_checks(self):
        assert "Backend DTO Field Missing" in API_CONTRACT_STANDARDS
        assert "Frontend Model Field Mismatch" in API_CONTRACT_STANDARDS
        assert "Type Mismatch" in API_CONTRACT_STANDARDS


# ============================================================
# Group 8: CLI wiring verification (AST-based)
# ============================================================
class TestCLIWiring:
    """Verify CLI integration using AST analysis."""

    def test_run_api_contract_fix_exists(self):
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(content)
        func_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert "_run_api_contract_fix" in func_names

    def test_run_api_contract_fix_is_async(self):
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_run_api_contract_fix":
                return
        pytest.fail("_run_api_contract_fix should be async")

    def test_scan_invocation_exists(self):
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert "run_api_contract_scan" in content

    def test_scan_gated_on_config(self):
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert "config.post_orchestration_scans.api_contract_scan" in content

    def test_scan_gated_on_fullstack(self):
        """Scan must check has_backend and has_frontend."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the API contract scan block
        idx = content.find("API Contract Verification scan")
        assert idx > 0, "API Contract Verification scan block not found"
        block = content[idx:idx + 1000]
        assert "has_backend" in block and "has_frontend" in block

    def test_fix_added_to_recovery_types(self):
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert '"api_contract_fix"' in content

    def test_scan_before_e2e(self):
        """API contract scan must come before E2E Testing Phase."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        scan_pos = content.find("run_api_contract_scan")
        e2e_pos = content.find("E2E Testing Phase")
        assert scan_pos > 0, "run_api_contract_scan not found in cli.py"
        assert e2e_pos > 0, "E2E Testing Phase not found in cli.py"
        assert scan_pos < e2e_pos, "API contract scan must be before E2E Testing Phase"

    def test_scan_after_database(self):
        """API contract scan must come after database scans."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        scan_pos = content.find("run_api_contract_scan")
        db_pos = content.rfind("Relationship scan failed")
        assert scan_pos > 0
        assert db_pos > 0
        assert scan_pos > db_pos, "API contract scan must be after database scans"

    def test_crash_isolation(self):
        """Scan block must be wrapped in try/except."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the scan block
        idx = content.find("API Contract Verification scan")
        assert idx > 0
        block = content[idx - 200:idx + 1000]
        assert "try:" in block
        assert "except Exception" in block

    def test_fix_function_handles_empty_violations(self):
        """_run_api_contract_fix should return 0.0 for empty violations."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the function
        idx = content.find("async def _run_api_contract_fix")
        assert idx > 0
        func_block = content[idx:idx + 1000]
        assert "return 0.0" in func_block


# ============================================================
# Group 9: Backward compatibility
# ============================================================
class TestBackwardCompat:
    """Ensure no regressions with existing features."""

    def test_existing_prompts_preserved(self):
        """ARCHITECT, CODE_WRITER, CODE_REVIEWER prompts still export."""
        from agent_team.agents import (
            ARCHITECT_PROMPT,
            CODE_WRITER_PROMPT,
            CODE_REVIEWER_PROMPT,
        )
        assert ARCHITECT_PROMPT
        assert CODE_WRITER_PROMPT
        assert CODE_REVIEWER_PROMPT

    def test_existing_scans_preserved(self):
        content = (_SRC / "quality_checks.py").read_text(encoding="utf-8")
        assert "run_mock_data_scan" in content
        assert "run_ui_compliance_scan" in content
        assert "run_dual_orm_scan" in content
        assert "run_default_value_scan" in content
        assert "run_relationship_scan" in content

    def test_existing_config_fields_preserved(self):
        cfg = PostOrchestrationScanConfig()
        assert hasattr(cfg, "mock_data_scan")
        assert hasattr(cfg, "ui_compliance_scan")
        assert cfg.mock_data_scan is True
        assert cfg.ui_compliance_scan is True

    def test_existing_standards_preserved(self):
        assert FRONTEND_STANDARDS
        assert BACKEND_STANDARDS
        assert DATABASE_INTEGRITY_STANDARDS

    def test_scan_scope_still_works(self):
        scope = ScanScope(changed_files=[])
        assert scope.changed_files == []

    def test_violation_dataclass(self):
        v = Violation(
            check="TEST-001",
            message="test",
            file_path="test.py",
            line=1,
            severity="error",
        )
        assert v.check == "TEST-001"
        assert v.severity == "error"


# ============================================================
# Group 10: SvcContract dataclass
# ============================================================
class TestSvcContract:
    def test_fields(self):
        c = SvcContract(
            svc_id="SVC-001",
            frontend_service_method="Svc.get()",
            backend_endpoint="GET /api/items",
            http_method="GET",
            request_dto="-",
            response_dto="{ id: number }",
            request_fields={},
            response_fields={"id": "number"},
        )
        assert c.svc_id == "SVC-001"
        assert c.response_fields == {"id": "number"}

    def test_empty_fields(self):
        c = SvcContract(
            svc_id="SVC-002",
            frontend_service_method="",
            backend_endpoint="",
            http_method="",
            request_dto="",
            response_dto="",
            request_fields={},
            response_fields={},
        )
        assert c.request_fields == {}
        assert c.response_fields == {}

    def test_request_and_response(self):
        c = SvcContract(
            svc_id="SVC-003",
            frontend_service_method="AuthService.login()",
            backend_endpoint="POST /api/auth/login",
            http_method="POST",
            request_dto="{ email: string, password: string }",
            response_dto="{ token: string }",
            request_fields={"email": "string", "password": "string"},
            response_fields={"token": "string"},
        )
        assert len(c.request_fields) == 2
        assert c.response_fields["token"] == "string"


# ============================================================
# Group 11: Type compatibility checks
# ============================================================
class TestTypeCompatibility:
    """Test _check_type_compatibility behavior via run_api_contract_scan."""

    def test_complex_types_skipped(self, tmp_path):
        """Complex types (objects, arrays) should be skipped for API-003."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { items: Array<string>, nested: { x: number } } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs", "public class Ctrl { }")
        _make_file(tmp_path, "interfaces/iface.ts", "export interface Model { }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        # Complex types should not trigger API-003
        assert all("Array" not in v.message for v in api003)

    def test_enum_type_not_flagged(self, tmp_path):
        """'enum' type should not trigger API-003."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { status: enum } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs", "public class Ctrl { public int Status { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts", "export interface Model { status: number; }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        assert api003 == []

    def test_int_compatible_with_number(self, tmp_path):
        """'int' should be compatible with 'number' (no API-003)."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: int } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs", "public class Ctrl { public int Id { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts", "export interface Model { id: number; }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        assert api003 == []

    def test_bool_compatible_with_boolean(self, tmp_path):
        """'bool' should be compatible with 'boolean' (no API-003)."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { active: bool } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs", "public class Ctrl { public bool Active { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts", "export interface Model { active: boolean; }")
        violations = run_api_contract_scan(tmp_path)
        api003 = [v for v in violations if v.check == "API-003"]
        assert api003 == []


# ============================================================
# Group 12: PascalCase / camelCase matching
# ============================================================
class TestCaseMatching:
    """Test that PascalCase/camelCase matching works correctly."""

    def test_backend_pascal_matches_camel_schema(self, tmp_path):
        """C# PascalCase property should match camelCase schema field."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { firstName: string, lastName: string } |\n")
        # controllers/ = backend only
        _make_file(tmp_path, "controllers/UserController.cs",
            "public class UserController { public string FirstName { get; set; } public string LastName { get; set; } }")
        # interfaces/ = frontend only
        _make_file(tmp_path, "interfaces/user.ts",
            "export interface User { firstName: string; lastName: string; }")
        violations = run_api_contract_scan(tmp_path)
        api001 = [v for v in violations if v.check == "API-001"]
        assert api001 == [], f"Should not flag PascalCase match: {api001}"

    def test_backend_exact_camel_also_matches(self, tmp_path):
        """Backend file using exact camelCase (e.g., TypeScript backend) should also match."""
        _make_file(tmp_path, "REQUIREMENTS.md",
            "| SVC-001 | Svc.get() | GET /api/x | GET | - | { userId: number } |\n")
        # controllers/ matches backend pattern
        _make_file(tmp_path, "controllers/user.controller.ts",
            "const response = { userId: user.id };")
        # interfaces/ matches frontend pattern
        _make_file(tmp_path, "interfaces/user.ts",
            "export interface User { userId: number; }")
        violations = run_api_contract_scan(tmp_path)
        api001 = [v for v in violations if v.check == "API-001"]
        assert api001 == []
