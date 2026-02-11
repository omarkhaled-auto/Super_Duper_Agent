"""Tests for XREF endpoint cross-reference scanning bug fixes.

Covers 5 bugs fixed in the extraction and normalization logic:

BUG-1: Variable-URL frontend calls (Angular bare variable refs)
BUG-2: Deduplication of frontend calls by line number
BUG-3: Base URL variable stripping in normalization + resolution
BUG-4: Express mount prefix resolution via import/require tracing
BUG-5: ASP.NET ~ route override (absolute path, ignore controller prefix)

Plus an integration class that validates end-to-end XREF scanning with
the fixes applied.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agent_team.quality_checks import (
    _normalize_api_path,
    _extract_frontend_http_calls,
    _extract_backend_routes_dotnet,
    _extract_backend_routes_express,
    _resolve_import_path,
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
# BUG-1: Variable-URL frontend calls (Angular bare variable refs)
# ============================================================
class TestBug1VariableUrlResolution:
    """BUG-1: _extract_frontend_http_calls resolves this.http.get(this.apiUrl)
    by looking up field declarations like ``private apiUrl = '/api/tasks'``.
    """

    def test_simple_variable_url_resolved(self, tmp_path: Path):
        """this.http.get<Task>(this.apiUrl) should resolve to /api/tasks."""
        _make_file(tmp_path, "src/services/task.service.ts", """\
            import { Injectable } from '@angular/core';
            import { HttpClient } from '@angular/common/http';

            @Injectable()
            export class TaskService {
                private apiUrl = '/api/tasks';

                constructor(private http: HttpClient) {}

                getAll() {
                    return this.http.get<Task>(this.apiUrl, { observe: 'response' });
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 1
        paths = [c.path for c in calls]
        assert any("/api/tasks" in p for p in paths), f"Expected /api/tasks in {paths}"

    def test_nested_generics_variable_url(self, tmp_path: Path):
        """this.http.get<PaginatedResponse<Task>>(this.apiUrl) with nested <> works."""
        _make_file(tmp_path, "src/services/task.service.ts", """\
            import { HttpClient } from '@angular/common/http';

            export class TaskService {
                private apiUrl = '/api/tasks';

                constructor(private http: HttpClient) {}

                getPaginated() {
                    return this.http.get<PaginatedResponse<Task>>(this.apiUrl);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 1
        paths = [c.path for c in calls]
        assert any("/api/tasks" in p for p in paths), f"Expected /api/tasks in {paths}"

    def test_unresolvable_variable_skipped(self, tmp_path: Path):
        """Variable with no field declaration should be silently skipped."""
        _make_file(tmp_path, "src/services/task.service.ts", """\
            import { HttpClient } from '@angular/common/http';

            export class TaskService {
                constructor(private http: HttpClient) {}

                getAll() {
                    return this.http.get<Task>(this.unknownUrl);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        # No call should be extracted for an unresolvable variable
        assert len(calls) == 0

    def test_post_method_variable_url(self, tmp_path: Path):
        """this.http.post(this.apiUrl, data) resolves correctly and has POST method."""
        _make_file(tmp_path, "src/services/item.service.ts", """\
            export class ItemService {
                private apiUrl = '/api/items';
                constructor(private http: HttpClient) {}
                create(data: any) {
                    return this.http.post(this.apiUrl, data);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 1
        post_calls = [c for c in calls if c.method == "POST"]
        assert len(post_calls) >= 1, f"Expected POST call, got {[c.method for c in calls]}"
        assert any("/api/items" in c.path for c in post_calls)

    def test_readonly_field_resolved(self, tmp_path: Path):
        """readonly field declarations should be resolved too."""
        _make_file(tmp_path, "src/services/auth.service.ts", """\
            export class AuthService {
                readonly authUrl = '/api/auth';
                constructor(private http: HttpClient) {}
                login() {
                    return this.http.post(this.authUrl, {});
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 1
        paths = [c.path for c in calls]
        assert any("/api/auth" in p for p in paths)

    def test_multiple_variable_urls_in_same_file(self, tmp_path: Path):
        """Multiple different variable URLs in the same class should all resolve."""
        _make_file(tmp_path, "src/services/multi.service.ts", """\
            export class MultiService {
                private tasksUrl = '/api/tasks';
                private usersUrl = '/api/users';
                constructor(private http: HttpClient) {}
                getTasks() {
                    return this.http.get<Task[]>(this.tasksUrl);
                }
                getUsers() {
                    return this.http.get<User[]>(this.usersUrl);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        paths = [c.path for c in calls]
        assert any("/api/tasks" in p for p in paths), f"Missing /api/tasks in {paths}"
        assert any("/api/users" in p for p in paths), f"Missing /api/users in {paths}"

    def test_triple_nested_generics_no_crash(self, tmp_path: Path):
        """Triple-nested generics <A<B<C>>> exceed regex depth (1 level nesting
        supported). The variable-URL regex should not crash; the call is simply
        not captured by the nested-generic pattern. This is expected behavior."""
        _make_file(tmp_path, "src/services/deep.service.ts", """\
            export class DeepService {
                private apiUrl = '/api/deep';
                constructor(private http: HttpClient) {}
                get() {
                    return this.http.get<ApiResponse<PaginatedList<Item>>>(this.apiUrl);
                }
            }
        """)

        # Should not crash — calls may or may not be extracted depending on
        # regex depth support, but no exception should be raised.
        calls = _extract_frontend_http_calls(tmp_path, None)
        # We do not assert on count; the important thing is no crash.
        assert isinstance(calls, list)

    def test_public_field_resolved(self, tmp_path: Path):
        """public field declarations should be resolved too."""
        _make_file(tmp_path, "src/services/pub.service.ts", """\
            export class PubService {
                public endpoint = '/api/pub';
                constructor(private http: HttpClient) {}
                fetch() {
                    return this.http.get(this.endpoint);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 1
        paths = [c.path for c in calls]
        assert any("/api/pub" in p for p in paths)


# ============================================================
# BUG-2: Deduplication of frontend calls by line number
# ============================================================
class TestBug2Deduplication:
    """BUG-2: Angular and Axios regex overlap on this.http.post should
    produce exactly 1 call, not 2.  Deduplication is by line number.
    """

    def test_single_http_post_no_duplicate(self, tmp_path: Path):
        """this.http.post<Res>('/api/items', data) matches both Angular and
        Axios regex but should yield exactly 1 call after dedup."""
        _make_file(tmp_path, "src/services/item.service.ts", """\
            export class ItemService {
                constructor(private http: HttpClient) {}
                create(data: any) {
                    return this.http.post<CreateRes>('/api/items', data);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        # Exactly 1 call, no duplicate
        api_items_calls = [c for c in calls if "/api/items" in c.path]
        assert len(api_items_calls) == 1, (
            f"Expected exactly 1 call for /api/items, got {len(api_items_calls)}: {api_items_calls}"
        )

    def test_two_different_calls_not_over_deduped(self, tmp_path: Path):
        """Two DIFFERENT calls on different lines should produce 2 calls."""
        _make_file(tmp_path, "src/services/multi.service.ts", """\
            export class MultiService {
                constructor(private http: HttpClient) {}
                create(data: any) {
                    return this.http.post<Res>('/api/items', data);
                }
                update(id: number, data: any) {
                    return this.http.put<Res>('/api/items/' + id, data);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) >= 2, f"Expected at least 2 calls, got {len(calls)}: {calls}"

    def test_same_url_different_methods_both_captured(self, tmp_path: Path):
        """GET and POST to the same URL on different lines should both appear."""
        _make_file(tmp_path, "src/services/dual.service.ts", """\
            export class DualService {
                constructor(private http: HttpClient) {}
                getItems() {
                    return this.http.get<Item[]>('/api/items');
                }
                createItem(data: any) {
                    return this.http.post<Item>('/api/items', data);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        methods = {c.method for c in calls if "/api/items" in c.path}
        assert "GET" in methods, f"Missing GET in {methods}"
        assert "POST" in methods, f"Missing POST in {methods}"

    def test_http_get_with_axios_style_no_dup(self, tmp_path: Path):
        """this.http.get matches both Angular and possibly Axios ('http' prefix).
        Dedup by line ensures exactly 1."""
        _make_file(tmp_path, "src/services/overlap.service.ts", """\
            export class OverlapService {
                constructor(private http: HttpClient) {}
                fetch() {
                    return this.http.get<Data>('/api/data');
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        data_calls = [c for c in calls if "/api/data" in c.path]
        assert len(data_calls) == 1, (
            f"Expected 1 call for /api/data, got {len(data_calls)}"
        )

    def test_three_calls_on_three_lines(self, tmp_path: Path):
        """Three distinct calls on separate lines should all be captured."""
        _make_file(tmp_path, "src/services/triple.service.ts", """\
            export class TripleService {
                constructor(private http: HttpClient) {}
                a() { return this.http.get<A>('/api/a'); }
                b() { return this.http.post<B>('/api/b', {}); }
                c() { return this.http.delete<C>('/api/c'); }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        assert len(calls) == 3, f"Expected 3 calls, got {len(calls)}: {calls}"


# ============================================================
# BUG-3: Base URL variable stripping in normalization
# ============================================================
class TestBug3BaseUrlNormalization:
    """BUG-3: _normalize_api_path strips leading ${...} patterns that
    contain '.' (base URL references), and _extract_frontend_http_calls
    resolves ${this.xxx} prefixes via field lookup.
    """

    def test_strip_this_apiUrl_prefix(self):
        """${this.apiUrl}/auth/login should normalize to /auth/login."""
        result = _normalize_api_path("${this.apiUrl}/auth/login")
        assert result == "/auth/login"

    def test_strip_environment_apiUrl_prefix(self):
        """${environment.apiUrl}/tasks should normalize to /tasks."""
        result = _normalize_api_path("${environment.apiUrl}/tasks")
        assert result == "/tasks"

    def test_mid_path_param_unaffected(self):
        """/tenders/${tenderId}/approval should keep the mid-path param."""
        result = _normalize_api_path("/tenders/${tenderId}/approval")
        # tenderId has no dot, so not a base URL var; should become {param}
        assert "/tenders/{param}/approval" in result

    def test_base_url_var_alone(self):
        """${this.apiUrl} alone should normalize to /."""
        result = _normalize_api_path("${this.apiUrl}")
        assert result == "/"

    def test_dotted_var_at_start_stripped(self):
        """${config.baseUrl}/users should strip the base URL var."""
        result = _normalize_api_path("${config.baseUrl}/users")
        assert result == "/users"

    def test_non_dotted_var_not_stripped(self):
        """${apiUrl}/users -- no dot inside, so NOT a base URL var.
        Should be treated as a path param."""
        result = _normalize_api_path("${apiUrl}/users")
        # No dot = not stripped, becomes {param}
        assert "{param}" in result

    def test_base_url_resolution_in_extraction(self, tmp_path: Path):
        """BUG-3+: ${this.apiUrl}/login resolves via field lookup.
        If apiUrl = '${environment.apiUrl}/auth', result = '${environment.apiUrl}/auth/login'.
        After normalization, ${environment.apiUrl} is stripped -> /auth/login.
        """
        _make_file(tmp_path, "src/services/auth.service.ts", """\
            export class AuthService {
                private apiUrl = '${environment.apiUrl}/auth';
                constructor(private http: HttpClient) {}
                login(data: any) {
                    return this.http.post<Res>(`${this.apiUrl}/login`, data);
                }
            }
        """)

        calls = _extract_frontend_http_calls(tmp_path, None)
        # The resolved path should contain /auth/login after the base URL
        # variable resolution chain
        assert len(calls) >= 1
        # After field resolution: ${environment.apiUrl}/auth/login
        # After normalization: /auth/login
        paths = [c.path for c in calls]
        # The raw path should contain 'auth' and 'login'
        assert any("auth" in p and "login" in p for p in paths), (
            f"Expected auth/login path in {paths}"
        )

    def test_base_url_with_trailing_slash_stripped(self):
        """${this.baseUrl}/ should normalize to /."""
        result = _normalize_api_path("${this.baseUrl}/")
        assert result == "/"

    def test_api_prefix_removed_after_base_url_strip(self):
        """${this.baseUrl}/api/v1/users -> /api/v1/users -> /users."""
        result = _normalize_api_path("${this.baseUrl}/api/v1/users")
        assert result == "/users"

    def test_multiple_dots_in_var_stripped(self):
        """${this.config.api.baseUrl}/data should strip the dotted base var."""
        result = _normalize_api_path("${this.config.api.baseUrl}/data")
        assert result == "/data"


# ============================================================
# BUG-4: Express mount prefix resolution
# ============================================================
class TestBug4ExpressMountPrefix:
    """BUG-4: _extract_backend_routes_express resolves app.use('/prefix', routerVar)
    to the actual route file by tracing import/require statements.

    NOTE: The second pass of Express route extraction only considers files whose
    name contains a route-detection keyword (route, router, controller, handler,
    api, endpoint, app, server, index).  Test files are named accordingly.
    """

    def test_import_default_mount_prefix(self, tmp_path: Path):
        """Default import: import authRouter from './routes/authRoute'.
        app.use('/api/auth', authRouter) should apply /api/auth prefix.
        """
        _make_file(tmp_path, "server/index.ts", """\
            import authRouter from './routes/authRoute';
            const app = express();
            app.use('/api/auth', authRouter);
        """)
        _make_file(tmp_path, "server/routes/authRoute.ts", """\
            const router = express.Router();
            router.get('/login', loginHandler);
            router.post('/register', registerHandler);
            export default router;
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("/api/auth/login" in p for p in paths), f"Expected /api/auth/login in {paths}"
        assert any("/api/auth/register" in p for p in paths), f"Expected /api/auth/register in {paths}"

    def test_destructured_import_mount_prefix(self, tmp_path: Path):
        """Destructured import: import { taskRouter } from './routes/taskRouter'.
        app.use('/api/tasks', taskRouter) should apply prefix.
        """
        _make_file(tmp_path, "server/app.ts", """\
            import { taskRouter } from './routes/taskRouter';
            const app = express();
            app.use('/api/tasks', taskRouter);
        """)
        _make_file(tmp_path, "server/routes/taskRouter.ts", """\
            const router = express.Router();
            router.get('/', getAllTasks);
            router.post('/', createTask);
            router.get('/:id', getTaskById);
            export { router as taskRouter };
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        # At least one route should have the /api/tasks prefix
        assert any("/api/tasks" in p for p in paths), (
            f"Expected /api/tasks routes in {paths}"
        )

    def test_require_mount_prefix(self, tmp_path: Path):
        """const userRouter = require('./routes/userRoute') with app.use mount."""
        _make_file(tmp_path, "server/index.ts", """\
            const userRouter = require('./routes/userRoute');
            const app = express();
            app.use('/api/users', userRouter);
        """)
        _make_file(tmp_path, "server/routes/userRoute.ts", """\
            const router = express.Router();
            router.get('/', getAllUsers);
            router.delete('/:id', deleteUser);
            module.exports = router;
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("/api/users" in p for p in paths), (
            f"Expected /api/users routes in {paths}"
        )

    def test_multi_dot_import_path_resolved(self, tmp_path: Path):
        """Import path like ./routes/auth.routes should find auth.routes.ts."""
        _make_file(tmp_path, "server/app.ts", """\
            import authRouter from './routes/auth.routes';
            const app = express();
            app.use('/api/auth', authRouter);
        """)
        _make_file(tmp_path, "server/routes/auth.routes.ts", """\
            const router = express.Router();
            router.post('/login', loginHandler);
            export default router;
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("/api/auth/login" in p for p in paths), (
            f"Expected /api/auth/login in {paths}"
        )

    def test_no_mount_prefix_when_no_app_use(self, tmp_path: Path):
        """Route files without app.use mounting should have no prefix."""
        _make_file(tmp_path, "server/routes/itemRoute.ts", """\
            const router = express.Router();
            router.get('/items', getAllItems);
            router.post('/items', createItem);
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("/items" in p for p in paths), f"Expected /items in {paths}"

    def test_multiple_mounts_in_same_file(self, tmp_path: Path):
        """Multiple app.use() mounts in the same file should each resolve."""
        _make_file(tmp_path, "server/index.ts", """\
            import authRouter from './routes/authRoute';
            import taskRouter from './routes/taskRoute';
            const app = express();
            app.use('/api/auth', authRouter);
            app.use('/api/tasks', taskRouter);
        """)
        _make_file(tmp_path, "server/routes/authRoute.ts", """\
            const router = express.Router();
            router.get('/me', getCurrentUser);
            export default router;
        """)
        _make_file(tmp_path, "server/routes/taskRoute.ts", """\
            const router = express.Router();
            router.get('/', listTasks);
            export default router;
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("/api/auth/me" in p for p in paths), f"Missing /api/auth/me in {paths}"
        assert any("/api/tasks" in p for p in paths), f"Missing /api/tasks in {paths}"

    def test_prefix_with_trailing_slash_normalized(self, tmp_path: Path):
        """Mount prefix with trailing slash should still combine correctly."""
        _make_file(tmp_path, "server/index.ts", """\
            import apiRouter from './routes/apiRoute';
            const app = express();
            app.use('/api/', apiRouter);
        """)
        _make_file(tmp_path, "server/routes/apiRoute.ts", """\
            const router = express.Router();
            router.get('/health', healthCheck);
            export default router;
        """)

        routes = _extract_backend_routes_express(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("api" in p and "health" in p for p in paths), (
            f"Expected api/health route in {paths}"
        )


# ============================================================
# BUG-4 sub: _resolve_import_path
# ============================================================
class TestResolveImportPath:
    """Tests for _resolve_import_path extension resolution."""

    def test_ts_extension_appended(self, tmp_path: Path):
        """Import './routes/auth' should find routes/auth.ts."""
        _make_file(tmp_path, "server/routes/auth.ts", "export default router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/auth", mount_file, tmp_path)
        assert result is not None
        assert "auth.ts" in result

    def test_js_extension_appended(self, tmp_path: Path):
        """Import './routes/items' should find routes/items.js if .ts absent."""
        _make_file(tmp_path, "server/routes/items.js", "module.exports = router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/items", mount_file, tmp_path)
        assert result is not None
        assert "items.js" in result

    def test_multi_dot_import_path(self, tmp_path: Path):
        """Import './routes/auth.routes' should find auth.routes.ts, not auth.ts."""
        _make_file(tmp_path, "server/routes/auth.routes.ts", "export default router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/auth.routes", mount_file, tmp_path)
        assert result is not None
        assert "auth.routes.ts" in result

    def test_index_fallback(self, tmp_path: Path):
        """Import './routes' should find routes/index.ts if it exists."""
        _make_file(tmp_path, "server/routes/index.ts", "export default router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes", mount_file, tmp_path)
        assert result is not None
        assert "index.ts" in result

    def test_nonexistent_path_returns_none(self, tmp_path: Path):
        """Import to a nonexistent file should return None."""
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/nonexistent", mount_file, tmp_path)
        assert result is None

    def test_exact_match_with_extension(self, tmp_path: Path):
        """Import './routes/auth.ts' should find auth.ts directly."""
        _make_file(tmp_path, "server/routes/auth.ts", "export default router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/auth.ts", mount_file, tmp_path)
        assert result is not None
        assert "auth.ts" in result

    def test_mjs_extension(self, tmp_path: Path):
        """Import should also find .mjs files."""
        _make_file(tmp_path, "server/routes/esm.mjs", "export default router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/esm", mount_file, tmp_path)
        assert result is not None
        assert "esm.mjs" in result

    def test_multi_dot_with_js(self, tmp_path: Path):
        """Import './routes/user.controller' should find user.controller.js."""
        _make_file(tmp_path, "server/routes/user.controller.js", "module.exports = router;")
        mount_file = tmp_path / "server" / "index.ts"
        mount_file.parent.mkdir(parents=True, exist_ok=True)
        mount_file.write_text("// mount file", encoding="utf-8")

        result = _resolve_import_path("./routes/user.controller", mount_file, tmp_path)
        assert result is not None
        assert "user.controller.js" in result


# ============================================================
# BUG-5: ASP.NET ~ route override
# ============================================================
class TestBug5DotnetTildeOverride:
    """BUG-5: [HttpGet("~/api/path")] means ignore controller prefix."""

    def test_tilde_override_ignores_controller_prefix(self, tmp_path: Path):
        """[HttpGet("~/api/exceptions")] should extract /api/exceptions,
        NOT /api/evaluation/~/api/exceptions."""
        _make_file(tmp_path, "Controllers/EvaluationController.cs", """\
            [Route("api/evaluation")]
            public class EvaluationController : ControllerBase
            {
                [HttpGet]
                public IActionResult GetAll() => Ok();

                [HttpGet("~/api/exceptions")]
                public IActionResult GetExceptions() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        assert any(p == "/api/exceptions" for p in paths), (
            f"Expected /api/exceptions in {paths}"
        )
        # Should NOT have the concatenated version
        assert not any("~/api" in p for p in paths), (
            f"Should not have ~ in any path: {paths}"
        )

    def test_regular_action_combines_prefix(self, tmp_path: Path):
        """Regular action without ~ should combine controller prefix + action."""
        _make_file(tmp_path, "Controllers/TenderController.cs", """\
            [Route("api/tenders")]
            public class TenderController : ControllerBase
            {
                [HttpGet]
                public IActionResult GetAll() => Ok();

                [HttpGet("{id}")]
                public IActionResult GetById(int id) => Ok();

                [HttpPost("submit")]
                public IActionResult Submit() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        # api/tenders (no action suffix for [HttpGet])
        assert any("api/tenders" in p for p in paths)
        # api/tenders/{id} for [HttpGet("{id}")]
        assert any("api/tenders/" in p and "{" in p for p in paths), (
            f"Expected parametric route, got {paths}"
        )
        # api/tenders/submit for [HttpPost("submit")]
        assert any("api/tenders/submit" in p for p in paths), (
            f"Expected api/tenders/submit in {paths}"
        )

    def test_tilde_with_slash_prefix(self, tmp_path: Path):
        """[HttpPost("~/api/v2/special")] should extract /api/v2/special."""
        _make_file(tmp_path, "Controllers/LegacyController.cs", """\
            [Route("api/legacy")]
            public class LegacyController : ControllerBase
            {
                [HttpPost("~/api/v2/special")]
                public IActionResult Special() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        assert any(p == "/api/v2/special" for p in paths), (
            f"Expected /api/v2/special in {paths}"
        )

    def test_mixed_tilde_and_regular(self, tmp_path: Path):
        """Controller with both regular routes and tilde overrides."""
        _make_file(tmp_path, "Controllers/MixedController.cs", """\
            [Route("api/mixed")]
            public class MixedController : ControllerBase
            {
                [HttpGet]
                public IActionResult GetAll() => Ok();

                [HttpGet("{id}")]
                public IActionResult GetById(int id) => Ok();

                [HttpGet("~/api/other/special")]
                public IActionResult OtherSpecial() => Ok();

                [HttpPost("create")]
                public IActionResult Create() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        # Regular routes should have prefix
        assert any("api/mixed" in p and "create" in p for p in paths)
        # Tilde route should NOT have prefix
        assert any(p == "/api/other/special" for p in paths), (
            f"Expected /api/other/special in {paths}"
        )

    def test_tilde_method_is_correct(self, tmp_path: Path):
        """Tilde override should preserve the correct HTTP method."""
        _make_file(tmp_path, "Controllers/MethodController.cs", """\
            [Route("api/ctrl")]
            public class MethodController : ControllerBase
            {
                [HttpDelete("~/api/admin/purge")]
                public IActionResult Purge() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        delete_routes = [r for r in routes if r.method == "DELETE"]
        assert len(delete_routes) >= 1
        assert any(r.path == "/api/admin/purge" for r in delete_routes)

    def test_no_route_prefix_with_tilde(self, tmp_path: Path):
        """Controller without [Route] prefix + tilde override should still work."""
        _make_file(tmp_path, "Controllers/NoRouteController.cs", """\
            public class NoRouteController : ControllerBase
            {
                [HttpGet("~/api/health")]
                public IActionResult Health() => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        assert any(p == "/api/health" for p in paths), (
            f"Expected /api/health in {paths}"
        )

    def test_tilde_with_path_params(self, tmp_path: Path):
        """Tilde route with path parameters should work correctly."""
        _make_file(tmp_path, "Controllers/SpecialController.cs", """\
            [Route("api/special")]
            public class SpecialController : ControllerBase
            {
                [HttpGet("~/api/override/{id}/details")]
                public IActionResult GetDetails(int id) => Ok();
            }
        """)

        routes = _extract_backend_routes_dotnet(tmp_path, None)
        paths = [r.path for r in routes]
        assert any("api/override" in p and "details" in p for p in paths), (
            f"Expected /api/override/{{id}}/details in {paths}"
        )
        # Should NOT contain the controller prefix
        assert not any("special" in p.lower() for p in paths), (
            f"Tilde route should not contain controller prefix 'special': {paths}"
        )


# ============================================================
# Integration: run_endpoint_xref_scan with bug fixes applied
# ============================================================
class TestXrefIntegration:
    """Integration tests validating the full run_endpoint_xref_scan pipeline
    with all bug fixes applied together.
    """

    def test_angular_variable_url_matches_express_route(self, tmp_path: Path):
        """Angular service using variable URL should match Express route
        via variable resolution + normalization."""
        # Frontend
        _make_file(tmp_path, "src/services/task.service.ts", """\
            export class TaskService {
                private apiUrl = '/api/tasks';
                constructor(private http: HttpClient) {}
                getAll() {
                    return this.http.get<Task[]>(this.apiUrl);
                }
            }
        """)
        # Backend -- file named with 'route' keyword so Express scanner picks it up
        _make_file(tmp_path, "server/routes/taskRoute.ts", """\
            const router = express.Router();
            router.get('/api/tasks', getAllTasks);
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        # Should match: frontend GET /api/tasks == backend GET /api/tasks
        xref001 = [v for v in violations if v.check == "XREF-001"]
        task_violations = [v for v in xref001 if "tasks" in v.message.lower()]
        assert len(task_violations) == 0, (
            f"Should have no XREF-001 for tasks, but got: {task_violations}"
        )

    def test_base_url_var_stripped_for_matching(self, tmp_path: Path):
        """Frontend using ${environment.apiUrl}/items should match backend /items
        after base URL stripping."""
        _make_file(tmp_path, "src/services/item.service.ts", """\
            export class ItemService {
                constructor(private http: HttpClient) {}
                getItems() {
                    return this.http.get<Item[]>('${environment.apiUrl}/items');
                }
            }
        """)
        _make_file(tmp_path, "server/routes/itemRoute.ts", """\
            const router = express.Router();
            router.get('/api/items', getAllItems);
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        # After normalization: both become /items
        xref001 = [v for v in violations if v.check == "XREF-001"]
        item_violations = [v for v in xref001 if "items" in v.message.lower()]
        assert len(item_violations) == 0, (
            f"Should match after base URL strip, but got: {item_violations}"
        )

    def test_express_mount_prefix_matches_frontend(self, tmp_path: Path):
        """Frontend calling /api/auth/login should match Express route
        mounted with app.use('/api/auth', authRouter)."""
        # Frontend
        _make_file(tmp_path, "src/services/auth.service.ts", """\
            export class AuthService {
                constructor(private http: HttpClient) {}
                login(data: any) {
                    return this.http.post<Res>('/api/auth/login', data);
                }
            }
        """)
        # Backend mount file
        _make_file(tmp_path, "server/app.ts", """\
            import authRouter from './routes/authRoute';
            const app = express();
            app.use('/api/auth', authRouter);
        """)
        # Backend route file
        _make_file(tmp_path, "server/routes/authRoute.ts", """\
            const router = express.Router();
            router.post('/login', loginHandler);
            export default router;
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        xref001 = [v for v in violations if v.check == "XREF-001"]
        auth_violations = [v for v in xref001 if "auth" in v.message.lower() and "login" in v.message.lower()]
        assert len(auth_violations) == 0, (
            f"Should match via mount prefix, but got: {auth_violations}"
        )

    def test_dotnet_tilde_route_matches_frontend(self, tmp_path: Path):
        """Frontend calling /api/exceptions should match dotnet [HttpGet("~/api/exceptions")]."""
        _make_file(tmp_path, "src/services/exception.service.ts", """\
            export class ExceptionService {
                constructor(private http: HttpClient) {}
                getExceptions() {
                    return this.http.get<any>('/api/exceptions');
                }
            }
        """)
        _make_file(tmp_path, "Controllers/EvalController.cs", """\
            [Route("api/evaluation")]
            public class EvalController : ControllerBase
            {
                [HttpGet("~/api/exceptions")]
                public IActionResult GetExceptions() => Ok();
            }
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        xref001 = [v for v in violations if v.check == "XREF-001"]
        exc_violations = [v for v in xref001 if "exceptions" in v.message.lower()]
        assert len(exc_violations) == 0, (
            f"Tilde route should match frontend call, but got: {exc_violations}"
        )

    def test_deduped_calls_do_not_produce_extra_violations(self, tmp_path: Path):
        """Duplicate calls (from regex overlap) should not produce duplicate violations."""
        _make_file(tmp_path, "src/services/item.service.ts", """\
            export class ItemService {
                constructor(private http: HttpClient) {}
                create(data: any) {
                    return this.http.post<Res>('/api/items', data);
                }
            }
        """)
        # Backend exists but with a different route, so /api/items is unmatched
        _make_file(tmp_path, "server/routes/otherRoute.ts", """\
            const router = express.Router();
            router.get('/api/other', handler);
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        item_violations = [v for v in violations if "items" in v.message.lower()]
        assert len(item_violations) == 1, (
            f"Expected exactly 1 violation for /api/items (no dupes), got {len(item_violations)}"
        )

    def test_method_mismatch_xref002(self, tmp_path: Path):
        """Frontend GET to a backend POST-only route should produce XREF-002."""
        _make_file(tmp_path, "src/services/action.service.ts", """\
            export class ActionService {
                constructor(private http: HttpClient) {}
                execute() {
                    return this.http.get<any>('/api/actions/execute');
                }
            }
        """)
        _make_file(tmp_path, "server/routes/actionRoute.ts", """\
            const router = express.Router();
            router.post('/api/actions/execute', executeHandler);
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        xref002 = [v for v in violations if v.check == "XREF-002"]
        assert len(xref002) >= 1, f"Expected XREF-002 for method mismatch, got {violations}"

    def test_empty_project_no_crash(self, tmp_path: Path):
        """Empty project directory should return empty list, no crash."""
        violations = run_endpoint_xref_scan(tmp_path, None)
        assert violations == []

    def test_frontend_only_no_crash(self, tmp_path: Path):
        """Project with only frontend calls and no backend returns empty list."""
        _make_file(tmp_path, "src/services/solo.service.ts", """\
            export class SoloService {
                constructor(private http: HttpClient) {}
                get() { return this.http.get<any>('/api/solo'); }
            }
        """)

        violations = run_endpoint_xref_scan(tmp_path, None)
        # No backend routes found -> returns empty
        assert violations == []
