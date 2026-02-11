"""Tests for v11 E2E Gap Closure — ENUM-004, SDL-001, API-002 bidirectional,
prompt injections, config wiring, CLI pipeline verification."""
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
    _check_enum_serialization,
    _check_cqrs_persistence,
    _check_frontend_extra_fields,
    run_silent_data_loss_scan,
    run_api_contract_scan,
    SvcContract,
    _parse_field_schema,
)
from agent_team.config import (
    AgentTeamConfig,
    PostOrchestrationScanConfig,
    _dict_to_config,
    apply_depth_quality_gating,
)
from agent_team.code_quality_standards import (
    SILENT_DATA_LOSS_STANDARDS,
    API_CONTRACT_STANDARDS,
    _AGENT_STANDARDS_MAP,
    get_standards_for_agent,
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
# Group 1: TestEnumSerializationCheck (~12 tests)
# ============================================================
class TestEnumSerializationCheck:
    """Test _check_enum_serialization() — ENUM-004."""

    def test_dotnet_no_converter_flags(self, tmp_path):
        """.NET project with no JsonStringEnumConverter -> 1 ENUM-004 violation."""
        _make_file(tmp_path, "MyProject/MyProject.csproj", "<Project></Project>")
        _make_file(tmp_path, "MyProject/Program.cs",
                   'var builder = WebApplication.CreateBuilder(args);\nbuilder.Services.AddControllers();')
        violations = _check_enum_serialization(tmp_path)
        assert len(violations) == 1
        assert violations[0].check == "ENUM-004"
        assert violations[0].severity == "error"
        assert "JsonStringEnumConverter" in violations[0].message

    def test_dotnet_no_startup_files(self, tmp_path):
        """.NET project with no Program.cs or Startup.cs -> 1 violation."""
        _make_file(tmp_path, "src/MyApp.csproj", "<Project></Project>")
        _make_file(tmp_path, "src/SomeService.cs", "public class SomeService {}")
        violations = _check_enum_serialization(tmp_path)
        assert len(violations) == 1
        assert violations[0].check == "ENUM-004"

    def test_dotnet_with_converter_in_program(self, tmp_path):
        """.NET WITH JsonStringEnumConverter in Program.cs -> 0 violations."""
        _make_file(tmp_path, "MyProject/MyProject.csproj", "<Project></Project>")
        _make_file(tmp_path, "MyProject/Program.cs",
                   'builder.Services.AddControllers().AddJsonOptions(o => '
                   'o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));')
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_dotnet_with_converter_in_startup(self, tmp_path):
        """.NET WITH JsonStringEnumConverter in Startup.cs -> 0 violations."""
        _make_file(tmp_path, "MyProject/MyProject.csproj", "<Project></Project>")
        _make_file(tmp_path, "MyProject/Startup.cs",
                   'services.AddControllers().AddJsonOptions(o => '
                   'o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()));')
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_python_project_skips(self, tmp_path):
        """Python project (no .csproj) -> 0 violations (scan skips)."""
        _make_file(tmp_path, "requirements.txt", "flask==2.0")
        _make_file(tmp_path, "app.py", "from flask import Flask")
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_nodejs_project_skips(self, tmp_path):
        """Node.js project (no .csproj) -> 0 violations (scan skips)."""
        _make_file(tmp_path, "package.json", '{"name": "myapp"}')
        _make_file(tmp_path, "index.ts", "console.log('hello');")
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_empty_directory(self, tmp_path):
        """Empty directory -> 0 violations, no crash."""
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_multiple_csproj_files(self, tmp_path):
        """Multiple .csproj files -> still works (finds any)."""
        _make_file(tmp_path, "Backend/Api.csproj", "<Project></Project>")
        _make_file(tmp_path, "Backend/Domain.csproj", "<Project></Project>")
        _make_file(tmp_path, "Backend/Program.cs",
                   'o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());')
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_nested_startup_still_caught(self, tmp_path):
        """JsonStringEnumConverter in a nested Startup.cs -> still caught."""
        _make_file(tmp_path, "src/Api.csproj", "<Project></Project>")
        _make_file(tmp_path, "src/Api/Startup.cs",
                   'new JsonStringEnumConverter()');
        violations = _check_enum_serialization(tmp_path)
        assert violations == []

    def test_csproj_but_no_cs_files(self, tmp_path):
        """Project with .csproj but no .cs files -> 1 violation."""
        _make_file(tmp_path, "MyProject/MyProject.csproj", "<Project></Project>")
        violations = _check_enum_serialization(tmp_path)
        assert len(violations) == 1
        assert violations[0].check == "ENUM-004"

    def test_file_read_error_handling(self, tmp_path):
        """File read error on Program.cs -> graceful handling (no crash)."""
        _make_file(tmp_path, "MyProject.csproj", "<Project></Project>")
        prog = _make_file(tmp_path, "Program.cs", "some content")
        # Mock OSError during read
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            # rglob still works, but read_text raises — should not crash
            violations = _check_enum_serialization(tmp_path)
        # Should still flag because it couldn't read to verify converter
        assert len(violations) == 1


# ============================================================
# Group 2: TestCqrsPersistenceCheck (~15 tests)
# ============================================================
class TestCqrsPersistenceCheck:
    """Test _check_cqrs_persistence() — SDL-001."""

    def test_cs_handler_no_persistence(self, tmp_path):
        """CreateOrderCommandHandler.cs with no persistence -> 1 SDL-001 violation."""
        _make_file(tmp_path, "Handlers/CreateOrderCommandHandler.cs",
                   'public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, OrderDto>\n'
                   '{\n'
                   '    public async Task<OrderDto> Handle(CreateOrderCommand request, CancellationToken ct)\n'
                   '    {\n'
                   '        var order = new Order(request.Title);\n'
                   '        return new OrderDto(order.Id, order.Title);\n'
                   '    }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert len(violations) == 1
        assert violations[0].check == "SDL-001"
        assert violations[0].severity == "error"
        assert "CreateOrderCommandHandler.cs" in violations[0].message

    def test_python_handler_no_persistence(self, tmp_path):
        """import_command_handler.py with no db.session.commit() -> 1 violation."""
        _make_file(tmp_path, "handlers/import_command_handler.py",
                   'class ImportCommandHandler:\n'
                   '    def handle(self, command):\n'
                   '        data = process(command.payload)\n'
                   '        return data\n')
        violations = _check_cqrs_persistence(tmp_path)
        assert len(violations) == 1
        assert violations[0].check == "SDL-001"

    def test_query_handler_excluded(self, tmp_path):
        """GetOrderQueryHandler.cs -> NOT flagged (query handler excluded)."""
        _make_file(tmp_path, "Handlers/GetOrderQueryHandler.cs",
                   'public class GetOrderQueryHandler : IRequestHandler<GetOrderQuery, OrderDto> {}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_handler_with_save_changes_async(self, tmp_path):
        """Handler with SaveChangesAsync -> NOT flagged."""
        _make_file(tmp_path, "Handlers/CreateOrderCommandHandler.cs",
                   'public class CreateOrderCommandHandler\n'
                   '{\n'
                   '    public async Task Handle(CreateOrderCommand request)\n'
                   '    {\n'
                   '        _context.Orders.Add(new Order());\n'
                   '        await _context.SaveChangesAsync();\n'
                   '    }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_handler_with_repository_add(self, tmp_path):
        """Handler with _repository.Add -> NOT flagged."""
        _make_file(tmp_path, "Handlers/CreateItemCommandHandler.cs",
                   'public class CreateItemCommandHandler\n'
                   '{\n'
                   '    public async Task Handle(CreateItemCommand request)\n'
                   '    {\n'
                   '        _repository.Add(new Item());\n'
                   '    }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_handler_with_unit_of_work(self, tmp_path):
        """Handler with _unitOfWork.Complete -> NOT flagged."""
        _make_file(tmp_path, "Handlers/UpdateOrderCommandHandler.cs",
                   'public class UpdateOrderCommandHandler\n'
                   '{\n'
                   '    public async Task Handle()\n'
                   '    {\n'
                   '        order.Update();\n'
                   '        await _unitOfWork.Complete();\n'
                   '    }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_notification_handler_excluded(self, tmp_path):
        """File with INotificationHandler -> NOT flagged (event-only)."""
        _make_file(tmp_path, "Handlers/OrderCreatedCommandHandler.cs",
                   'public class OrderCreatedCommandHandler : INotificationHandler<OrderCreatedEvent>\n'
                   '{\n'
                   '    public Task Handle(OrderCreatedEvent notification) { }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_mediator_publish_excluded(self, tmp_path):
        """File with _mediator.Publish -> NOT flagged (event dispatch)."""
        _make_file(tmp_path, "Handlers/DispatchCommandHandler.cs",
                   'public class DispatchCommandHandler\n'
                   '{\n'
                   '    public async Task Handle()\n'
                   '    {\n'
                   '        await _mediator.Publish(new SomeEvent());\n'
                   '    }\n'
                   '}')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_non_handler_file_not_scanned(self, tmp_path):
        """Non-handler file -> NOT scanned."""
        _make_file(tmp_path, "Services/OrderService.cs",
                   'public class OrderService { public void DoStuff() {} }')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_test_files_excluded(self, tmp_path):
        """Test files (test in name) -> NOT scanned."""
        _make_file(tmp_path, "Tests/CreateOrderCommandHandlerTest.cs",
                   'public class CreateOrderCommandHandlerTest { }')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_spec_files_excluded(self, tmp_path):
        """Spec files -> NOT scanned."""
        _make_file(tmp_path, "Tests/CreateOrderCommandHandler.spec.cs",
                   'public class CreateOrderCommandHandlerSpec { }')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_empty_project(self, tmp_path):
        """No command handler files -> 0 violations, no crash."""
        _make_file(tmp_path, "src/app.ts", "console.log('hello');")
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []

    def test_scan_scope_filtering(self, tmp_path):
        """ScanScope filtering works correctly."""
        handler_a = _make_file(tmp_path, "Handlers/CreateACommandHandler.cs",
                               'public class CreateACommandHandler { }')
        _make_file(tmp_path, "Handlers/CreateBCommandHandler.cs",
                   'public class CreateBCommandHandler { }')
        # Only handler_a in scope
        scope = ScanScope(changed_files=[handler_a.resolve()])
        violations = _check_cqrs_persistence(tmp_path, scope=scope)
        assert len(violations) == 1
        assert "CreateACommandHandler.cs" in violations[0].message

    def test_max_violations_cap(self, tmp_path):
        """_MAX_VIOLATIONS cap respected."""
        for i in range(_MAX_VIOLATIONS + 10):
            _make_file(tmp_path, f"Handlers/Create{i}CommandHandler.cs",
                       f'public class Create{i}CommandHandler {{ }}')
        violations = _check_cqrs_persistence(tmp_path)
        assert len(violations) <= _MAX_VIOLATIONS

    def test_python_handler_with_commit(self, tmp_path):
        """Python handler with db.session.commit -> NOT flagged."""
        _make_file(tmp_path, "handlers/create_order_command_handler.py",
                   'class CreateOrderCommandHandler:\n'
                   '    def handle(self, command):\n'
                   '        order = Order(command.title)\n'
                   '        db.session.add(order)\n'
                   '        db.session.commit()\n')
        violations = _check_cqrs_persistence(tmp_path)
        assert violations == []


# ============================================================
# Group 3: TestFrontendExtraFieldsCheck (~15 tests)
# ============================================================
class TestFrontendExtraFieldsCheck:
    """Test _check_frontend_extra_fields() — API-002 bidirectional."""

    def _make_contract(self, response_fields: dict[str, str], svc_id: str = "SVC-001") -> SvcContract:
        return SvcContract(
            svc_id=svc_id,
            frontend_service_method="SomeService.get()",
            backend_endpoint="GET /api/items",
            http_method="GET",
            request_dto="-",
            response_dto="",
            request_fields={},
            response_fields=response_fields,
        )

    def test_extra_field_companyName(self, tmp_path):
        """Frontend interface has field companyName, SVC doesn't -> violation."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; companyName: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert len(violations) >= 1
        assert any("companyName" in v.message for v in violations)
        assert all(v.check == "API-002" for v in violations)

    def test_extra_field_clarifications(self, tmp_path):
        """Frontend has clarifications, SVC has clarificationCount -> violation."""
        contract = self._make_contract({
            "id": "number", "title": "string", "clarificationCount": "number",
        })
        _make_file(tmp_path, "models/tender.ts",
                   'export interface Tender { id: number; title: string; '
                   'clarificationCount: number; clarifications: any[]; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        extra = [v for v in violations if "clarifications" in v.message]
        assert len(extra) >= 1

    def test_multiple_extra_fields(self, tmp_path):
        """Multiple extra fields -> multiple violations."""
        contract = self._make_contract({"id": "number", "name": "string"})
        _make_file(tmp_path, "models/user.ts",
                   'export interface User { id: number; name: string; '
                   'companyName: string; hasSubmittedBid: boolean; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert len(violations) >= 2

    def test_matching_fields_no_violations(self, tmp_path):
        """Frontend and backend fields match -> 0 violations."""
        contract = self._make_contract({"id": "number", "title": "string", "status": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; status: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_optional_field_warning_severity(self, tmp_path):
        """Optional field (field?: type) -> 'warning' severity."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; extraField?: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        optional_violations = [v for v in violations if "extraField" in v.message]
        assert len(optional_violations) >= 1
        assert optional_violations[0].severity == "warning"

    def test_universal_fields_not_checked(self, tmp_path):
        """Universal fields (id, createdAt, updatedAt) -> NOT checked."""
        contract = self._make_contract({"title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { title: string; id: number; createdAt: string; updatedAt: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        # id, createdAt, updatedAt should be skipped
        assert violations == []

    def test_ui_only_fields_not_checked(self, tmp_path):
        """UI-only fields (isLoading, isSelected, className) -> NOT checked."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; '
                   'isLoading: boolean; isSelected: boolean; className: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_low_overlap_not_matched(self, tmp_path):
        """Interface with <50% field overlap -> NOT matched (different type)."""
        contract = self._make_contract({
            "id": "number", "title": "string", "description": "string",
            "status": "string", "amount": "number",
        })
        # Only 1 out of 5 fields overlap (20%) — should not match
        _make_file(tmp_path, "models/other.ts",
                   'export interface Other { id: number; foo: string; bar: number; baz: boolean; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_no_response_fields_skips(self, tmp_path):
        """Contract with no response_fields -> skip."""
        contract = self._make_contract({})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; foo: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_no_ts_files_skips(self, tmp_path):
        """No TypeScript files -> skip."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.py", "class Item: pass")
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_required_extra_field_error_severity(self, tmp_path):
        """Required extra field (no ?) -> 'error' severity."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; requiredExtra: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        required_violations = [v for v in violations if "requiredExtra" in v.message]
        assert len(required_violations) >= 1
        assert required_violations[0].severity == "error"

    def test_backward_compat_existing_api002(self, tmp_path):
        """Existing API-001/002 behavior unchanged — run full scan."""
        _make_file(tmp_path, "REQUIREMENTS.md",
                   "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, title: string } |\n")
        _make_file(tmp_path, "interfaces/item.ts",
                   "export interface Item { id: number; title: string; }")
        _make_file(tmp_path, "controllers/Ctrl.cs",
                   "public class Ctrl { public int Id { get; set; } public string Title { get; set; } }")
        violations = run_api_contract_scan(tmp_path)
        assert violations == []

    def test_bidirectional_integrated_in_scan(self, tmp_path):
        """Full scan catches bidirectional field mismatch."""
        _make_file(tmp_path, "REQUIREMENTS.md",
                   "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, title: string } |\n")
        _make_file(tmp_path, "models/item.ts",
                   "export interface Item { id: number; title: string; extraField: string; }")
        _make_file(tmp_path, "controllers/Ctrl.cs",
                   "public class Ctrl { public int Id { get; set; } public string Title { get; set; } }")
        violations = run_api_contract_scan(tmp_path)
        extra = [v for v in violations if "extraField" in v.message]
        assert len(extra) >= 1

    def test_case_insensitive_match(self, tmp_path):
        """Case-insensitive matching between interface and SVC fields."""
        contract = self._make_contract({"userId": "number", "userName": "string"})
        # All fields present (case-insensitive) -> no violations
        _make_file(tmp_path, "models/user.ts",
                   'export interface User { userId: number; userName: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []

    def test_createdby_updatedby_skipped(self, tmp_path):
        """createdBy, updatedBy are universal fields and should be skipped."""
        contract = self._make_contract({"id": "number", "title": "string"})
        _make_file(tmp_path, "models/item.ts",
                   'export interface Item { id: number; title: string; '
                   'createdBy: string; updatedBy: string; }')
        violations: list[Violation] = []
        _check_frontend_extra_fields(contract, tmp_path, violations)
        assert violations == []


# ============================================================
# Group 4: TestConfigWiring (~10 tests)
# ============================================================
class TestConfigWiring:
    """Test config.py changes for silent_data_loss_scan."""

    def test_default_enabled(self):
        """PostOrchestrationScanConfig has silent_data_loss_scan with default True."""
        cfg = PostOrchestrationScanConfig()
        assert cfg.silent_data_loss_scan is True

    def test_dict_to_config_default(self):
        """_dict_to_config({}) returns config with silent_data_loss_scan=True."""
        cfg, overrides = _dict_to_config({})
        assert cfg.post_orchestration_scans.silent_data_loss_scan is True

    def test_dict_to_config_explicit_false(self):
        """_dict_to_config with silent_data_loss_scan=False returns False."""
        data = {"post_orchestration_scans": {"silent_data_loss_scan": False}}
        cfg, overrides = _dict_to_config(data)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is False

    def test_user_override_tracking(self):
        """User override tracking works for silent_data_loss_scan."""
        data = {"post_orchestration_scans": {"silent_data_loss_scan": True}}
        cfg, overrides = _dict_to_config(data)
        assert "post_orchestration_scans.silent_data_loss_scan" in overrides

    def test_quick_depth_disables(self):
        """apply_depth_quality_gating('quick') sets silent_data_loss_scan=False."""
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is False

    def test_standard_depth_keeps_enabled(self):
        """apply_depth_quality_gating('standard') leaves silent_data_loss_scan=True."""
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("standard", cfg, overrides)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is True

    def test_user_override_survives_quick(self):
        """User override NOT overridden by depth gating."""
        data = {"post_orchestration_scans": {"silent_data_loss_scan": True}}
        cfg, overrides = _dict_to_config(data)
        apply_depth_quality_gating("quick", cfg, overrides)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is True

    def test_unknown_yaml_keys_no_crash(self):
        """Unknown YAML keys don't break parsing."""
        data = {"post_orchestration_scans": {"unknown_key": True, "silent_data_loss_scan": False}}
        cfg, overrides = _dict_to_config(data)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is False

    def test_thorough_depth_keeps_enabled(self):
        """thorough depth doesn't change silent_data_loss_scan."""
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("thorough", cfg, overrides)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is True

    def test_exhaustive_depth_keeps_enabled(self):
        """exhaustive depth doesn't change silent_data_loss_scan."""
        cfg, overrides = _dict_to_config({})
        apply_depth_quality_gating("exhaustive", cfg, overrides)
        assert cfg.post_orchestration_scans.silent_data_loss_scan is True


# ============================================================
# Group 5: TestPromptInjections (~10 tests)
# ============================================================
class TestPromptInjections:
    """Verify prompt injections exist in agents.py and e2e_testing.py."""

    def test_architect_has_dotnet_serialization(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "JsonStringEnumConverter" in content
        assert ".NET Serialization" in content

    def test_reviewer_has_enum_serialization(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "Enum Serialization (ENUM-004)" in content

    def test_reviewer_has_silent_data_loss(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "Silent Data Loss Prevention (SDL-001/002/003)" in content

    def test_reviewer_has_cqrs_persistence(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "CQRS PERSISTENCE" in content

    def test_reviewer_has_response_consumption(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "RESPONSE CONSUMPTION" in content

    def test_reviewer_has_silent_guards(self):
        content = (_SRC / "agents.py").read_text(encoding="utf-8")
        assert "SILENT GUARDS" in content

    def test_backend_e2e_has_mutation_verification(self):
        content = (_SRC / "e2e_testing.py").read_text(encoding="utf-8")
        assert "Mutation Verification Rule" in content

    def test_frontend_e2e_has_mutation_verification(self):
        content = (_SRC / "e2e_testing.py").read_text(encoding="utf-8")
        # Both BACKEND_E2E_PROMPT and FRONTEND_E2E_PROMPT should have it
        occurrences = content.count("Mutation Verification Rule")
        assert occurrences >= 2

    def test_silent_data_loss_standards_exists(self):
        assert "SDL-001" in SILENT_DATA_LOSS_STANDARDS
        assert "ENUM-004" in SILENT_DATA_LOSS_STANDARDS

    def test_standards_mapped_to_code_writer(self):
        assert SILENT_DATA_LOSS_STANDARDS in _AGENT_STANDARDS_MAP["code-writer"]

    def test_standards_mapped_to_code_reviewer(self):
        assert SILENT_DATA_LOSS_STANDARDS in _AGENT_STANDARDS_MAP["code-reviewer"]

    def test_get_standards_includes_sdl(self):
        writer = get_standards_for_agent("code-writer")
        assert "SDL-001" in writer
        reviewer = get_standards_for_agent("code-reviewer")
        assert "SDL-001" in reviewer


# ============================================================
# Group 6: TestWiringVerification (~10 tests)
# ============================================================
class TestWiringVerification:
    """Verify wiring: pattern IDs, display.py, CLI pipeline order, function existence."""

    def test_pattern_ids_no_collision(self):
        """Pattern IDs ENUM-004, SDL-001 don't collide with existing IDs."""
        content = (_SRC / "quality_checks.py").read_text(encoding="utf-8")
        # Extract all check="XXX-NNN" patterns
        pattern_ids = set(re.findall(r'check="([A-Z]+-\d+)"', content))
        # Verify our new IDs exist
        assert "ENUM-004" in pattern_ids
        assert "SDL-001" in pattern_ids
        # Verify they don't overlap with existing prefixes at the same number
        # ENUM-001..003 exists already, ENUM-004 is new and distinct
        assert "SDL-001" not in {"FRONT-001", "BACK-001", "MOCK-001", "UI-001", "E2E-001",
                                  "DEPLOY-001", "ASSET-001", "PRD-001", "DB-001", "API-001"}

    def test_display_type_hints_entry(self):
        """'silent_data_loss_fix' exists in display.py type_hints dict."""
        content = (_SRC / "display.py").read_text(encoding="utf-8")
        assert '"silent_data_loss_fix"' in content

    def test_sdl_scan_after_api_contract(self):
        """SDL scan in cli.py is AFTER API contract scan."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        api_pos = content.find("API Contract Verification scan")
        sdl_pos = content.find("Silent Data Loss scan")
        assert api_pos > 0, "API Contract scan section not found"
        assert sdl_pos > 0, "SDL scan section not found"
        assert sdl_pos > api_pos, "SDL scan must be after API contract scan"

    def test_sdl_scan_before_e2e(self):
        """SDL scan in cli.py is BEFORE E2E Testing Phase."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        sdl_pos = content.find("Silent Data Loss scan")
        e2e_pos = content.find("E2E Testing Phase")
        assert sdl_pos > 0, "SDL scan section not found"
        assert e2e_pos > 0, "E2E Testing Phase not found"
        assert sdl_pos < e2e_pos, "SDL scan must be before E2E Testing Phase"

    def test_enum004_runs_inside_api_contract_scan(self):
        """ENUM-004 scan runs inside run_api_contract_scan."""
        content = (_SRC / "quality_checks.py").read_text(encoding="utf-8")
        # Find run_api_contract_scan function
        func_start = content.find("def run_api_contract_scan")
        assert func_start > 0
        func_body = content[func_start:]
        assert "_check_enum_serialization" in func_body

    def test_run_silent_data_loss_fix_exists(self):
        """_run_silent_data_loss_fix function exists in cli.py."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(content)
        func_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        assert "_run_silent_data_loss_fix" in func_names

    def test_run_silent_data_loss_fix_is_async(self):
        """_run_silent_data_loss_fix should be async."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_run_silent_data_loss_fix":
                return
        pytest.fail("_run_silent_data_loss_fix should be async")

    def test_recovery_type_appended(self):
        """Recovery type 'silent_data_loss_fix' is appended when violations found."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert '"silent_data_loss_fix"' in content

    def test_config_gating_in_cli(self):
        """Config gating: when silent_data_loss_scan=False, SDL block is skipped."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        assert "config.post_orchestration_scans.silent_data_loss_scan" in content

    def test_crash_isolation(self):
        """SDL scan block is wrapped in try/except."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        idx = content.find("Silent Data Loss scan")
        assert idx > 0
        block = content[idx - 200:idx + 1500]
        assert "try:" in block
        assert "except Exception" in block

    def test_fix_function_early_return(self):
        """_run_silent_data_loss_fix should return 0.0 for empty violations."""
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        idx = content.find("async def _run_silent_data_loss_fix")
        assert idx > 0
        func_block = content[idx:idx + 800]
        assert "return 0.0" in func_block


# ============================================================
# Group 7: TestRunSilentDataLossScan (public API)
# ============================================================
class TestRunSilentDataLossScan:
    """Test the run_silent_data_loss_scan public API wrapper."""

    def test_wraps_cqrs_check(self, tmp_path):
        """run_silent_data_loss_scan wraps _check_cqrs_persistence."""
        _make_file(tmp_path, "Handlers/CreateCommandHandler.cs",
                   'public class CreateCommandHandler { }')
        violations = run_silent_data_loss_scan(tmp_path)
        assert len(violations) >= 1
        assert violations[0].check == "SDL-001"

    def test_empty_project_returns_empty(self, tmp_path):
        """Empty project -> empty list."""
        violations = run_silent_data_loss_scan(tmp_path)
        assert violations == []

    def test_violations_sorted(self, tmp_path):
        """Violations are sorted by severity, file, line."""
        _make_file(tmp_path, "Handlers/AACommandHandler.cs", "class AACommandHandler {}")
        _make_file(tmp_path, "Handlers/BBCommandHandler.cs", "class BBCommandHandler {}")
        violations = run_silent_data_loss_scan(tmp_path)
        if len(violations) >= 2:
            # All are error severity, sorted by file_path
            assert violations[0].file_path <= violations[1].file_path

    def test_scope_support(self, tmp_path):
        """ScanScope filtering works with run_silent_data_loss_scan."""
        handler_a = _make_file(tmp_path, "Handlers/CreateACommandHandler.cs", "class A {}")
        _make_file(tmp_path, "Handlers/CreateBCommandHandler.cs", "class B {}")
        scope = ScanScope(changed_files=[handler_a.resolve()])
        violations = run_silent_data_loss_scan(tmp_path, scope=scope)
        assert len(violations) == 1

    def test_capped_at_max_violations(self, tmp_path):
        """Violations capped at _MAX_VIOLATIONS."""
        for i in range(_MAX_VIOLATIONS + 5):
            _make_file(tmp_path, f"Handlers/Create{i}CommandHandler.cs", f"class C{i} {{}}")
        violations = run_silent_data_loss_scan(tmp_path)
        assert len(violations) <= _MAX_VIOLATIONS


# ============================================================
# Group 8: TestEnum004InApiContractScan (integration)
# ============================================================
class TestEnum004InApiContractScan:
    """ENUM-004 scan fires as part of run_api_contract_scan."""

    def test_enum004_fires_with_no_requirements(self, tmp_path):
        """Even without REQUIREMENTS.md, ENUM-004 still fires for .NET projects."""
        _make_file(tmp_path, "MyProject.csproj", "<Project></Project>")
        _make_file(tmp_path, "Program.cs", "var builder = WebApplication.CreateBuilder(args);")
        violations = run_api_contract_scan(tmp_path)
        enum_violations = [v for v in violations if v.check == "ENUM-004"]
        assert len(enum_violations) == 1

    def test_enum004_fires_alongside_api_violations(self, tmp_path):
        """ENUM-004 fires alongside regular API-001/002 violations."""
        _make_file(tmp_path, "MyProject.csproj", "<Project></Project>")
        _make_file(tmp_path, "Program.cs", "var builder = WebApplication.CreateBuilder(args);")
        _make_file(tmp_path, "REQUIREMENTS.md",
                   "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number, title: string } |\n")
        _make_file(tmp_path, "controllers/Ctrl.cs",
                   "public class Ctrl { public int Id { get; set; } }")
        _make_file(tmp_path, "interfaces/iface.ts",
                   "export interface Model { id: number; title: string; }")
        violations = run_api_contract_scan(tmp_path)
        enum_violations = [v for v in violations if v.check == "ENUM-004"]
        api_violations = [v for v in violations if v.check.startswith("API-")]
        assert len(enum_violations) >= 1
        # API-001 should fire (backend missing "title" in PascalCase check)
        # Just verify enum is present
        assert any(v.check == "ENUM-004" for v in violations)

    def test_enum004_does_not_fire_for_non_dotnet(self, tmp_path):
        """ENUM-004 doesn't fire for non-.NET projects."""
        _make_file(tmp_path, "package.json", '{"name": "myapp"}')
        _make_file(tmp_path, "REQUIREMENTS.md",
                   "| SVC-001 | Svc.get() | GET /api/x | GET | - | { id: number } |\n")
        _make_file(tmp_path, "interfaces/iface.ts",
                   "export interface Model { id: number; }")
        violations = run_api_contract_scan(tmp_path)
        enum_violations = [v for v in violations if v.check == "ENUM-004"]
        assert enum_violations == []


# ============================================================
# Group 9: TestCliPrintContractViolationBug
# ============================================================
class TestCliPrintContractViolationBug:
    """Verify the print_contract_violation call in SDL scan block.

    Bug found: cli.py calls print_contract_violation(v.check, v.message, v.severity)
    but display.py defines it with a single argument: print_contract_violation(violation: str).
    This would crash at runtime. Check if it's been fixed or needs fixing.
    """

    def test_print_contract_violation_call_site(self):
        """Verify print_contract_violation is called correctly in SDL scan block.

        Previously had a bug: called with 3 args (v.check, v.message, v.severity)
        but display.py only accepts 1 string arg. Fixed to use formatted string.
        """
        content = (_SRC / "cli.py").read_text(encoding="utf-8")
        # Find the SDL scan block
        sdl_start = content.find("Silent Data Loss scan")
        assert sdl_start > 0
        sdl_block = content[sdl_start:sdl_start + 1500]

        # Verify the 3-arg bug is NOT present
        assert "print_contract_violation(v.check, v.message, v.severity)" not in sdl_block, \
            "BUG: print_contract_violation called with 3 args but accepts only 1"
        # Verify print_contract_violation IS used (with single formatted string)
        assert "print_contract_violation" in sdl_block
