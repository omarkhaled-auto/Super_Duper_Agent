# Build 3 Technology Research: Security & Observability

## 1. JWT Validation Verification

### 1.1 PyJWT Library API (v2.x)

**Core decode/verify function:**
```python
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    MissingRequiredClaimError,
    DecodeError,
)

# Full validation (production)
payload = jwt.decode(
    token,
    key,                          # Secret key or public key
    algorithms=["HS256"],         # REQUIRED — prevents algorithm confusion attacks
    audience="my-app",            # Validates 'aud' claim
    issuer="https://auth.example.com",  # Validates 'iss' claim
    leeway=5,                     # Clock skew tolerance (seconds)
    options={
        "require": ["exp", "iss", "sub"],  # Require specific claims
    },
)

# Exception hierarchy:
# jwt.exceptions.DecodeError          — malformed token
# jwt.exceptions.InvalidSignatureError — signature mismatch
# jwt.exceptions.ExpiredSignatureError — exp claim past
# jwt.exceptions.InvalidAudienceError  — aud mismatch
# jwt.exceptions.InvalidIssuerError    — iss mismatch
# jwt.exceptions.MissingRequiredClaimError — required claim absent
```

### 1.2 python-jose Library API

```python
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError

# Strict production validation
decoded = jwt.decode(
    token,
    'secret',
    algorithms=['HS256'],
    audience='myapp',
    issuer='auth-service',
    options={
        'verify_signature': True,
        'verify_exp': True,
        'verify_aud': True,
        'require_exp': True,
        'require_iat': True,
        'leeway': 0,          # No time leeway in strict mode
    }
)

# DANGEROUS — permissive mode (detect this in scans!)
options_permissive = {
    'verify_signature': True,
    'verify_exp': False,      # VULN: token never expires
    'verify_nbf': False,
    'verify_aud': False,       # VULN: accepts any audience
    'require_exp': False,      # VULN: no expiration required
}
```

### 1.3 Static Analysis: Detecting Unauthenticated Endpoints

**Pattern: Find endpoints missing auth middleware/decorators**

```python
import re
from pathlib import Path
from typing import NamedTuple

class AuthViolation(NamedTuple):
    file: str
    line: int
    endpoint: str
    code: str   # SEC-001, SEC-002, etc.
    message: str

# ============================================================
# FRAMEWORK: FastAPI
# ============================================================
# Auth is typically via Depends() with a security dependency
_RE_FASTAPI_ROUTE = re.compile(
    r'@(?:app|router)\.(get|post|put|patch|delete|options|head)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
# Auth dependency pattern: Depends(get_current_user) or Security(...)
_RE_FASTAPI_AUTH = re.compile(
    r'Depends\s*\(\s*(?:get_current_user|verify_token|require_auth|check_auth|oauth2_scheme)'
    r'|Security\s*\('
    r'|Depends\s*\(\s*\w*[Aa]uth\w*\)',
)

def check_fastapi_auth(file_path: Path) -> list[AuthViolation]:
    """Check FastAPI routes for missing auth dependencies."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for i, line in enumerate(lines):
        route_match = _RE_FASTAPI_ROUTE.search(line)
        if not route_match:
            continue

        endpoint = route_match.group(2)
        # Skip health/docs endpoints
        if endpoint in ("/health", "/healthz", "/ready", "/docs", "/openapi.json", "/redoc"):
            continue

        # Search function body (next 20 lines) for auth dependency
        func_block = "\n".join(lines[i:i+20])
        if not _RE_FASTAPI_AUTH.search(func_block):
            violations.append(AuthViolation(
                file=str(file_path),
                line=i + 1,
                endpoint=endpoint,
                code="SEC-001",
                message=f"FastAPI endpoint '{endpoint}' has no auth dependency (Depends/Security)",
            ))
    return violations


# ============================================================
# FRAMEWORK: Express.js / Node.js
# ============================================================
_RE_EXPRESS_ROUTE = re.compile(
    r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_RE_EXPRESS_AUTH_MIDDLEWARE = re.compile(
    r'(?:authenticate|requireAuth|verifyToken|isAuthenticated|authMiddleware|passport\.authenticate'
    r'|requireRole|checkAuth|ensureAuth|protect)\s*[\(,]',
    re.IGNORECASE,
)

def check_express_auth(file_path: Path) -> list[AuthViolation]:
    """Check Express routes for missing auth middleware."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for i, line in enumerate(lines):
        route_match = _RE_EXPRESS_ROUTE.search(line)
        if not route_match:
            continue
        endpoint = route_match.group(2)
        if endpoint in ("/health", "/healthz", "/ready", "/api-docs"):
            continue
        # Check if auth middleware is in the route definition line
        if not _RE_EXPRESS_AUTH_MIDDLEWARE.search(line):
            violations.append(AuthViolation(
                file=str(file_path),
                line=i + 1,
                endpoint=endpoint,
                code="SEC-001",
                message=f"Express endpoint '{endpoint}' has no auth middleware in route definition",
            ))
    return violations


# ============================================================
# FRAMEWORK: ASP.NET Core (C#)
# ============================================================
_RE_ASPNET_CONTROLLER_ACTION = re.compile(
    r'\[Http(Get|Post|Put|Patch|Delete)\s*(?:\(\s*"([^"]*)")?\s*\]',
)
_RE_ASPNET_AUTH = re.compile(
    r'\[Authorize\b'       # [Authorize] or [Authorize(Roles=...)]
    r'|\[Authorize\('
    r'|\[AllowAnonymous\]',  # Explicitly public
)

def check_aspnet_auth(file_path: Path) -> list[AuthViolation]:
    """Check ASP.NET controller actions for [Authorize] attribute."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    # Check if controller-level [Authorize] exists
    has_class_auth = bool(re.search(r'\[Authorize\b.*\]\s*\n\s*public\s+class\s+\w+Controller', content, re.DOTALL))

    for i, line in enumerate(lines):
        action_match = _RE_ASPNET_CONTROLLER_ACTION.search(line)
        if not action_match:
            continue
        method = action_match.group(1)
        route = action_match.group(2) or ""

        if has_class_auth:
            continue  # Controller-level auth covers all actions

        # Look backwards up to 5 lines for [Authorize] or [AllowAnonymous]
        preceding = "\n".join(lines[max(0, i-5):i+1])
        if not _RE_ASPNET_AUTH.search(preceding):
            violations.append(AuthViolation(
                file=str(file_path),
                line=i + 1,
                endpoint=f"[Http{method}(\"{route}\")]",
                code="SEC-001",
                message=f"ASP.NET action '{method} {route}' has no [Authorize] attribute",
            ))
    return violations


# ============================================================
# FRAMEWORK: Django
# ============================================================
_RE_DJANGO_VIEW = re.compile(
    r'def\s+(get|post|put|patch|delete|list|create|retrieve|update|destroy)\s*\(\s*self',
    re.IGNORECASE,
)
_RE_DJANGO_AUTH = re.compile(
    r'permission_classes\s*=\s*\[.*(?:IsAuthenticated|IsAdminUser|AllowAny)'
    r'|@login_required'
    r'|@permission_required'
    r'|authentication_classes\s*=',
)
```

### 1.4 JWT Misconfiguration Detection Patterns

```python
# ============================================================
# Detect JWT misconfigurations in source code
# ============================================================

_JWT_MISCONFIG_PATTERNS = [
    # SEC-002: Algorithm set to 'none'
    {
        "code": "SEC-002",
        "severity": "critical",
        "regex": re.compile(
            r'''algorithms?\s*[:=]\s*\[?\s*['"]none['"]''',
            re.IGNORECASE,
        ),
        "message": "JWT algorithm set to 'none' — signature bypass vulnerability",
    },
    # SEC-003: Signature verification disabled
    {
        "code": "SEC-003",
        "severity": "critical",
        "regex": re.compile(
            r'''verify_signature['"]\s*:\s*False'''
            r'''|verify\s*[:=]\s*False'''
            r'''|options\s*[:=]\s*\{[^}]*'verify'\s*:\s*False''',
            re.IGNORECASE,
        ),
        "message": "JWT signature verification disabled",
    },
    # SEC-004: Expiration check disabled
    {
        "code": "SEC-004",
        "severity": "high",
        "regex": re.compile(
            r'''verify_exp['"]\s*:\s*False'''
            r'''|options\s*[:=]\s*\{[^}]*'verify_exp'\s*:\s*False''',
            re.IGNORECASE,
        ),
        "message": "JWT expiration verification disabled — tokens never expire",
    },
    # SEC-005: Hardcoded JWT secret
    {
        "code": "SEC-005",
        "severity": "critical",
        "regex": re.compile(
            r'''(?:jwt_secret|secret_key|JWT_SECRET)\s*[:=]\s*['"][^'"]{8,}['"]''',
            re.IGNORECASE,
        ),
        "message": "Hardcoded JWT secret in source code",
    },
    # SEC-006: Weak algorithm (HS256 with public key)
    {
        "code": "SEC-006",
        "severity": "high",
        "regex": re.compile(
            r'''algorithms?\s*[:=]\s*\[?\s*['"]HS256['"]\s*\]?\s*.*public.?key''',
            re.IGNORECASE | re.DOTALL,
        ),
        "message": "HS256 used with what appears to be a public key — algorithm confusion risk",
    },
]

def scan_jwt_misconfigurations(file_path: Path) -> list[AuthViolation]:
    """Scan a file for JWT misconfigurations."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern in _JWT_MISCONFIG_PATTERNS:
            if pattern["regex"].search(line):
                violations.append(AuthViolation(
                    file=str(file_path),
                    line=i + 1,
                    endpoint="",
                    code=pattern["code"],
                    message=pattern["message"],
                ))
    return violations
```

---

## 2. CORS Verification

### 2.1 CORS Misconfiguration Detection (Static Analysis)

```python
import re
from typing import NamedTuple

class CorsViolation(NamedTuple):
    file: str
    line: int
    code: str
    severity: str
    message: str

# ============================================================
# CORS-001: Wildcard origin in production
# ============================================================
_CORS_WILDCARD_PATTERNS = [
    # Python (FastAPI / Flask-CORS)
    re.compile(r'''allow_origins\s*=\s*\[\s*['"]\*['"]\s*\]'''),
    re.compile(r'''origins\s*=\s*\[\s*['"]\*['"]\s*\]'''),
    re.compile(r'''CORS\s*\(\s*app\s*,\s*origins\s*=\s*['"]\*['"]'''),
    re.compile(r'''CORS\s*\(\s*app\s*\)'''),  # Flask-CORS default = allow all
    # JavaScript (Express cors middleware)
    re.compile(r'''origin\s*:\s*['"]\*['"]'''),
    re.compile(r'''origin\s*:\s*true'''),  # Reflects any origin
    re.compile(r'''cors\(\s*\)'''),  # Express cors() with no config = allow all
    # C# (ASP.NET Core)
    re.compile(r'''\.AllowAnyOrigin\s*\(\s*\)'''),
    re.compile(r'''WithOrigins\s*\(\s*['"]\*['"]\s*\)'''),
]

# ============================================================
# CORS-002: Credentials with wildcard
# ============================================================
_CORS_CRED_WILDCARD = [
    # allow_credentials=True + wildcard origin is a browser error
    # but some servers send it anyway
    re.compile(
        r'''allow_credentials\s*=\s*True.*allow_origins\s*=\s*\[\s*['"]\*['"]\s*\]''',
        re.DOTALL,
    ),
    re.compile(
        r'''credentials\s*:\s*true.*origin\s*:\s*['"]\*['"]''',
        re.DOTALL | re.IGNORECASE,
    ),
    re.compile(
        r'''\.AllowCredentials\s*\(.*\.AllowAnyOrigin\s*\(''',
        re.DOTALL,
    ),
]

# ============================================================
# CORS-003: Dynamic origin reflection without validation
# ============================================================
_CORS_ORIGIN_REFLECTION = [
    # Express: origin: (origin, cb) => cb(null, true) — reflects any origin
    re.compile(r'''origin\s*:\s*\(\s*\w+\s*,\s*\w+\s*\)\s*=>\s*\w+\s*\(\s*null\s*,\s*true\s*\)'''),
    # Python: returning request origin directly
    re.compile(r'''Access-Control-Allow-Origin.*request\.headers.*origin''', re.IGNORECASE),
]

def scan_cors_misconfigurations(file_path: Path) -> list[CorsViolation]:
    """Scan a single file for CORS misconfigurations."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        for pattern in _CORS_WILDCARD_PATTERNS:
            if pattern.search(line):
                violations.append(CorsViolation(
                    file=str(file_path), line=i+1,
                    code="CORS-001", severity="error",
                    message="Wildcard CORS origin (*) — allows any website to make requests",
                ))
                break

    # Multi-line checks (credentials + wildcard)
    for pattern in _CORS_CRED_WILDCARD:
        if pattern.search(content):
            violations.append(CorsViolation(
                file=str(file_path), line=0,
                code="CORS-002", severity="critical",
                message="CORS credentials enabled with wildcard origin — cookie/auth exposure",
            ))
            break

    for pattern in _CORS_ORIGIN_REFLECTION:
        if pattern.search(content):
            violations.append(CorsViolation(
                file=str(file_path), line=0,
                code="CORS-003", severity="high",
                message="Dynamic origin reflection without validation — effectively wildcard",
            ))
            break

    return violations
```

### 2.2 CORS Header Verification (Runtime with httpx)

```python
import httpx

async def verify_cors_headers(
    base_url: str,
    allowed_origin: str,
    disallowed_origin: str = "https://evil.com",
) -> dict:
    """Verify CORS configuration via actual HTTP requests."""
    results = {}
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        # Test 1: Preflight with allowed origin
        preflight = await client.options(
            f"{base_url}/api/health",
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        results["preflight_status"] = preflight.status_code
        results["allow_origin"] = preflight.headers.get("access-control-allow-origin", "MISSING")
        results["allow_methods"] = preflight.headers.get("access-control-allow-methods", "MISSING")
        results["allow_headers"] = preflight.headers.get("access-control-allow-headers", "MISSING")
        results["allow_credentials"] = preflight.headers.get("access-control-allow-credentials", "MISSING")

        # Test 2: Request with disallowed origin (should NOT return ACAO header)
        evil_resp = await client.get(
            f"{base_url}/api/health",
            headers={"Origin": disallowed_origin},
        )
        evil_acao = evil_resp.headers.get("access-control-allow-origin", "")
        results["evil_origin_reflected"] = evil_acao == disallowed_origin or evil_acao == "*"

        # Test 3: Check credentials + wildcard combo
        if results["allow_origin"] == "*" and results["allow_credentials"] == "true":
            results["critical_vuln"] = "credentials_with_wildcard"

    return results
```

### 2.3 CORS Detection in Framework Configuration

```python
# Framework-specific CORS middleware detection

# FastAPI: CORSMiddleware in main app file
_RE_FASTAPI_CORS = re.compile(
    r'add_middleware\s*\(\s*CORSMiddleware'
    r'|from\s+fastapi\.middleware\.cors\s+import\s+CORSMiddleware',
)

# Express: cors package
_RE_EXPRESS_CORS = re.compile(
    r'''require\s*\(\s*['"]cors['"]\s*\)'''
    r'''|import\s+cors\s+from\s+['"]cors['"]'''
    r'''|app\.use\s*\(\s*cors''',
)

# ASP.NET Core: CORS policy
_RE_ASPNET_CORS = re.compile(
    r'\.AddCors\s*\('
    r'|\.UseCors\s*\('
    r'|services\.AddCors'
    r'|builder\.Services\.AddCors',
)

# Django: django-cors-headers
_RE_DJANGO_CORS = re.compile(
    r'''CORS_ALLOWED_ORIGINS\s*='''
    r'''|CORS_ALLOW_ALL_ORIGINS\s*=\s*True'''
    r'''|['"]corsheaders['"]''',
)
```

---

## 3. Structured Logging & Trace ID Propagation

### 3.1 OpenTelemetry Python SDK — Trace Context

```python
# ============================================================
# Injection: Sending service adds trace context to outgoing request
# ============================================================
from opentelemetry import trace, baggage
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
tracer = trace.get_tracer(__name__)

# Inject trace context into outgoing HTTP headers
with tracer.start_as_current_span("api1_span") as span:
    headers = {}
    TraceContextTextMapPropagator().inject(headers)
    # headers now contains: {'traceparent': '00-<trace_id>-<span_id>-01'}
    # Use these headers in your HTTP client call


# ============================================================
# Extraction: Receiving service reads trace context from request
# ============================================================
from flask import request

carrier = {'traceparent': request.headers.get('Traceparent', '')}
ctx = TraceContextTextMapPropagator().extract(carrier=carrier)

with tracer.start_span("api2_span", context=ctx):
    # This span is now a child of the calling service's span
    pass


# ============================================================
# Manual SpanContext construction (for testing/verification)
# ============================================================
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

span_context = SpanContext(
    trace_id=0xa9c3b99a95cc045e573e163c3ac80a77,  # 16 bytes
    span_id=0xd99d251a8caecd06,                    # 8 bytes
    is_remote=True,
    trace_flags=TraceFlags(0x01),                  # sampled
)
ctx = trace.set_span_in_context(NonRecordingSpan(span_context))
```

### 3.2 W3C Trace Context Format (traceparent header)

```
# Format: version-trace_id-parent_id-trace_flags
# Example: 00-a9c3b99a95cc045e573e163c3ac80a77-d99d251a8caecd06-01

# version:     2 hex chars  (always "00" for current spec)
# trace_id:    32 hex chars (16 bytes, globally unique)
# parent_id:   16 hex chars (8 bytes, span identifier)
# trace_flags: 2 hex chars  (01 = sampled)
```

**Regex for validating traceparent format:**
```python
_RE_TRACEPARENT = re.compile(
    r'^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$'
)

def is_valid_traceparent(value: str) -> bool:
    """Validate W3C traceparent header format."""
    if not _RE_TRACEPARENT.match(value):
        return False
    # trace_id must not be all zeros
    parts = value.split("-")
    if parts[1] == "0" * 32:
        return False
    # parent_id must not be all zeros
    if parts[2] == "0" * 16:
        return False
    return True
```

### 3.3 Structured Logging Verification (Static Analysis)

```python
# ============================================================
# Detect logging format issues in source code
# ============================================================

class LogViolation(NamedTuple):
    file: str
    line: int
    code: str
    severity: str
    message: str

# LOG-001: Unstructured print statements used instead of logger
_RE_PRINT_LOGGING = re.compile(
    r'^\s*print\s*\(',
)

# LOG-002: Logger without structured format (no JSON formatter)
_RE_PYTHON_BASIC_CONFIG = re.compile(
    r'logging\.basicConfig\s*\(',
)
_RE_PYTHON_JSON_FORMATTER = re.compile(
    r'pythonjsonlogger|jsonlogger|json_logging|structlog'
    r'|JsonFormatter|JSONFormatter|json\.dumps.*log',
    re.IGNORECASE,
)

# LOG-003: Missing trace ID in log configuration
_RE_TRACE_ID_IN_LOG = re.compile(
    r'trace.?id|traceId|trace_id|otelTraceID|span.?id|spanId|span_id|otelSpanID'
    r'|correlation.?id|correlationId|request.?id|requestId',
    re.IGNORECASE,
)

# LOG-004: Console.log in production (Node.js)
_RE_CONSOLE_LOG = re.compile(
    r'^\s*console\.(log|warn|error|info|debug)\s*\(',
)

# LOG-005: Sensitive data in log output
_RE_SENSITIVE_LOG = re.compile(
    r'(?:log(?:ger)?|console)\.\w+\s*\([^)]*(?:password|secret|token|api.?key|credit.?card|ssn)\b',
    re.IGNORECASE,
)

def scan_logging_issues(file_path: Path, is_production: bool = True) -> list[LogViolation]:
    """Scan a file for logging quality issues."""
    violations = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    suffix = file_path.suffix.lower()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue

        # Python: print() instead of logger
        if suffix == ".py" and _RE_PRINT_LOGGING.search(line):
            violations.append(LogViolation(
                file=str(file_path), line=i+1,
                code="LOG-001", severity="warning",
                message="print() used instead of structured logger",
            ))

        # Node.js: console.log in production
        if suffix in (".js", ".ts", ".mjs") and _RE_CONSOLE_LOG.search(line):
            violations.append(LogViolation(
                file=str(file_path), line=i+1,
                code="LOG-004", severity="warning",
                message="console.log() used — prefer structured logger (winston/pino)",
            ))

        # Sensitive data in logs
        if _RE_SENSITIVE_LOG.search(line):
            violations.append(LogViolation(
                file=str(file_path), line=i+1,
                code="LOG-005", severity="error",
                message="Potential sensitive data in log output",
            ))

    return violations
```

### 3.4 Trace ID Propagation Verification Between Services

```python
# ============================================================
# Static analysis: verify services propagate trace context
# ============================================================

def check_trace_propagation(project_root: Path) -> list[LogViolation]:
    """Check that HTTP client calls include trace context propagation."""
    violations = []

    # Python: httpx/requests calls without header injection
    _RE_HTTP_CALL_PY = re.compile(
        r'(?:httpx|requests|aiohttp)\.(get|post|put|patch|delete)\s*\(',
    )
    _RE_HEADER_INJECT_PY = re.compile(
        r'TraceContextTextMapPropagator.*inject'
        r'|propagate.*inject'
        r'|traceparent.*header'
        r'|headers\s*\[.*trace',
        re.IGNORECASE | re.DOTALL,
    )

    # Node.js: axios/fetch calls without trace headers
    _RE_HTTP_CALL_JS = re.compile(
        r'(?:axios|fetch|got|superagent|request)\s*[\.(]',
    )
    _RE_HEADER_INJECT_JS = re.compile(
        r'traceparent|x-trace-id|x-request-id|propagation.*inject'
        r'|opentelemetry.*propagat',
        re.IGNORECASE,
    )

    # C#: HttpClient calls without trace propagation
    _RE_HTTP_CALL_CS = re.compile(
        r'HttpClient\s*\(\)|\.GetAsync\s*\(|\.PostAsync\s*\(|\.SendAsync\s*\(',
    )
    _RE_HEADER_INJECT_CS = re.compile(
        r'traceparent|ActivityTraceId|Activity\.Current'
        r'|Propagator\.Inject|DiagnosticSource',
        re.IGNORECASE,
    )

    for py_file in project_root.rglob("*.py"):
        if "test" in py_file.name.lower() or "node_modules" in str(py_file):
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if _RE_HTTP_CALL_PY.search(content) and not _RE_HEADER_INJECT_PY.search(content):
            violations.append(LogViolation(
                file=str(py_file), line=0,
                code="TRACE-001", severity="warning",
                message="HTTP client calls without trace context propagation",
            ))

    for js_file in project_root.rglob("*.ts"):
        if "test" in js_file.name.lower() or "node_modules" in str(js_file):
            continue
        content = js_file.read_text(encoding="utf-8", errors="ignore")
        if _RE_HTTP_CALL_JS.search(content) and not _RE_HEADER_INJECT_JS.search(content):
            violations.append(LogViolation(
                file=str(js_file), line=0,
                code="TRACE-001", severity="warning",
                message="HTTP client calls without trace context propagation",
            ))

    return violations


# ============================================================
# OpenTelemetry log output with trace/span IDs (JSON format)
# ============================================================
# Expected JSON log entry format:
# {
#     "body": "Processing request",
#     "severity_text": "INFO",
#     "trace_id": "0xdb1fc322141e64eb84f5bd8a8b1c6d1f",
#     "span_id": "0x5c2b0f851030d17d",
#     "trace_flags": 1,
#     "attributes": { "otelSpanID": "...", "otelTraceID": "..." },
#     "timestamp": "2023-10-10T08:14:32.631195Z"
# }

# Environment variables for Python OpenTelemetry log correlation:
# export OTEL_PYTHON_LOG_CORRELATION=true
# export OTEL_PYTHON_LOG_FORMAT="%(msg)s [span_id=%(span_id)s]"
# export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
```

---

## 4. Secret Scanning

### 4.1 detect-secrets (Yelp) — Python API

```python
from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings, transient_settings
import json

# ============================================================
# Basic scan with default plugins
# ============================================================
secrets = SecretsCollection()
with default_settings():
    secrets.scan_file('config.yaml')
    secrets.scan_file('.env')
    secrets.scan_file('docker-compose.yml')

# Output results as JSON
results = secrets.json()
print(json.dumps(results, indent=2))
# Output format:
# {
#   "config.yaml": [
#     {
#       "hashed_secret": "513e0a36963ae1e8431c041b744679ee578b7c44",
#       "is_verified": false,
#       "line_number": 45,
#       "type": "Private Key"
#     }
#   ]
# }


# ============================================================
# Custom plugin configuration for targeted scanning
# ============================================================
secrets = SecretsCollection()
with transient_settings({
    'plugins_used': [
        {'name': 'AWSKeyDetector'},
        {'name': 'PrivateKeyDetector'},
        {'name': 'BasicAuthDetector'},
        {'name': 'Base64HighEntropyString', 'limit': 4.5},
        {'name': 'HexHighEntropyString', 'limit': 3.0},
        {'name': 'KeywordDetector'},
        {'name': 'JwtTokenDetector'},
    ],
}) as settings:
    # Disable filters that cause false negatives
    settings.disable_filters(
        'detect_secrets.filters.heuristic.is_prefixed_with_dollar_sign',
        'detect_secrets.filters.heuristic.is_likely_id_string',
    )
    secrets.scan_file('app/settings.py')

# Built-in plugin list (detect-secrets v1.x):
# - AWSKeyDetector
# - ArtifactoryDetector
# - AzureStorageKeyDetector
# - Base64HighEntropyString
# - BasicAuthDetector
# - CloudantDetector
# - DiscordBotTokenDetector
# - GitHubTokenDetector
# - HexHighEntropyString
# - IbmCloudIamDetector
# - IbmCosHmacDetector
# - JwtTokenDetector
# - KeywordDetector
# - MailchimpDetector
# - NpmDetector
# - PrivateKeyDetector
# - SendGridDetector
# - SlackDetector
# - SoftlayerDetector
# - SquareOAuthDetector
# - StripeDetector
# - TwilioKeyDetector


# ============================================================
# CLI usage (for subprocess integration)
# ============================================================
# detect-secrets scan > .secrets.baseline
# detect-secrets scan --all-files --force-use-all-plugins > .secrets.baseline
# detect-secrets scan --list-all-plugins
# detect-secrets audit .secrets.baseline
```

### 4.2 TruffleHog CLI Usage

```bash
# Scan local filesystem
trufflehog filesystem path/to/project/

# Scan Git repository
trufflehog git file://path/to/repo --since-commit HEAD~10
trufflehog git https://github.com/org/repo.git

# Scan with custom config (regex patterns)
trufflehog filesystem /tmp --config=config.yaml

# JSON output for parsing
trufflehog filesystem path/to/project/ --json

# Only verified secrets
trufflehog filesystem path/to/project/ --only-verified
```

**TruffleHog custom config (YAML):**
```yaml
# config.yaml for trufflehog
detectors:
  - name: custom_api_key
    keywords:
      - api_key
      - apikey
    regex:
      adjective: '[A-Za-z0-9]{32,}'
    verify:
      - endpoint: https://api.example.com/verify
        unsafe: true
        headers:
          - "Authorization: Bearer {adjective.0}"
```

### 4.3 Custom Secret Detection Regex Patterns

```python
import re

# ============================================================
# SECRET SCANNING REGEX PATTERNS
# For static analysis of source code
# ============================================================

_SECRET_PATTERNS = {
    # SEC-SECRET-001: AWS Access Keys
    "SEC-SECRET-001": {
        "name": "AWS Access Key",
        "severity": "critical",
        "regex": re.compile(r'(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}'),
    },
    # SEC-SECRET-002: AWS Secret Key
    "SEC-SECRET-002": {
        "name": "AWS Secret Key",
        "severity": "critical",
        "regex": re.compile(
            r'''(?i)(?:aws)?_?(?:secret)?_?(?:access)?_?key\s*[:=]\s*['"]?([A-Za-z0-9/+=]{40})['"]?'''
        ),
    },
    # SEC-SECRET-003: Private Keys (RSA, DSA, EC, PGP)
    "SEC-SECRET-003": {
        "name": "Private Key",
        "severity": "critical",
        "regex": re.compile(
            r'-----BEGIN\s+(?:RSA|DSA|EC|PGP|OPENSSH)?\s*PRIVATE\s+KEY'
        ),
    },
    # SEC-SECRET-004: Generic API Key assignment
    "SEC-SECRET-004": {
        "name": "Generic API Key",
        "severity": "high",
        "regex": re.compile(
            r'''(?i)(?:api[_-]?key|apikey|api_secret)\s*[:=]\s*['"]([a-z0-9]{20,})['"]'''
        ),
    },
    # SEC-SECRET-005: Database connection strings with passwords
    "SEC-SECRET-005": {
        "name": "Database Connection String",
        "severity": "critical",
        "regex": re.compile(
            r'''(?i)(?:mysql|postgres|postgresql|mongodb|redis|mssql)://[^:]+:([^@\s]+)@'''
        ),
    },
    # SEC-SECRET-006: Bearer tokens hardcoded
    "SEC-SECRET-006": {
        "name": "Hardcoded Bearer Token",
        "severity": "high",
        "regex": re.compile(
            r'''(?i)(?:bearer|authorization)\s*[:=]\s*['"]?(?:Bearer\s+)?([a-zA-Z0-9._-]{20,})['"]?'''
        ),
    },
    # SEC-SECRET-007: Generic password assignment
    "SEC-SECRET-007": {
        "name": "Hardcoded Password",
        "severity": "high",
        "regex": re.compile(
            r'''(?i)(?:password|passwd|pwd|pass)\s*[:=]\s*['"]([^'"]{8,})['"]'''
        ),
    },
    # SEC-SECRET-008: GitHub/GitLab tokens
    "SEC-SECRET-008": {
        "name": "GitHub/GitLab Token",
        "severity": "critical",
        "regex": re.compile(
            r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}'  # GitHub PAT
            r'|glpat-[A-Za-z0-9_-]{20,}'                     # GitLab PAT
        ),
    },
    # SEC-SECRET-009: Stripe keys
    "SEC-SECRET-009": {
        "name": "Stripe Key",
        "severity": "critical",
        "regex": re.compile(
            r'(?:sk|pk)_(?:test|live)_[A-Za-z0-9]{20,}'
        ),
    },
    # SEC-SECRET-010: JWT tokens hardcoded
    "SEC-SECRET-010": {
        "name": "Hardcoded JWT",
        "severity": "high",
        "regex": re.compile(
            r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
        ),
    },
    # SEC-SECRET-011: Slack webhook/token
    "SEC-SECRET-011": {
        "name": "Slack Token",
        "severity": "high",
        "regex": re.compile(
            r'xox[baprs]-[0-9]{10,}-[a-zA-Z0-9-]+'
            r'|https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[a-zA-Z0-9]+'
        ),
    },
    # SEC-SECRET-012: SendGrid API Key
    "SEC-SECRET-012": {
        "name": "SendGrid Key",
        "severity": "critical",
        "regex": re.compile(r'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}'),
    },
}

# Files to skip (binary, generated, vendor)
_SECRET_SCAN_SKIP_PATTERNS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    ".min.js", ".min.css", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", ".secrets.baseline",
}

_SECRET_SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".cs", ".java", ".go",
    ".rb", ".php", ".yml", ".yaml", ".json", ".xml", ".toml",
    ".env", ".cfg", ".conf", ".ini", ".properties", ".sh",
    ".dockerfile", ".tf", ".hcl",
}

def scan_file_for_secrets(file_path: Path) -> list[dict]:
    """Scan a single file for hardcoded secrets."""
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return violations

    lines = content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        # Skip lines that reference env vars (not hardcoded)
        if re.search(r'os\.environ|process\.env|Environment\.GetEnvironmentVariable|\$\{', line):
            continue

        for code, pattern_info in _SECRET_PATTERNS.items():
            if pattern_info["regex"].search(line):
                violations.append({
                    "code": code,
                    "file": str(file_path),
                    "line": i + 1,
                    "name": pattern_info["name"],
                    "severity": pattern_info["severity"],
                })
    return violations
```

### 4.4 Docker Security Verification

```python
import re
from pathlib import Path

class DockerViolation(NamedTuple):
    file: str
    line: int
    code: str
    severity: str
    message: str

# ============================================================
# DOCKER-001: Running as root (no USER directive)
# ============================================================
def check_dockerfile_nonroot(dockerfile: Path) -> list[DockerViolation]:
    """Check that Dockerfile specifies a non-root user."""
    violations = []
    content = dockerfile.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    has_user_directive = False
    user_is_root = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper().startswith("USER "):
            has_user_directive = True
            user_value = stripped[5:].strip()
            if user_value in ("root", "0"):
                user_is_root = True
                violations.append(DockerViolation(
                    file=str(dockerfile), line=i+1,
                    code="DOCKER-001", severity="error",
                    message="USER directive explicitly sets root user",
                ))

    if not has_user_directive:
        violations.append(DockerViolation(
            file=str(dockerfile), line=0,
            code="DOCKER-001", severity="error",
            message="No USER directive — container runs as root by default",
        ))

    return violations


# ============================================================
# DOCKER-002: Secrets in Dockerfile (ENV with sensitive values)
# ============================================================
_RE_DOCKER_SECRET_ENV = re.compile(
    r'''^\s*ENV\s+\w*(?:PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY)\w*\s*=\s*\S+''',
    re.IGNORECASE | re.MULTILINE,
)

# ============================================================
# DOCKER-003: Using latest tag
# ============================================================
_RE_DOCKER_LATEST = re.compile(
    r'^\s*FROM\s+\S+:latest\b',
    re.MULTILINE | re.IGNORECASE,
)
_RE_DOCKER_NO_TAG = re.compile(
    r'^\s*FROM\s+(\S+)\s*$',
    re.MULTILINE,
)

# ============================================================
# DOCKER-004: COPY/ADD with overly broad context
# ============================================================
_RE_DOCKER_COPY_ALL = re.compile(
    r'^\s*(?:COPY|ADD)\s+\.\s+',
    re.MULTILINE,
)

# ============================================================
# DOCKER-005: No HEALTHCHECK directive
# ============================================================
def check_dockerfile_healthcheck(dockerfile: Path) -> list[DockerViolation]:
    """Check Dockerfile has a HEALTHCHECK instruction."""
    content = dockerfile.read_text(encoding="utf-8", errors="ignore")
    if "HEALTHCHECK" not in content.upper():
        return [DockerViolation(
            file=str(dockerfile), line=0,
            code="DOCKER-005", severity="warning",
            message="No HEALTHCHECK instruction — container health not monitored",
        )]
    return []


def scan_dockerfile(dockerfile: Path) -> list[DockerViolation]:
    """Comprehensive Dockerfile security scan."""
    violations = []
    content = dockerfile.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    violations.extend(check_dockerfile_nonroot(dockerfile))
    violations.extend(check_dockerfile_healthcheck(dockerfile))

    for i, line in enumerate(lines):
        if _RE_DOCKER_SECRET_ENV.match(line):
            violations.append(DockerViolation(
                file=str(dockerfile), line=i+1,
                code="DOCKER-002", severity="critical",
                message="Secret value in Dockerfile ENV — use build args or runtime secrets",
            ))
        if _RE_DOCKER_LATEST.match(line):
            violations.append(DockerViolation(
                file=str(dockerfile), line=i+1,
                code="DOCKER-003", severity="warning",
                message="Using :latest tag — pin to specific version for reproducibility",
            ))
        if _RE_DOCKER_NO_TAG.match(line):
            base = _RE_DOCKER_NO_TAG.match(line).group(1)
            if base not in ("scratch", "AS"):
                violations.append(DockerViolation(
                    file=str(dockerfile), line=i+1,
                    code="DOCKER-003", severity="warning",
                    message=f"FROM '{base}' without version tag — pin to specific version",
                ))
        if _RE_DOCKER_COPY_ALL.match(line):
            violations.append(DockerViolation(
                file=str(dockerfile), line=i+1,
                code="DOCKER-004", severity="warning",
                message="COPY . copies entire build context — use specific paths or .dockerignore",
            ))

    return violations


# ============================================================
# Docker Compose security checks
# ============================================================
def check_compose_security(compose_path: Path) -> list[DockerViolation]:
    """Check docker-compose.yml for security issues."""
    import yaml
    violations = []
    content = compose_path.read_text(encoding="utf-8", errors="ignore")
    try:
        compose = yaml.safe_load(content)
    except yaml.YAMLError:
        return violations

    if not isinstance(compose, dict):
        return violations

    services = compose.get("services", {})
    if not isinstance(services, dict):
        return violations

    for svc_name, svc_config in services.items():
        if not isinstance(svc_config, dict):
            continue

        # Check for privileged mode
        if svc_config.get("privileged", False):
            violations.append(DockerViolation(
                file=str(compose_path), line=0,
                code="DOCKER-006", severity="critical",
                message=f"Service '{svc_name}' runs in privileged mode",
            ))

        # Check for host network mode
        if svc_config.get("network_mode") == "host":
            violations.append(DockerViolation(
                file=str(compose_path), line=0,
                code="DOCKER-007", severity="warning",
                message=f"Service '{svc_name}' uses host network mode",
            ))

        # Check for capability additions
        cap_add = svc_config.get("cap_add", [])
        dangerous_caps = {"SYS_ADMIN", "NET_ADMIN", "ALL", "SYS_PTRACE"}
        for cap in cap_add:
            if cap.upper() in dangerous_caps:
                violations.append(DockerViolation(
                    file=str(compose_path), line=0,
                    code="DOCKER-008", severity="high",
                    message=f"Service '{svc_name}' adds dangerous capability: {cap}",
                ))

    return violations
```

---

## 5. Adversarial Review Patterns

### 5.1 Dead Event Detection (Published but Never Consumed)

```python
import re
from pathlib import Path
from collections import defaultdict

# ============================================================
# ADV-001: Events published but never consumed
# ============================================================

def detect_dead_events(project_root: Path) -> list[dict]:
    """Find events that are published/emitted but never subscribed/consumed."""
    publishers: dict[str, list[str]] = defaultdict(list)  # event_name -> [publisher_files]
    consumers: dict[str, list[str]] = defaultdict(list)   # event_name -> [consumer_files]

    # Event name extraction patterns (multi-framework)
    _RE_PUBLISH_PATTERNS = [
        # Python: emit, publish, send_event, dispatch
        re.compile(r'''(?:emit|publish|send_event|dispatch|fire|trigger)\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        # Node.js: EventEmitter.emit, rabbitmq publish
        re.compile(r'''\.emit\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        re.compile(r'''publish\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        # C#: RaiseEvent, Publish, Emit
        re.compile(r'''(?:RaiseEvent|Publish|Emit)\s*[<(]\s*(?:new\s+)?(\w+Event)\b'''),
        re.compile(r'''IMediator.*\.Publish\s*\(\s*new\s+(\w+)\s*\('''),
    ]

    _RE_CONSUME_PATTERNS = [
        # Python: on, subscribe, handle, listen
        re.compile(r'''(?:on|subscribe|handle|listen|register_handler)\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        re.compile(r'''@(?:event_handler|subscriber|on_event)\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        # Node.js: .on, .once, .addListener
        re.compile(r'''\.(?:on|once|addListener|addEventListener)\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        re.compile(r'''subscribe\s*\(\s*['"]([a-zA-Z0-9_.:-]+)['"]'''),
        # C#: INotificationHandler, IRequestHandler
        re.compile(r'''INotificationHandler\s*<\s*(\w+Event?)>'''),
        re.compile(r'''Handle\s*\(\s*(\w+Event)\s+'''),
    ]

    source_extensions = {".py", ".js", ".ts", ".cs", ".java", ".go"}

    for file_path in project_root.rglob("*"):
        if file_path.suffix not in source_extensions:
            continue
        if any(skip in str(file_path) for skip in ("node_modules", ".git", "__pycache__", "test")):
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for pattern in _RE_PUBLISH_PATTERNS:
            for match in pattern.finditer(content):
                event_name = match.group(1)
                publishers[event_name].append(str(file_path))

        for pattern in _RE_CONSUME_PATTERNS:
            for match in pattern.finditer(content):
                event_name = match.group(1)
                consumers[event_name].append(str(file_path))

    # Find published events with no consumers
    dead_events = []
    for event_name, pub_files in publishers.items():
        if event_name not in consumers:
            dead_events.append({
                "code": "ADV-001",
                "severity": "warning",
                "event": event_name,
                "published_in": list(set(pub_files)),
                "message": f"Event '{event_name}' is published but never consumed",
            })

    return dead_events
```

### 5.2 Dead Contract Detection (Defined but Never Implemented)

```python
# ============================================================
# ADV-002: Contracts/interfaces defined but never implemented
# ============================================================

def detect_dead_contracts(project_root: Path) -> list[dict]:
    """Find interfaces/abstract classes that are never implemented."""
    definitions: dict[str, str] = {}    # interface_name -> defining_file
    implementations: set[str] = set()   # interface_name set

    # Interface/abstract class definitions
    _RE_INTERFACE_DEF = [
        # TypeScript: interface Foo { ... } or abstract class Foo
        re.compile(r'''(?:export\s+)?interface\s+(\w+)\s*(?:extends\s+\w+\s*)?\{'''),
        re.compile(r'''(?:export\s+)?abstract\s+class\s+(\w+)'''),
        # Python: ABC, Protocol
        re.compile(r'''class\s+(\w+)\s*\(.*(?:ABC|Protocol|metaclass\s*=\s*ABCMeta)\s*.*\)'''),
        # C#: interface keyword
        re.compile(r'''(?:public|internal|private)?\s*interface\s+(I\w+)'''),
        # Java: interface keyword
        re.compile(r'''(?:public|private|protected)?\s*interface\s+(\w+)'''),
    ]

    # Implementation patterns
    _RE_IMPLEMENTS = [
        # TypeScript: implements InterfaceName
        re.compile(r'''implements\s+(\w+)'''),
        re.compile(r'''class\s+\w+\s+implements\s+(\w+)'''),
        # Python: class Foo(InterfaceName)
        re.compile(r'''class\s+\w+\s*\(\s*(\w+)\s*\)'''),
        # C#: class Foo : IInterface
        re.compile(r'''class\s+\w+\s*:\s*(I\w+)'''),
        re.compile(r'''class\s+\w+\s*:\s*\w+\s*,\s*(I\w+)'''),
        # Java: implements
        re.compile(r'''implements\s+([\w,\s]+)'''),
    ]

    # Injection/usage patterns (DI containers)
    _RE_USAGE = [
        # TypeScript: @Inject(InterfaceName), constructor(private foo: InterfaceName)
        re.compile(r''':\s*(\w+)\s*[,\)]'''),
        # C#: services.AddScoped<IFoo, Foo>()
        re.compile(r'''Add(?:Scoped|Singleton|Transient)\s*<\s*(I\w+)'''),
        # Python: Depends(get_foo), typing: IFoo
        re.compile(r''':\s*(\w+)\s*=\s*Depends'''),
    ]

    source_extensions = {".py", ".js", ".ts", ".cs", ".java", ".go"}

    for file_path in project_root.rglob("*"):
        if file_path.suffix not in source_extensions:
            continue
        if any(skip in str(file_path) for skip in ("node_modules", ".git", "__pycache__")):
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for pattern in _RE_INTERFACE_DEF:
            for match in pattern.finditer(content):
                name = match.group(1)
                # Skip common framework interfaces
                if name in ("Component", "Module", "Injectable", "Controller", "Service"):
                    continue
                definitions[name] = str(file_path)

        for pattern in _RE_IMPLEMENTS + _RE_USAGE:
            for match in pattern.finditer(content):
                names = match.group(1).split(",")
                for name in names:
                    implementations.add(name.strip())

    dead_contracts = []
    for name, def_file in definitions.items():
        if name not in implementations:
            dead_contracts.append({
                "code": "ADV-002",
                "severity": "warning",
                "contract": name,
                "defined_in": def_file,
                "message": f"Interface/abstract '{name}' is defined but never implemented or used",
            })

    return dead_contracts
```

### 5.3 Orphan Service Detection

```python
# ============================================================
# ADV-003: Orphan services (services with no inbound/outbound connections)
# ============================================================

def detect_orphan_services(project_root: Path) -> list[dict]:
    """Find services in docker-compose that have no API routes or connections."""
    import yaml

    compose_files = list(project_root.glob("**/docker-compose*.yml")) + \
                    list(project_root.glob("**/docker-compose*.yaml"))

    all_services: dict[str, dict] = {}
    service_connections: dict[str, set[str]] = defaultdict(set)

    for compose_file in compose_files:
        try:
            data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        services = data.get("services", {})
        if not isinstance(services, dict):
            continue

        for svc_name, svc_config in services.items():
            if not isinstance(svc_config, dict):
                continue
            all_services[svc_name] = svc_config

            # Check depends_on
            depends = svc_config.get("depends_on", [])
            if isinstance(depends, dict):
                depends = list(depends.keys())
            elif isinstance(depends, str):
                depends = [depends]
            for dep in depends:
                service_connections[svc_name].add(dep)
                service_connections[dep].add(svc_name)

            # Check links
            links = svc_config.get("links", [])
            for link in links:
                linked_svc = link.split(":")[0]
                service_connections[svc_name].add(linked_svc)
                service_connections[linked_svc].add(svc_name)

            # Check environment for service references
            env = svc_config.get("environment", {})
            if isinstance(env, list):
                env_str = " ".join(env)
            elif isinstance(env, dict):
                env_str = " ".join(str(v) for v in env.values())
            else:
                env_str = ""
            for other_svc in services:
                if other_svc != svc_name and other_svc in env_str:
                    service_connections[svc_name].add(other_svc)
                    service_connections[other_svc].add(svc_name)

    orphans = []
    infrastructure_services = {"redis", "postgres", "postgresql", "mysql", "mariadb",
                                "mongo", "mongodb", "rabbitmq", "kafka", "zookeeper",
                                "elasticsearch", "minio", "mailhog", "traefik", "nginx"}

    for svc_name in all_services:
        if svc_name.lower() in infrastructure_services:
            continue
        if svc_name not in service_connections or len(service_connections[svc_name]) == 0:
            orphans.append({
                "code": "ADV-003",
                "severity": "warning",
                "service": svc_name,
                "message": f"Service '{svc_name}' has no connections to other services",
            })

    return orphans
```

### 5.4 Cross-Boundary Naming Consistency

```python
# ============================================================
# ADV-004: Inconsistent naming conventions across boundaries
# ============================================================

_NAMING_CONVENTIONS = {
    "camelCase": re.compile(r'^[a-z][a-zA-Z0-9]*$'),
    "PascalCase": re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
    "snake_case": re.compile(r'^[a-z][a-z0-9_]*$'),
    "kebab-case": re.compile(r'^[a-z][a-z0-9-]*$'),
    "SCREAMING_SNAKE": re.compile(r'^[A-Z][A-Z0-9_]*$'),
}

def detect_naming_convention(name: str) -> str:
    """Detect the naming convention of a given identifier."""
    for conv_name, pattern in _NAMING_CONVENTIONS.items():
        if pattern.match(name):
            return conv_name
    return "mixed"


def check_api_naming_consistency(project_root: Path) -> list[dict]:
    """Check that API field names are consistent across frontend/backend boundaries."""
    violations = []

    # Extract API response field names from backend
    _RE_JSON_FIELD_PY = re.compile(r'''['"](\w{2,})['"]:\s*(?:self\.|data\.|item\.)''')
    _RE_JSON_FIELD_CS = re.compile(r'''(?:public|private)\s+\w+\s+(\w+)\s*\{''')
    _RE_JSON_FIELD_JS = re.compile(r'''(\w{2,})\s*:\s*(?:req\.|res\.|data\.|item\.)''')

    # Extract frontend model/interface field names
    _RE_FRONTEND_FIELD = re.compile(r'''(\w{2,})\s*[?]?\s*:\s*(?:string|number|boolean|Date|any|\w+\[\])''')

    backend_fields: dict[str, str] = {}   # field_name -> convention
    frontend_fields: dict[str, str] = {}  # field_name -> convention

    backend_dirs = ["backend", "server", "api", "src/api", "app"]
    frontend_dirs = ["frontend", "client", "src/app", "src/components", "web"]

    for file_path in project_root.rglob("*"):
        if file_path.suffix not in (".py", ".cs", ".ts", ".js"):
            continue
        if "node_modules" in str(file_path) or ".git" in str(file_path):
            continue

        rel = str(file_path.relative_to(project_root)).replace("\\", "/").lower()
        is_backend = any(rel.startswith(d) for d in backend_dirs)
        is_frontend = any(rel.startswith(d) for d in frontend_dirs)

        if not is_backend and not is_frontend:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if is_backend:
            for pattern in [_RE_JSON_FIELD_PY, _RE_JSON_FIELD_CS, _RE_JSON_FIELD_JS]:
                for match in pattern.finditer(content):
                    field = match.group(1)
                    backend_fields[field] = detect_naming_convention(field)

        if is_frontend:
            for match in _RE_FRONTEND_FIELD.finditer(content):
                field = match.group(1)
                frontend_fields[field] = detect_naming_convention(field)

    # Check for fields that exist in both but with different conventions
    # e.g., backend uses snake_case "user_name" but frontend uses camelCase "userName"
    # This is a simplified check — production version needs field mapping
    backend_conventions = set(backend_fields.values()) - {"mixed"}
    frontend_conventions = set(frontend_fields.values()) - {"mixed"}

    if backend_conventions and frontend_conventions:
        if backend_conventions != frontend_conventions:
            violations.append({
                "code": "ADV-004",
                "severity": "info",
                "message": f"Naming convention mismatch: backend uses {backend_conventions}, "
                           f"frontend uses {frontend_conventions}. "
                           f"Ensure consistent serialization settings.",
                "backend_sample": dict(list(backend_fields.items())[:5]),
                "frontend_sample": dict(list(frontend_fields.items())[:5]),
            })

    return violations
```

### 5.5 Missing Error Handling Detection

```python
# ============================================================
# ADV-005: Missing error handling / unhandled promise rejections
# ============================================================

_ERROR_HANDLING_PATTERNS = {
    # ADV-005a: Async/await without try-catch (JavaScript/TypeScript)
    "async_no_catch_js": {
        "detect": re.compile(r'async\s+(?:function\s+)?\w+\s*\([^)]*\)\s*\{', re.MULTILINE),
        "guard": re.compile(r'try\s*\{|\.catch\s*\(|catchError|handleError', re.MULTILINE),
        "code": "ADV-005",
        "severity": "warning",
        "langs": {".js", ".ts", ".jsx", ".tsx"},
        "message": "Async function without try-catch or .catch() error handling",
    },
    # ADV-005b: Promise without .catch() (JavaScript)
    "promise_no_catch": {
        "detect": re.compile(r'\.then\s*\(\s*(?:async\s*)?\(?', re.MULTILINE),
        "guard": re.compile(r'\.catch\s*\(|\.finally\s*\(', re.MULTILINE),
        "code": "ADV-005",
        "severity": "warning",
        "langs": {".js", ".ts"},
        "message": "Promise chain without .catch() handler",
    },
    # ADV-005c: Python bare except
    "bare_except_py": {
        "detect": re.compile(r'^\s*except\s*:', re.MULTILINE),
        "guard": None,  # Always a violation
        "code": "ADV-005",
        "severity": "warning",
        "langs": {".py"},
        "message": "Bare except: catches all exceptions including SystemExit/KeyboardInterrupt",
    },
    # ADV-005d: C# empty catch block
    "empty_catch_cs": {
        "detect": re.compile(r'catch\s*(?:\([^)]*\))?\s*\{\s*\}', re.MULTILINE),
        "guard": None,
        "code": "ADV-005",
        "severity": "warning",
        "langs": {".cs", ".java"},
        "message": "Empty catch block — exception silently swallowed",
    },
}

def scan_error_handling(file_path: Path) -> list[dict]:
    """Scan for missing or inadequate error handling."""
    violations = []
    suffix = file_path.suffix.lower()
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations

    for pattern_name, config in _ERROR_HANDLING_PATTERNS.items():
        if suffix not in config["langs"]:
            continue
        matches = list(config["detect"].finditer(content))
        if not matches:
            continue

        if config["guard"] is None:
            # Every match is a violation
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                violations.append({
                    "code": config["code"],
                    "file": str(file_path),
                    "line": line_num,
                    "severity": config["severity"],
                    "message": config["message"],
                })
        else:
            # Check if guard pattern exists in the function scope
            for match in matches:
                # Get the function body (next 50 lines)
                start = match.start()
                func_block = content[start:start+2000]
                if not config["guard"].search(func_block):
                    line_num = content[:start].count("\n") + 1
                    violations.append({
                        "code": config["code"],
                        "file": str(file_path),
                        "line": line_num,
                        "severity": config["severity"],
                        "message": config["message"],
                    })

    return violations
```

### 5.6 Race Condition Detection in Event Processing

```python
# ============================================================
# ADV-006: Potential race conditions in event/message processing
# ============================================================

_RACE_CONDITION_PATTERNS = [
    # Shared mutable state without locking
    {
        "code": "ADV-006",
        "severity": "warning",
        "detect": re.compile(
            r'''(?:global|class)\s+\w+.*?(?:dict|list|set|counter|queue)\s*=''',
            re.IGNORECASE | re.DOTALL,
        ),
        "guard": re.compile(
            r'Lock\s*\(|Semaphore\s*\(|synchronized|mutex|RLock|asyncio\.Lock'
            r'|threading\.Lock|Mutex|lock\s*\(',
            re.IGNORECASE,
        ),
        "message": "Shared mutable state without lock/mutex — potential race condition",
        "langs": {".py", ".js", ".ts", ".cs", ".java"},
    },
    # Read-modify-write without atomicity (e.g., counter += 1)
    {
        "code": "ADV-006",
        "severity": "info",
        "detect": re.compile(
            r'''(?:self\.|this\.)\w+\s*(?:\+=|\-=|\*=|/=|%=)\s*''',
        ),
        "guard": re.compile(
            r'Lock\s*\(|atomic|Interlocked|synchronized|@synchronized'
            r'|Atomic(?:Integer|Long|Reference)',
            re.IGNORECASE,
        ),
        "message": "Read-modify-write on instance variable — consider atomicity",
        "langs": {".py", ".cs", ".java"},
    },
    # Event handler modifying shared database record without optimistic concurrency
    {
        "code": "ADV-006",
        "severity": "warning",
        "detect": re.compile(
            r'''(?:@on_event|@subscriber|\.on\s*\()\s*.*?(?:\.update\s*\(|\.save\s*\(|SaveChanges)''',
            re.DOTALL,
        ),
        "guard": re.compile(
            r'ConcurrencyStamp|RowVersion|optimistic|version|ETag|If-Match',
            re.IGNORECASE,
        ),
        "message": "Event handler modifies database without optimistic concurrency control",
        "langs": {".py", ".cs", ".ts", ".js"},
    },
]

def scan_race_conditions(file_path: Path) -> list[dict]:
    """Scan for potential race conditions in event processing code."""
    violations = []
    suffix = file_path.suffix.lower()
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations

    for pattern in _RACE_CONDITION_PATTERNS:
        if suffix not in pattern["langs"]:
            continue
        if pattern["detect"].search(content) and not pattern["guard"].search(content):
            violations.append({
                "code": pattern["code"],
                "file": str(file_path),
                "severity": pattern["severity"],
                "message": pattern["message"],
            })

    return violations
```

---

## 6. Health Endpoint Verification

```python
# ============================================================
# HEALTH-001: Health endpoint detection and verification
# ============================================================

_RE_HEALTH_ENDPOINT = [
    # FastAPI
    re.compile(r'''@(?:app|router)\.(get|head)\s*\(\s*['"]/(health|healthz|ready|alive|status)['"]''', re.IGNORECASE),
    # Express
    re.compile(r'''(?:app|router)\.(get|head)\s*\(\s*['"]/(health|healthz|ready|alive|status)['"]''', re.IGNORECASE),
    # ASP.NET
    re.compile(r'''MapHealthChecks\s*\(\s*['"]/(health|healthz|ready)['"]''', re.IGNORECASE),
    re.compile(r'''MapGet\s*\(\s*['"]/(health|healthz|ready|alive|status)['"]''', re.IGNORECASE),
    # Django
    re.compile(r'''path\s*\(\s*['"](?:api/)?(?:health|healthz|ready|alive|status)/?['"]''', re.IGNORECASE),
]

def check_health_endpoints(project_root: Path) -> list[dict]:
    """Verify that each service has a health endpoint."""
    violations = []
    service_dirs = []

    # Detect service boundaries
    for compose_file in project_root.rglob("docker-compose*.yml"):
        try:
            import yaml
            data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("services"), dict):
                for svc_name, svc_config in data["services"].items():
                    if isinstance(svc_config, dict) and "build" in svc_config:
                        build = svc_config["build"]
                        if isinstance(build, str):
                            service_dirs.append((svc_name, project_root / build))
                        elif isinstance(build, dict) and "context" in build:
                            service_dirs.append((svc_name, project_root / build["context"]))
        except (yaml.YAMLError, OSError):
            continue

    for svc_name, svc_dir in service_dirs:
        if not svc_dir.is_dir():
            continue
        has_health = False
        for file_path in svc_dir.rglob("*"):
            if file_path.suffix not in (".py", ".js", ".ts", ".cs", ".java", ".go"):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in _RE_HEALTH_ENDPOINT:
                if pattern.search(content):
                    has_health = True
                    break
            if has_health:
                break

        if not has_health:
            violations.append({
                "code": "HEALTH-001",
                "severity": "warning",
                "service": svc_name,
                "directory": str(svc_dir),
                "message": f"Service '{svc_name}' has no health endpoint (/health, /healthz, /ready)",
            })

    return violations
```

---

## 7. Gitleaks Configuration Reference

**TOML configuration for custom secret rules:**
```toml
# .gitleaks.toml — Extend default rules + add custom ones

[extend]
useDefault = true
# Optionally disable noisy defaults
disabledRules = ["generic-api-key"]

# Custom: Company-specific API key pattern
[[rules]]
id = "company-internal-key"
description = "Internal API key"
regex = '''COMP_[A-Z0-9]{40}'''
keywords = ["COMP_"]
tags = ["company", "api"]

# Custom: Database connection string
[[rules]]
id = "db-connection-string"
description = "Database connection string with password"
regex = '''(?i)(?:mysql|postgres|mongodb)://[^:]+:([^@]+)@'''
secretGroup = 1
keywords = ["mysql://", "postgres://", "mongodb://"]
tags = ["database"]

# Custom: Hardcoded JWT secret
[[rules]]
id = "jwt-secret-hardcoded"
description = "Hardcoded JWT signing secret"
regex = '''(?i)jwt[_-]?secret\s*[:=]\s*['"][^'"]{8,}['"]'''
keywords = ["jwt_secret", "JWT_SECRET", "jwt-secret"]
tags = ["jwt", "auth"]

# Allowlist: Exclude test files and examples
[extend.allowlists]
paths = ["**/test/**", "**/tests/**", "**/*.test.*", "**/mock/**", "**/fixture/**"]
```

---

## 8. Version Compatibility Notes

| Library | Minimum Version | Recommended | Notes |
|---------|----------------|-------------|-------|
| PyJWT | 2.0+ | 2.8+ | v2 requires `algorithms` param (breaking from v1) |
| python-jose | 3.3+ | 3.3.0 | JWE support, `options` dict format |
| OpenTelemetry Python SDK | 1.20+ | 1.25+ | Stable logs API from 1.24 |
| detect-secrets (Yelp) | 1.4+ | 1.5+ | SecretsCollection API, transient_settings |
| detect-secrets (IBM fork) | 0.13+ | 0.13.1+ | Additional plugins (IBM Cloud, DB2) |
| TruffleHog | 3.0+ | 3.80+ | v3 is Go rewrite, filesystem scanning |
| Gitleaks | 8.0+ | 8.18+ | TOML config format, extend.useDefault |
| httpx | 0.24+ | 0.27+ | Async client, HTTP/2 support |

---

## 9. Integration Summary — Scan Code Map

| Scan Code | Category | Severity | Detection Method |
|-----------|----------|----------|------------------|
| SEC-001 | JWT Auth | error | Endpoint without auth middleware/decorator |
| SEC-002 | JWT Config | critical | Algorithm set to 'none' |
| SEC-003 | JWT Config | critical | Signature verification disabled |
| SEC-004 | JWT Config | high | Expiration check disabled |
| SEC-005 | JWT Config | critical | Hardcoded JWT secret |
| SEC-006 | JWT Config | high | HS256 with public key (algorithm confusion) |
| CORS-001 | CORS | error | Wildcard origin (*) |
| CORS-002 | CORS | critical | Credentials with wildcard origin |
| CORS-003 | CORS | high | Dynamic origin reflection without validation |
| LOG-001 | Logging | warning | print() instead of structured logger |
| LOG-004 | Logging | warning | console.log() in production code |
| LOG-005 | Logging | error | Sensitive data in log output |
| TRACE-001 | Observability | warning | HTTP calls without trace context propagation |
| SEC-SECRET-001..012 | Secrets | critical/high | Hardcoded secrets (AWS, keys, passwords, tokens) |
| DOCKER-001 | Docker | error | Container runs as root |
| DOCKER-002 | Docker | critical | Secrets in Dockerfile ENV |
| DOCKER-003 | Docker | warning | Unpinned base image tag |
| DOCKER-004 | Docker | warning | COPY . (broad context) |
| DOCKER-005 | Docker | warning | No HEALTHCHECK instruction |
| DOCKER-006 | Docker | critical | Privileged mode enabled |
| DOCKER-007 | Docker | warning | Host network mode |
| DOCKER-008 | Docker | high | Dangerous Linux capabilities |
| ADV-001 | Adversarial | warning | Events published but never consumed |
| ADV-002 | Adversarial | warning | Contracts defined but never implemented |
| ADV-003 | Adversarial | warning | Orphan services (no connections) |
| ADV-004 | Adversarial | info | Cross-boundary naming inconsistency |
| ADV-005 | Adversarial | warning | Missing error handling |
| ADV-006 | Adversarial | warning | Potential race conditions |
| HEALTH-001 | Health | warning | Missing health endpoint |

**Total: 30 scan codes across 7 categories**

---

## 10. Key Implementation Decisions for Build 3

1. **All scans are static analysis** — no running services required. The httpx CORS check (Section 2.2) is the only runtime verification and is optional.

2. **detect-secrets Python API** is preferred over CLI for programmatic integration. Use `SecretsCollection` + `default_settings()` context manager.

3. **TruffleHog** is CLI-only (Go binary). If integrated, use `subprocess.run(["trufflehog", "filesystem", path, "--json"])` and parse JSON output.

4. **Gitleaks** is also CLI-only (Go binary). Use TOML config for custom rules. Parse JSON output from `gitleaks detect --report-format json`.

5. **OpenTelemetry trace verification** is primarily static analysis (checking for propagator usage in code). Runtime trace ID verification requires a running system.

6. **Adversarial review patterns** (ADV-001..006) are heuristic — they will produce false positives. Severity should be "warning" or "info", never blocking.

7. **Docker security scans** require YAML parsing (PyYAML). Already a dependency in the agent-team codebase.

8. **Framework detection** reuses `detect_app_type()` from e2e_testing.py to determine which auth/CORS patterns to apply.
