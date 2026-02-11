"""Tests for XREF function-call URL filter (severity demotion).

Function-call URLs like ``${this.importUrl(tenderId, bidId)}/parse`` cannot
be resolved statically.  These are demoted to ``info`` severity so they
don't trigger expensive fix passes in the pipeline.

Covers:
- _has_function_call_url detection
- _check_endpoint_xref severity demotion for function-call URLs
- Integration: run_endpoint_xref_scan with mixed real + function-call violations
- CLI severity filter behavior (actionable vs info-only)
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_team.quality_checks import (
    _has_function_call_url,
    _check_endpoint_xref,
    _normalize_api_path,
    _extract_frontend_http_calls,
    run_endpoint_xref_scan,
)


# ============================================================
# Helpers
# ============================================================
def _make_file(tmp_path: Path, rel: str, content: str) -> Path:
    """Create a file at tmp_path/rel with the given content."""
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ============================================================
# _has_function_call_url detection
# ============================================================
class TestHasFunctionCallUrl:
    """Test the function-call URL detection regex."""

    def test_simple_function_call(self):
        assert _has_function_call_url("${this.importUrl(tenderId, bidId)}/parse")

    def test_single_arg(self):
        assert _has_function_call_url("${this.getUrl(id)}/items")

    def test_no_args(self):
        assert _has_function_call_url("${this.baseUrl()}/action")

    def test_self_prefix(self):
        assert _has_function_call_url("${self.endpoint(pk)}/detail")

    def test_nested_in_path(self):
        assert _has_function_call_url("/api/${this.func(x)}/suffix")

    def test_field_access_no_call(self):
        """Field access like ${this.apiUrl} is NOT a function call."""
        assert not _has_function_call_url("${this.apiUrl}/login")

    def test_environment_variable(self):
        assert not _has_function_call_url("${environment.apiUrl}/tasks")

    def test_plain_path(self):
        assert not _has_function_call_url("/api/tasks")

    def test_param_interpolation(self):
        assert not _has_function_call_url("/api/tasks/${id}")

    def test_complex_args(self):
        assert _has_function_call_url("${this.buildUrl(request.tenderId, request.bidId)}/execute")


# ============================================================
# _check_endpoint_xref severity demotion
# ============================================================
class TestCheckEndpointXrefFunctionCallDemotion:
    """Verify that function-call URLs get info severity."""

    def _make_call(self, method, path, file_path="svc.ts", line=1):
        from agent_team.quality_checks import _FrontendCall
        return _FrontendCall(method=method, path=path, file_path=file_path, line=line)

    def _make_route(self, method, path, file_path="ctrl.cs", line=1):
        from agent_team.quality_checks import _BackendRoute
        return _BackendRoute(method=method, path=path, file_path=file_path, line=line)

    def test_function_call_xref001_demoted_to_info(self):
        """XREF-001 for function-call URL should be info, not error."""
        calls = [self._make_call("POST", "${this.importUrl(tid, bid)}/parse")]
        routes = [self._make_route("GET", "/api/unrelated")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert violations[0].check == "XREF-001"
        assert violations[0].severity == "info"

    def test_regular_xref001_stays_error(self):
        """XREF-001 for regular URL should be error."""
        calls = [self._make_call("GET", "/api/missing-endpoint")]
        routes = [self._make_route("GET", "/api/other")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert violations[0].check == "XREF-001"
        assert violations[0].severity == "error"

    def test_function_call_xref002_demoted_to_info(self):
        """XREF-002 for function-call URL should be info, not warning."""
        # Path matches but method doesn't
        calls = [self._make_call("DELETE", "${this.getUrl(id)}/items")]
        routes = [self._make_route("GET", "/items")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert violations[0].check == "XREF-002"
        assert violations[0].severity == "info"

    def test_regular_xref002_stays_warning(self):
        """XREF-002 for regular URL should be warning."""
        calls = [self._make_call("DELETE", "/api/items/${id}")]
        routes = [self._make_route("GET", "/api/items/{id}")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert violations[0].check == "XREF-002"
        assert violations[0].severity == "warning"

    def test_mixed_violations_correct_severities(self):
        """Mix of function-call and regular URLs should have correct severities."""
        calls = [
            self._make_call("POST", "${this.base(id)}/action", line=1),
            self._make_call("GET", "/api/real-missing", line=2),
            self._make_call("DELETE", "/api/items/${id}", line=3),
        ]
        routes = [
            self._make_route("GET", "/api/items/{id}"),
        ]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 3

        by_line = {v.line: v for v in violations}
        assert by_line[1].severity == "info"      # function-call → info
        assert by_line[2].severity == "error"      # regular missing → error
        assert by_line[3].severity == "warning"    # method mismatch → warning

    def test_function_call_message_includes_annotation(self):
        """Function-call XREF-001 should note 'unresolvable function-call URL'."""
        calls = [self._make_call("POST", "${this.fn(x)}/path")]
        routes = [self._make_route("GET", "/api/other")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert "unresolvable function-call URL" in violations[0].message

    def test_regular_message_no_annotation(self):
        """Regular XREF-001 should NOT mention function-call."""
        calls = [self._make_call("GET", "/api/missing")]
        routes = [self._make_route("GET", "/api/other")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 1
        assert "unresolvable function-call URL" not in violations[0].message

    def test_function_call_exact_match_no_violation(self):
        """Function-call URL that happens to match should produce no violation."""
        calls = [self._make_call("GET", "${this.fn(id)}/items")]
        routes = [self._make_route("GET", "/items")]
        violations = _check_endpoint_xref(calls, routes)
        assert len(violations) == 0


# ============================================================
# Integration: run_endpoint_xref_scan with function-call URLs
# ============================================================
class TestXrefScanFunctionCallIntegration:
    """End-to-end test with Angular service using function-call URLs."""

    def test_function_call_urls_demoted(self, tmp_path: Path):
        """Function-call URLs in Angular service get info severity."""
        _make_file(tmp_path, "frontend/src/svc.ts", """\
            import { HttpClient } from '@angular/common/http';

            export class EvalService {
                constructor(private http: HttpClient) {}

                private evalUrl(tenderId: string): string {
                    return `/api/tenders/${tenderId}/evaluation`;
                }

                getSetup(tenderId: string) {
                    return this.http.get<any>(`${this.evalUrl(tenderId)}/setup`);
                }

                getPanelists(tenderId: string) {
                    return this.http.get<any>(`${this.evalUrl(tenderId)}/panelists`);
                }
            }
        """)
        # Backend with NO matching eval endpoints
        _make_file(tmp_path, "backend/Controllers/TestController.cs", """\
            using Microsoft.AspNetCore.Mvc;

            [Route("api/[controller]")]
            [ApiController]
            public class TestController : ControllerBase
            {
                [HttpGet]
                public IActionResult Get() => Ok();
            }
        """)

        violations = run_endpoint_xref_scan(tmp_path, scope=None)
        assert len(violations) == 2
        assert all(v.severity == "info" for v in violations)
        assert all(v.check == "XREF-001" for v in violations)

    def test_mixed_real_and_function_call(self, tmp_path: Path):
        """Mix of real missing endpoints and function-call URLs."""
        _make_file(tmp_path, "frontend/src/svc.ts", """\
            import { HttpClient } from '@angular/common/http';

            export class MixedService {
                constructor(private http: HttpClient) {}

                private basePath(id: string): string {
                    return `/api/items/${id}`;
                }

                // Function-call URL (should be info)
                getData(id: string) {
                    return this.http.get<any>(`${this.basePath(id)}/data`);
                }

                // Regular URL (should be error)
                getMissing() {
                    return this.http.get<any>('/api/totally-missing');
                }
            }
        """)
        _make_file(tmp_path, "backend/Controllers/ItemsController.cs", """\
            using Microsoft.AspNetCore.Mvc;

            [Route("api/[controller]")]
            [ApiController]
            public class ItemsController : ControllerBase
            {
                [HttpGet]
                public IActionResult GetAll() => Ok();
            }
        """)

        violations = run_endpoint_xref_scan(tmp_path, scope=None)
        info_violations = [v for v in violations if v.severity == "info"]
        error_violations = [v for v in violations if v.severity == "error"]

        assert len(info_violations) >= 1  # function-call URL
        assert len(error_violations) >= 1  # real missing endpoint

    def test_no_violations_when_all_match(self, tmp_path: Path):
        """If all endpoints match (regardless of function-call), no violations."""
        _make_file(tmp_path, "frontend/src/svc.ts", """\
            import { HttpClient } from '@angular/common/http';

            export class SomeService {
                constructor(private http: HttpClient) {}

                getItems() {
                    return this.http.get<any>('/api/items');
                }
            }
        """)
        _make_file(tmp_path, "backend/Controllers/ItemsController.cs", """\
            using Microsoft.AspNetCore.Mvc;

            [Route("api/[controller]")]
            [ApiController]
            public class ItemsController : ControllerBase
            {
                [HttpGet]
                public IActionResult GetAll() => Ok();
            }
        """)

        violations = run_endpoint_xref_scan(tmp_path, scope=None)
        assert len(violations) == 0


# ============================================================
# CLI severity filter behavior
# ============================================================
class TestCliSeverityFilter:
    """Verify the CLI actionable-filter logic (simulated)."""

    def _make_violation(self, check, severity, message="test"):
        from agent_team.quality_checks import Violation
        return Violation(
            check=check,
            message=message,
            file_path="test.ts",
            line=1,
            severity=severity,
        )

    def test_filter_excludes_info(self):
        """Info-only violations should be filtered as non-actionable."""
        violations = [
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-001", "info"),
        ]
        actionable = [v for v in violations if v.severity != "info"]
        assert len(actionable) == 0

    def test_filter_keeps_error_and_warning(self):
        """Error and warning violations remain actionable."""
        violations = [
            self._make_violation("XREF-001", "error"),
            self._make_violation("XREF-002", "warning"),
            self._make_violation("XREF-001", "info"),
        ]
        actionable = [v for v in violations if v.severity != "info"]
        assert len(actionable) == 2

    def test_all_info_no_fix_trigger(self):
        """When all violations are info, no fix should be triggered."""
        violations = [
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-001", "info"),
        ]
        actionable = [v for v in violations if v.severity != "info"]
        should_fix = bool(actionable)
        assert should_fix is False

    def test_mixed_triggers_fix(self):
        """When at least one actionable violation exists, fix should trigger."""
        violations = [
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-001", "error"),
            self._make_violation("XREF-001", "info"),
        ]
        actionable = [v for v in violations if v.severity != "info"]
        should_fix = bool(actionable)
        assert should_fix is True

    def test_info_count_computed(self):
        """Info-only count should be computable for reporting."""
        violations = [
            self._make_violation("XREF-001", "error"),
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-001", "info"),
            self._make_violation("XREF-002", "warning"),
        ]
        actionable = [v for v in violations if v.severity != "info"]
        info_count = len(violations) - len(actionable)
        assert len(actionable) == 2
        assert info_count == 2
