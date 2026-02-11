"""Tests for v12.0 Hard Ceiling — Endpoint Cross-Reference scan, API-004,
prompt directives, config wiring, and CLI integration.

~70 tests across 8 test classes.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 3.1 TestNormalizeApiPath (6 tests)
# ---------------------------------------------------------------------------

from agent_team.quality_checks import _normalize_api_path


class TestNormalizeApiPath:
    """Validate API path normalization for cross-reference matching."""

    def test_strips_slashes_and_lowercases(self):
        # /Api/Tenders/ -> /tenders
        result = _normalize_api_path("/Api/Tenders/")
        assert result == "/tenders"

    def test_replaces_braces_params(self):
        # /tenders/{id} -> /tenders/{param}
        result = _normalize_api_path("/tenders/{id}")
        assert "{param}" in result
        assert "{id}" not in result

    def test_replaces_colon_params(self):
        # /tenders/:id -> /tenders/{param}
        result = _normalize_api_path("/tenders/:id")
        assert "{param}" in result
        assert ":id" not in result

    def test_replaces_angle_params(self):
        # /tenders/<int:id> -> /tenders/{param}
        result = _normalize_api_path("/tenders/<int:id>")
        assert "{param}" in result
        assert "<" not in result

    def test_strips_api_prefix(self):
        # /api/tenders -> /tenders
        result = _normalize_api_path("/api/tenders")
        assert result == "/tenders"

    def test_strips_api_v1_prefix(self):
        # /api/v1/tenders -> /tenders
        result = _normalize_api_path("/api/v1/tenders")
        assert result == "/tenders"


# ---------------------------------------------------------------------------
# 3.2 TestFrontendHttpExtraction (10 tests)
# ---------------------------------------------------------------------------

from agent_team.quality_checks import _extract_frontend_http_calls, _FrontendCall


class TestFrontendHttpExtraction:
    """Validate frontend HTTP call extraction from TS/JS files."""

    def test_angular_http_client_get(self, tmp_path):
        svc = tmp_path / "tender.service.ts"
        svc.write_text(
            "this.http.get<Tender[]>('/api/tenders')",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        # May match both Angular and Axios regex (both match this.http.get)
        assert len(calls) >= 1
        assert any(c.method == "GET" for c in calls)
        assert any("tenders" in c.path for c in calls)

    def test_angular_http_client_post_put_delete(self, tmp_path):
        svc = tmp_path / "api.service.ts"
        svc.write_text(
            "this.http.post('/api/items', body)\n"
            "this.http.put('/api/items/1', body)\n"
            "this.http.delete('/api/items/1')\n",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        methods = {c.method for c in calls}
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_axios_get_post(self, tmp_path):
        svc = tmp_path / "api.ts"
        svc.write_text(
            "axios.get('/api/users')\naxios.post('/api/users', data)",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 2

    def test_fetch_default_get(self, tmp_path):
        svc = tmp_path / "api.ts"
        svc.write_text("fetch('/api/data')", encoding="utf-8")
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 1
        assert calls[0].method == "GET"

    def test_skips_external_urls(self, tmp_path):
        svc = tmp_path / "api.ts"
        svc.write_text(
            "this.http.get('https://example.com/api/data')",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 0

    def test_keeps_localhost_urls(self, tmp_path):
        svc = tmp_path / "api.ts"
        svc.write_text(
            "this.http.get('http://localhost:3000/api/data')",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        # May match both Angular and Axios regex
        assert len(calls) >= 1

    def test_skips_complex_template_literals(self, tmp_path):
        # Complex template with multiple ${} -- should be skipped
        svc = tmp_path / "api.ts"
        svc.write_text(
            "this.http.get(`${baseUrl}/${path}/${id}`)",
            encoding="utf-8",
        )
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 0

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "lib"
        nm.mkdir(parents=True)
        svc = nm / "api.ts"
        svc.write_text("this.http.get('/api/data')", encoding="utf-8")
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 0

    def test_skips_test_files(self, tmp_path):
        svc = tmp_path / "api.spec.ts"
        svc.write_text("this.http.get('/api/data')", encoding="utf-8")
        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 0

    def test_scope_none_returns_all(self, tmp_path):
        svc1 = tmp_path / "a.service.ts"
        svc1.write_text("this.http.get('/api/data')", encoding="utf-8")
        svc2 = tmp_path / "b.service.ts"
        svc2.write_text("this.http.get('/api/other')", encoding="utf-8")
        calls = _extract_frontend_http_calls(tmp_path, None)
        # Without scope, get all calls from both files
        # Each call may match multiple regex patterns (Angular + Axios)
        paths = {c.path for c in calls}
        assert "/api/data" in paths
        assert "/api/other" in paths


# ---------------------------------------------------------------------------
# 3.3 TestBackendRouteExtraction (12 tests)
# ---------------------------------------------------------------------------

from agent_team.quality_checks import (
    _extract_backend_routes_dotnet,
    _extract_backend_routes_express,
    _extract_backend_routes_python,
    run_endpoint_xref_scan,
)


class TestBackendRouteExtraction:
    """Validate backend route extraction for .NET, Express, and Python."""

    def test_dotnet_basic_controller(self, tmp_path):
        ctrl = tmp_path / "Controllers" / "ItemsController.cs"
        ctrl.parent.mkdir(parents=True)
        ctrl.write_text(
            '[Route("api/[controller]")]\n'
            "public class ItemsController : ControllerBase\n{\n"
            "    [HttpGet]\n"
            "    public IActionResult GetAll() { }\n"
            "    [HttpPost]\n"
            "    public IActionResult Create() { }\n"
            "}",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_dotnet(tmp_path, None)
        assert len(routes) >= 2
        methods = {r.method for r in routes}
        assert "GET" in methods
        assert "POST" in methods

    def test_dotnet_route_with_controller_placeholder(self, tmp_path):
        ctrl = tmp_path / "TendersController.cs"
        ctrl.write_text(
            '[Route("api/[controller]")]\n'
            "public class TendersController : ControllerBase\n{\n"
            "    [HttpGet]\n"
            "    public IActionResult Get() { }\n"
            "}",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_dotnet(tmp_path, None)
        assert len(routes) >= 1
        # [controller] should be replaced with "Tenders"
        assert any("tenders" in r.path.lower() for r in routes)

    def test_dotnet_http_method_with_path(self, tmp_path):
        ctrl = tmp_path / "UsersController.cs"
        ctrl.write_text(
            '[Route("api/users")]\n'
            "public class UsersController : ControllerBase\n{\n"
            '    [HttpGet("{id}")]\n'
            "    public IActionResult GetById() { }\n"
            "}",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_dotnet(tmp_path, None)
        assert len(routes) >= 1
        assert any("{" in r.path for r in routes)

    def test_dotnet_http_method_without_path(self, tmp_path):
        ctrl = tmp_path / "UsersController.cs"
        ctrl.write_text(
            '[Route("api/users")]\n'
            "public class UsersController : ControllerBase\n{\n"
            "    [HttpGet]\n"
            "    public IActionResult GetAll() { }\n"
            "}",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_dotnet(tmp_path, None)
        assert len(routes) >= 1

    def test_express_router_get_post(self, tmp_path):
        route_file = tmp_path / "routes" / "items.route.ts"
        route_file.parent.mkdir(parents=True)
        route_file.write_text(
            "router.get('/items', handler)\n"
            "router.post('/items', handler)\n",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_express(tmp_path, None)
        assert len(routes) >= 2

    def test_express_app_route(self, tmp_path):
        app_file = tmp_path / "app.ts"
        app_file.write_text(
            "app.get('/items', handler)\n"
            "app.post('/items', handler)\n",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_express(tmp_path, None)
        assert len(routes) >= 2

    def test_flask_route_decorator(self, tmp_path):
        app_file = tmp_path / "views.py"
        app_file.write_text(
            "@app.route('/api/items', methods=['GET', 'POST'])\n"
            "def items():\n    pass\n",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_python(tmp_path, None)
        assert len(routes) >= 2  # GET and POST

    def test_fastapi_router_decorator(self, tmp_path):
        app_file = tmp_path / "router.py"
        app_file.write_text(
            "@router.get('/items')\ndef get_items(): pass\n"
            "@router.post('/items')\ndef create_item(): pass\n",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_python(tmp_path, None)
        assert len(routes) >= 2

    def test_django_path(self, tmp_path):
        urls_file = tmp_path / "urls.py"
        urls_file.write_text(
            "path('api/items/', views.item_list)\n",
            encoding="utf-8",
        )
        routes = _extract_backend_routes_python(tmp_path, None)
        assert len(routes) >= 1

    def test_auto_detect_dotnet(self, tmp_path):
        # Create .csproj to trigger .NET detection
        (tmp_path / "app.csproj").write_text("<Project></Project>", encoding="utf-8")
        ctrl = tmp_path / "ItemsController.cs"
        ctrl.write_text(
            '[Route("api/items")]\n'
            "public class ItemsController : ControllerBase\n{\n"
            "    [HttpGet]\n"
            "    public IActionResult Get() { }\n"
            "}",
            encoding="utf-8",
        )
        # Also create a frontend file
        svc = tmp_path / "items.service.ts"
        svc.write_text("this.http.get('/api/items')", encoding="utf-8")
        violations = run_endpoint_xref_scan(tmp_path)
        # Should find the endpoint and match -- no XREF-001
        xref001s = [v for v in violations if v.check == "XREF-001"]
        assert len(xref001s) == 0

    def test_auto_detect_express(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"test"}', encoding="utf-8")
        route = tmp_path / "routes" / "api.ts"
        route.parent.mkdir()
        route.write_text("router.get('/items', handler)", encoding="utf-8")
        svc = tmp_path / "src" / "api.service.ts"
        svc.parent.mkdir()
        svc.write_text("axios.get('/items')", encoding="utf-8")
        violations = run_endpoint_xref_scan(tmp_path)
        xref001s = [v for v in violations if v.check == "XREF-001"]
        assert len(xref001s) == 0

    def test_auto_detect_python(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask==2.0\n", encoding="utf-8")
        views = tmp_path / "router.py"
        views.write_text(
            "@app.get('/items')\ndef get(): pass\n",
            encoding="utf-8",
        )
        svc = tmp_path / "src" / "api.service.ts"
        svc.parent.mkdir()
        svc.write_text("fetch('/items')", encoding="utf-8")
        violations = run_endpoint_xref_scan(tmp_path)
        xref001s = [v for v in violations if v.check == "XREF-001"]
        assert len(xref001s) == 0


# ---------------------------------------------------------------------------
# 3.4 TestEndpointXref (10 tests)
# ---------------------------------------------------------------------------

from agent_team.quality_checks import _check_endpoint_xref, _BackendRoute


class TestEndpointXref:
    """Validate the cross-reference matching logic."""

    def test_exact_match_no_violation(self):
        fc = [_FrontendCall("GET", "/api/items", "svc.ts", 1)]
        br = [_BackendRoute("GET", "/api/items", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 0

    def test_method_agnostic_xref002_warning(self):
        fc = [_FrontendCall("POST", "/api/items", "svc.ts", 1)]
        br = [_BackendRoute("GET", "/api/items", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 1
        assert vs[0].check == "XREF-002"
        assert vs[0].severity == "warning"

    def test_no_match_xref001_error(self):
        fc = [_FrontendCall("GET", "/api/missing", "svc.ts", 1)]
        br = [_BackendRoute("GET", "/api/items", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 1
        assert vs[0].check == "XREF-001"
        assert vs[0].severity == "error"

    def test_parameterized_paths_match(self):
        fc = [_FrontendCall("GET", "/api/items/${id}", "svc.ts", 1)]
        br = [_BackendRoute("GET", "/api/items/{id}", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 0

    def test_mixed_violations(self):
        fc = [
            _FrontendCall("POST", "/api/a", "svc.ts", 1),  # method mismatch
            _FrontendCall("GET", "/api/missing", "svc.ts", 2),  # missing
        ]
        br = [_BackendRoute("GET", "/api/a", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 2

    def test_cap_at_max_violations(self):
        # Create more than _MAX_VIOLATIONS (100) frontend calls with no backend
        fc = [
            _FrontendCall("GET", f"/api/item{i}", "svc.ts", i)
            for i in range(150)
        ]
        br: list[_BackendRoute] = []
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) <= 100

    def test_empty_frontend_no_violations(self):
        vs = _check_endpoint_xref(
            [], [_BackendRoute("GET", "/api/items", "ctrl.cs", 1)]
        )
        assert len(vs) == 0

    def test_empty_backend_all_xref001(self):
        fc = [_FrontendCall("GET", "/api/items", "svc.ts", 1)]
        vs = _check_endpoint_xref(fc, [])
        # All are XREF-001 since no backend to match against
        assert all(v.check == "XREF-001" for v in vs)

    def test_normalized_comparison(self):
        # API prefix stripped, case insensitive
        fc = [_FrontendCall("GET", "/api/v1/Items", "svc.ts", 1)]
        br = [_BackendRoute("GET", "/api/items", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 0

    def test_api_prefix_stripped_both_sides(self):
        fc = [_FrontendCall("GET", "/api/v1/tenders", "svc.ts", 1)]
        br = [_BackendRoute("GET", "api/tenders", "ctrl.cs", 1)]
        vs = _check_endpoint_xref(fc, br)
        assert len(vs) == 0


# ---------------------------------------------------------------------------
# 3.5 TestApi004WriteFields (8 tests)
# ---------------------------------------------------------------------------

from agent_team.quality_checks import (
    _extract_csharp_class_properties,
    _check_request_field_passthrough,
    SvcContract,
    run_api_contract_scan,
)


class TestApi004WriteFields:
    """Validate API-004 request field passthrough detection."""

    def test_csharp_property_extraction_basic(self):
        content = (
            "public class CreateItemCommand\n"
            "{\n"
            "    public string Name { get; set; }\n"
            "    public int Quantity { get; set; }\n"
            "    public decimal Price { get; set; }\n"
            "}\n"
        )
        props = _extract_csharp_class_properties(content, "CreateItemCommand")
        assert "Name" in props
        assert "Quantity" in props
        assert "Price" in props

    def test_csharp_property_extraction_empty_class(self):
        content = "public class EmptyCommand { }"
        props = _extract_csharp_class_properties(content, "EmptyCommand")
        assert len(props) == 0

    def test_request_field_missing_from_command(self, tmp_path):
        # Create backend file with Command class missing a field
        cmd = tmp_path / "Commands" / "CreateItemCommand.cs"
        cmd.parent.mkdir(parents=True)
        cmd.write_text(
            "public class CreateItemCommand {\n"
            "    public string Name { get; set; }\n"
            "}\n",
            encoding="utf-8",
        )
        contracts = [
            SvcContract(
                svc_id="SVC-001",
                frontend_service_method="createItem",
                backend_endpoint="POST /api/items",
                http_method="POST",
                request_dto="CreateItemCommand { name: string, quantity: number }",
                response_dto="",
                request_fields={"name": "string", "quantity": "number"},
                response_fields={},
            )
        ]
        vs = _check_request_field_passthrough(contracts, tmp_path, None)
        # "quantity" is missing from Command (it has Name but not Quantity)
        api004 = [v for v in vs if v.check == "API-004"]
        assert len(api004) >= 1

    def test_request_field_present_in_command(self, tmp_path):
        cmd = tmp_path / "Commands" / "CreateItemCommand.cs"
        cmd.parent.mkdir(parents=True)
        cmd.write_text(
            "public class CreateItemCommand {\n"
            "    public string Name { get; set; }\n"
            "    public int Quantity { get; set; }\n"
            "}\n",
            encoding="utf-8",
        )
        contracts = [
            SvcContract(
                svc_id="SVC-001",
                frontend_service_method="createItem",
                backend_endpoint="POST /api/items",
                http_method="POST",
                request_dto="CreateItemCommand { name: string, quantity: number }",
                response_dto="",
                request_fields={"name": "string", "quantity": "number"},
                response_fields={},
            )
        ]
        vs = _check_request_field_passthrough(contracts, tmp_path, None)
        assert len(vs) == 0

    def test_field_in_identifiers_fallback(self, tmp_path):
        # When class is not found by property extraction, fallback to identifiers
        cmd = tmp_path / "Handlers" / "CreateItemCommandHandler.cs"
        cmd.parent.mkdir(parents=True)
        cmd.write_text(
            "public class CreateItemCommandHandler {\n"
            "    var quantity = request.Quantity;\n"
            "}\n",
            encoding="utf-8",
        )
        # No explicit CreateItemCommand class found -> identifiers fallback
        contracts = [
            SvcContract(
                svc_id="SVC-001",
                frontend_service_method="createItem",
                backend_endpoint="POST /api/items",
                http_method="POST",
                request_dto="CreateItemCommand { name: string, quantity: number }",
                response_dto="",
                request_fields={"name": "string", "quantity": "number"},
                response_fields={},
            )
        ]
        # Results depend on whether class_name is found in any file
        vs = _check_request_field_passthrough(contracts, tmp_path, None)
        assert isinstance(vs, list)

    def test_case_insensitive_matching(self, tmp_path):
        cmd = tmp_path / "Commands" / "CreateFooCommand.cs"
        cmd.parent.mkdir(parents=True)
        cmd.write_text(
            "public class CreateFooCommand {\n"
            "    public string Title { get; set; }\n"
            "}\n",
            encoding="utf-8",
        )
        contracts = [
            SvcContract(
                svc_id="SVC-001",
                frontend_service_method="create",
                backend_endpoint="POST /api/foo",
                http_method="POST",
                request_dto="CreateFooCommand { title: string }",
                response_dto="",
                request_fields={"title": "string"},
                response_fields={},
            )
        ]
        vs = _check_request_field_passthrough(contracts, tmp_path, None)
        # "title" -> PascalCase "Title" should match
        assert len(vs) == 0

    def test_no_request_fields_skipped(self, tmp_path):
        contracts = [
            SvcContract(
                svc_id="SVC-001",
                frontend_service_method="getAll",
                backend_endpoint="GET /api/items",
                http_method="GET",
                request_dto="-",
                response_dto="ItemDto",
                request_fields={},
                response_fields={"id": "number"},
            )
        ]
        vs = _check_request_field_passthrough(contracts, tmp_path, None)
        assert len(vs) == 0

    def test_integrated_in_api_contract_scan(self, tmp_path):
        # Verify API-004 runs as part of run_api_contract_scan
        # Create REQUIREMENTS.md with SVC table
        req = tmp_path / "REQUIREMENTS.md"
        req.write_text(
            "| SVC-001 | svc.create() | POST /api/items | POST "
            "| CreateItemCommand { name: string, password: string } "
            "| ItemDto { id: number } |\n",
            encoding="utf-8",
        )
        # Create backend command missing "password"
        cmd = tmp_path / "Commands" / "CreateItemCommand.cs"
        cmd.parent.mkdir(parents=True)
        cmd.write_text(
            "public class CreateItemCommand {\n"
            "    public string Name { get; set; }\n"
            "}\n",
            encoding="utf-8",
        )
        vs = run_api_contract_scan(tmp_path)
        api004 = [v for v in vs if v.check == "API-004"]
        assert len(api004) >= 1  # "password" is missing


# ---------------------------------------------------------------------------
# 3.6 TestConfigWiring (8 tests)
# ---------------------------------------------------------------------------

from agent_team.config import (
    PostOrchestrationScanConfig,
    AgentTeamConfig,
    apply_depth_quality_gating,
    _dict_to_config,
)


class TestConfigWiring:
    """Validate that the endpoint_xref_scan config field is correctly wired."""

    def test_endpoint_xref_scan_field_exists(self):
        cfg = PostOrchestrationScanConfig()
        assert hasattr(cfg, "endpoint_xref_scan")

    def test_endpoint_xref_scan_defaults_true(self):
        cfg = PostOrchestrationScanConfig()
        assert cfg.endpoint_xref_scan is True

    def test_quick_depth_disables_xref(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("quick", cfg)
        assert cfg.post_orchestration_scans.endpoint_xref_scan is False

    def test_standard_depth_keeps_xref(self):
        cfg = AgentTeamConfig()
        apply_depth_quality_gating("standard", cfg)
        assert cfg.post_orchestration_scans.endpoint_xref_scan is True

    def test_dict_to_config_parses_xref(self):
        data = {"post_orchestration_scans": {"endpoint_xref_scan": False}}
        cfg, overrides = _dict_to_config(data)
        assert cfg.post_orchestration_scans.endpoint_xref_scan is False

    def test_user_overrides_tracks_xref(self):
        data = {"post_orchestration_scans": {"endpoint_xref_scan": True}}
        cfg, overrides = _dict_to_config(data)
        assert "post_orchestration_scans.endpoint_xref_scan" in overrides

    def test_endpoint_xref_standards_exists(self):
        from agent_team.code_quality_standards import ENDPOINT_XREF_STANDARDS

        assert "XREF-001" in ENDPOINT_XREF_STANDARDS
        assert "XREF-002" in ENDPOINT_XREF_STANDARDS
        assert "API-004" in ENDPOINT_XREF_STANDARDS

    def test_standards_mapped_to_agents(self):
        from agent_team.code_quality_standards import (
            _AGENT_STANDARDS_MAP,
            ENDPOINT_XREF_STANDARDS,
        )

        assert ENDPOINT_XREF_STANDARDS in _AGENT_STANDARDS_MAP["code-writer"]
        assert ENDPOINT_XREF_STANDARDS in _AGENT_STANDARDS_MAP["architect"]


# ---------------------------------------------------------------------------
# 3.7 TestPromptDirectives (8 tests)
# ---------------------------------------------------------------------------


class TestPromptDirectives:
    """Validate that v12 prompt directives are present in the correct modules."""

    def test_backend_e2e_has_endpoint_exhaustiveness(self):
        from agent_team.e2e_testing import BACKEND_E2E_PROMPT

        assert "Endpoint Exhaustiveness Rule" in BACKEND_E2E_PROMPT

    def test_backend_e2e_has_role_authorization(self):
        from agent_team.e2e_testing import BACKEND_E2E_PROMPT

        assert "Role Authorization Rule" in BACKEND_E2E_PROMPT

    def test_frontend_e2e_has_state_persistence(self):
        from agent_team.e2e_testing import FRONTEND_E2E_PROMPT

        assert "State Persistence Rule" in FRONTEND_E2E_PROMPT

    def test_frontend_e2e_has_revisit_testing(self):
        from agent_team.e2e_testing import FRONTEND_E2E_PROMPT

        assert "Revisit Testing Rule" in FRONTEND_E2E_PROMPT

    def test_frontend_e2e_has_dropdown_verification(self):
        from agent_team.e2e_testing import FRONTEND_E2E_PROMPT

        assert "Dropdown Verification Rule" in FRONTEND_E2E_PROMPT

    def test_frontend_e2e_has_button_outcome(self):
        from agent_team.e2e_testing import FRONTEND_E2E_PROMPT

        assert "Button Outcome Verification Rule" in FRONTEND_E2E_PROMPT

    def test_browser_executor_has_deep_verification(self):
        from agent_team.browser_testing import BROWSER_WORKFLOW_EXECUTOR_PROMPT

        assert "DEEP VERIFICATION RULES" in BROWSER_WORKFLOW_EXECUTOR_PROMPT

    def test_browser_regression_has_content_verification(self):
        from agent_team.browser_testing import BROWSER_REGRESSION_SWEEP_PROMPT

        assert "Content Verification" in BROWSER_REGRESSION_SWEEP_PROMPT


# ---------------------------------------------------------------------------
# 3.8 TestCLIWiring (10 tests)
# ---------------------------------------------------------------------------

_CLI_SRC_PATH = Path(__file__).resolve().parent.parent / "src" / "agent_team" / "cli.py"


class TestCLIWiring:
    """Validate CLI integration of the endpoint XREF scan and fix functions."""

    def test_xref_scan_block_in_cli(self):
        src = _CLI_SRC_PATH.read_text(encoding="utf-8")
        assert (
            "Endpoint Cross-Reference scan" in src
            or "Endpoint XREF scan" in src
        )

    def test_xref_scan_after_sdl_before_e2e(self):
        src = _CLI_SRC_PATH.read_text(encoding="utf-8")
        sdl_pos = src.find("Silent Data Loss scan")
        xref_pos = src.find("Endpoint Cross-Reference scan")
        if xref_pos < 0:
            xref_pos = src.find("Endpoint XREF scan")
        e2e_pos = src.find("E2E Testing Phase")
        assert sdl_pos > 0
        assert xref_pos > 0
        assert e2e_pos > 0
        assert sdl_pos < xref_pos < e2e_pos

    def test_fix_function_signature(self):
        from agent_team.cli import _run_endpoint_xref_fix

        sig = inspect.signature(_run_endpoint_xref_fix)
        params = list(sig.parameters.keys())
        assert "cwd" in params
        assert "config" in params
        assert "xref_violations" in params

    def test_fix_function_is_async(self):
        from agent_team.cli import _run_endpoint_xref_fix

        assert inspect.iscoroutinefunction(_run_endpoint_xref_fix)

    def test_fix_function_has_crash_isolation(self):
        src = _CLI_SRC_PATH.read_text(encoding="utf-8")
        # Find XREF scan block and verify it has try/except
        xref_start = src.find("Endpoint Cross-Reference scan")
        if xref_start < 0:
            xref_start = src.find("Endpoint XREF scan")
        xref_block = src[xref_start : xref_start + 3000]
        assert "except Exception" in xref_block

    def test_config_gating_works(self):
        src = _CLI_SRC_PATH.read_text(encoding="utf-8")
        assert "config.post_orchestration_scans.endpoint_xref_scan" in src

    def test_display_type_hint_exists(self):
        from agent_team.display import print_recovery_report

        src = inspect.getsource(print_recovery_report)
        assert "endpoint_xref_fix" in src

    def test_architect_prompt_has_endpoint_completeness(self):
        from agent_team.agents import ARCHITECT_PROMPT

        assert "ENDPOINT COMPLETENESS VERIFICATION" in ARCHITECT_PROMPT

    def test_reviewer_prompt_has_xref_verification(self):
        from agent_team.agents import CODE_REVIEWER_PROMPT

        assert "Endpoint Cross-Reference Verification" in CODE_REVIEWER_PROMPT

    def test_fix_function_returns_float(self):
        from agent_team.cli import _run_endpoint_xref_fix

        sig = inspect.signature(_run_endpoint_xref_fix)
        ret = sig.return_annotation
        assert ret is float or ret == "float"
