# AUDIT: Security Scanning Technical Review — Build 3 PRD

**Reviewer:** Security Scanning Technical Reviewer
**Date:** 2026-02-14
**Scope:** BUILD3_PRD.md (M4 Quality Gate), BUILD3_TECH_SECURITY_OBS.md, cross-references from BUILD1/BUILD2
**Method:** Context7 library research + line-by-line regex verification + cross-build consistency

---

## Executive Summary

The Build 3 PRD defines 40 scan codes across 8 categories. The overall security scanning architecture is sound. However, I found **1 HIGH**, **5 MEDIUM**, and **8 LOW** severity issues. Most issues are regex pattern gaps where the PRD patterns are narrower than the tech research reference patterns. No CRITICAL issues were found.

**Verdict: PASS WITH FIXES** — All HIGH/MEDIUM issues should be corrected before implementation.

---

## 1. detect-secrets Verification

### Context7 Research Findings

Library: `/yelp/detect-secrets` (71 snippets, High reputation)

**Confirmed API:**
- `SecretsCollection` is the main scanning interface (NOT `scan_file()` standalone)
- `scan_file()` is a METHOD on `SecretsCollection`, not `detect_secrets.core.scan.scan_file()`
- `transient_settings()` context manager from `detect_secrets.settings` — CONFIRMED
- `default_settings()` context manager also available — CONFIRMED
- Plugin names confirmed: `HexHighEntropyString`, `Base64HighEntropyString`, `AWSKeyDetector`, `PrivateKeyDetector`, `JwtTokenDetector`, `KeywordDetector`, `SlackDetector`, `StripeDetector`, `SendGridDetector`, `GitHubTokenDetector`
- Baseline format: JSON dict keyed by filename with hashed_secret, line_number, type
- Programmatic usage pattern:
  ```python
  secrets = SecretsCollection()
  with transient_settings({
      'plugins_used': [{'name': 'AWSKeyDetector'}, ...],
  }) as settings:
      settings.disable_filters(...)
      secrets.scan_file('path')
  ```

### PRD Assessment

| Claim | Status | Notes |
|-------|--------|-------|
| detect-secrets 1.5+ listed in tech stack (line 21) | MISLEADING | Listed but never used in any REQ |
| transient_settings mentioned in tech stack | CORRECT | API confirmed by Context7 |
| Python API with SecretsCollection | NOT USED | PRD uses custom regex patterns instead |
| Plugin system (HexHighEntropyString, etc.) | NOT USED | PRD uses SEC-SECRET-001..012 custom regex |

**FINDING-SEC-01 (LOW):** detect-secrets is listed in the Technology Stack (line 21) but no REQ, TECH, or WIRE requirement actually uses it. The PRD chose custom regex patterns (SEC-SECRET-001..012) for secret scanning instead. The tech research doc (Section 10, point 2) says "detect-secrets Python API is preferred over CLI for programmatic integration" but the PRD ignores this recommendation.

**Recommendation:** Either:
1. Remove detect-secrets from the Technology Stack since it's not used, OR
2. Add an optional detect-secrets integration as a secondary scanning pass in `SecurityScanner.scan_secrets()` using `SecretsCollection` + `default_settings()`

---

## 2. PyJWT Verification

### Context7 Research Findings

Library: `/jpadilla/pyjwt` (141 snippets, Score: 93.4)

**Confirmed API:**
```python
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,      # CONFIRMED
    InvalidAudienceError,       # CONFIRMED
    InvalidIssuerError,         # CONFIRMED
    InvalidSignatureError,      # CONFIRMED
    MissingRequiredClaimError,  # CONFIRMED
    DecodeError,                # CONFIRMED
)

# Correct decode call:
payload = jwt.decode(
    token,
    key,
    algorithms=["HS256"],           # REQUIRED - mandatory param
    audience="my-app",              # Validates aud claim
    issuer="https://auth.example.com",  # Validates iss claim
    leeway=5,                       # Clock skew tolerance
    options={                       # Options dict format
        "require": ["exp", "iss"],  # Require specific claims
        "verify_signature": True,   # Default True
        "verify_exp": True,         # Default: matches verify_signature
    },
)
```

**Key insight from Context7:** In PyJWT 2.x, verification toggles are inside an `options` dict parameter, not keyword arguments. The pattern is `options={"verify_exp": False}` not `verify_exp=False`.

### PRD Pattern Analysis

| Scan Code | PRD Pattern (REQ-034/035) | Issue |
|-----------|--------------------------|-------|
| SEC-001 | `@(?:app\|router)\.(?:get\|post\|put\|patch\|delete)\s*\(` without `Depends\(.*auth` within 10 lines | CORRECT — proper FastAPI auth detection |
| SEC-002 | `algorithms=["none"]` or `algorithms=['none']` | CORRECT — catches algorithm none attack |
| SEC-003 | `verify_signature:\s*False` or `verify_signature=False` | **ISSUE** — see below |
| SEC-004 | `verify_exp:\s*False` or `verify_exp=False` | **ISSUE** — see below |
| SEC-005 | `jwt\.(?:encode\|decode)\(.+["'][A-Za-z0-9_\-]{20,}["']` | ACCEPTABLE — greedy `.+` risk (see LOW) |
| SEC-006 | `algorithms=["HS256"]` with "public" or "pub_key" variable | CORRECT heuristic |

**FINDING-SEC-02 (MEDIUM): SEC-003 regex misses PyJWT options dict format.**

PRD REQ-034 pattern: `verify_signature:\s*False` or `verify_signature=False`

This catches:
- YAML config: `verify_signature: False`
- Keyword arg: `verify_signature=False`

But MISSES the actual PyJWT 2.x usage pattern:
- `options={"verify_signature": False}` — dict key with quotes
- `"verify_signature": False` — JSON/dict format
- `'verify_signature': False` — single-quoted dict key

The tech research doc (line 254) has the correct pattern: `verify_signature['"]\s*:\s*False` which catches quoted dict keys.

**Fix:** Change SEC-003 regex to:
```
(?:verify_signature|['"]verify_signature['"])\s*[:=]\s*False
```
Or use the tech research pattern: `verify_signature['"]\s*:\s*False|verify_signature\s*=\s*False`

**FINDING-SEC-03 (MEDIUM): SEC-004 has identical gap.**

Same issue as SEC-003 — `verify_exp:\s*False` misses `"verify_exp": False` dict key format.

**Fix:** Same approach: `(?:verify_exp|['"]verify_exp['"])\s*[:=]\s*False`

**FINDING-SEC-04 (LOW): SEC-005 `.+` is greedy and unbounded.**

Pattern: `jwt\.(?:encode|decode)\(.+["'][A-Za-z0-9_\-]{20,}["']`

The `.+` could theoretically match across very long lines. Since scanning is per-line, this is low risk, but a more precise pattern would use `[^)]+` to stay within the function call.

---

## 3. OpenTelemetry Verification

### Context7 Research Findings

Library: `/websites/opentelemetry_io` (8911 snippets, Score: 85.9)

**Confirmed imports and API:**
```python
# CONFIRMED correct imports:
from opentelemetry import trace, baggage
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

# CONFIRMED usage:
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Inject:
headers = {}
TraceContextTextMapPropagator().inject(headers)
# headers = {'traceparent': '00-<trace_id>-<span_id>-01'}

# Extract:
ctx = TraceContextTextMapPropagator().extract(carrier={'traceparent': '...'})

# Manual SpanContext:
span_context = SpanContext(
    trace_id=int_value,    # 16 bytes integer
    span_id=int_value,     # 8 bytes integer
    is_remote=True,
    trace_flags=TraceFlags(0x01),
)
```

**W3C traceparent format CONFIRMED:**
```
version-trace_id-parent_id-trace_flags
00-{32 hex chars}-{16 hex chars}-{2 hex chars}
Example: 00-a9c3b99a95cc045e573e163c3ac80a77-d99d251a8caecd06-01
```

### PRD Pattern Analysis

**FINDING-SEC-05 (MEDIUM): REQ-029 traceparent uses raw uuid4() with hyphens.**

REQ-029 DataFlowTracer.trace_request() specifies:
```python
trace_id = str(uuid.uuid4())
headers = {"traceparent": f"00-{trace_id}-0000000000000001-01"}
```

`uuid.uuid4()` returns format `550e8400-e29b-41d4-a716-446655440000` (with hyphens, 36 chars).
W3C traceparent requires 32 CONTINUOUS hex chars (no hyphens).

The constructed traceparent would be: `00-550e8400-e29b-41d4-a716-446655440000-0000000000000001-01` which has too many dash-separated segments and is INVALID.

**Fix:** REQ-029 should use `trace_id = uuid.uuid4().hex` (32 hex chars, no hyphens) or `str(uuid.uuid4()).replace("-", "")`.

**FINDING-SEC-06 (LOW): TRACE-001 detection approach is sound.**

REQ-036 TRACE-001 pattern: Find `httpx.(?:get|post|...)` or `requests.(?:get|post|...)` without traceparent in headers within 10 lines. This is a reasonable heuristic approach matching what Context7 confirms about manual injection requirements.

---

## 4. Scan Code Pattern Analysis (40 codes)

### Count Verification

| Category | Codes | Count |
|----------|-------|-------|
| JWT Security | SEC-001..006 | 6 |
| CORS | CORS-001..003 | 3 |
| Logging | LOG-001, LOG-004, LOG-005 | 3 |
| Trace Propagation | TRACE-001 | 1 |
| Secret Detection | SEC-SECRET-001..012 | 12 |
| Docker Security | DOCKER-001..008 | 8 |
| Adversarial | ADV-001..006 | 6 |
| Health Endpoints | HEALTH-001 | 1 |
| **Total** | | **40** |

**CONFIRMED:** REQ-006 `len(ALL_SCAN_CODES) == 40` assertion is correct.

**FINDING-SEC-07 (LOW): Tech research doc (line 1906) says "Total: 30 scan codes" but the actual table lists 40.** This is a typo in BUILD3_TECH_SECURITY_OBS.md, not in the PRD itself.

### Secret Detection Patterns (SEC-SECRET-001..012)

| Code | PRD Pattern | Tech Research Pattern | Issue |
|------|-------------|----------------------|-------|
| SEC-SECRET-001 | `AKIA[0-9A-Z]{16}` | `(?:A3T[A-Z0-9]\|AKIA\|ASIA\|ABIA\|ACCA)[A-Z0-9]{16}` | **LOW:** PRD misses A3T*, ASIA, ABIA, ACCA prefixes |
| SEC-SECRET-002 | `-----BEGIN (?:RSA \|EC \|DSA )?PRIVATE KEY-----` | `-----BEGIN\s+(?:RSA\|DSA\|EC\|PGP\|OPENSSH)?\s*PRIVATE\s+KEY` | **MEDIUM:** Misses OPENSSH and PGP types |
| SEC-SECRET-003 | `(?:api[_-]?key\|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{20,}['"]` | Same + `(?i)` flag | LOW: Missing case-insensitive flag |
| SEC-SECRET-004 | `(?:postgres\|mysql\|mongodb\|redis)://[^:]+:[^@]+@` | Adds mssql, postgresql, mariadb | LOW: Missing DB types |
| SEC-SECRET-005 | `Bearer\s+[A-Za-z0-9\-._~+/]+=*` | Different approach | LOW: May match non-hardcoded usage |
| SEC-SECRET-006 | `(?:password\|passwd\|pwd)\s*[:=]\s*['"][^'"]{8,}['"]` | Same | OK |
| SEC-SECRET-007 | `gh[ps]_[A-Za-z0-9_]{36,}` | `(?:ghp\|gho\|ghu\|ghs\|ghr)_[A-Za-z0-9_]{36,}` | **HIGH:** Misses gho_, ghu_, ghr_ |
| SEC-SECRET-008 | `glpat-[A-Za-z0-9\-_]{20,}` | Same | OK |
| SEC-SECRET-009 | `sk_(?:live\|test)_[A-Za-z0-9]{24,}` | `(?:sk\|pk)_(?:test\|live)_` | LOW: Missing pk_ prefix |
| SEC-SECRET-010 | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` | Same | OK |
| SEC-SECRET-011 | `xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+` | `xox[baprs]-[0-9]{10,}-[a-zA-Z0-9-]+` | **MEDIUM:** Only bot tokens (xoxb), misses xoxp/xoxa/xoxr/xoxs |
| SEC-SECRET-012 | `SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}` | Same | OK |

**FINDING-SEC-08 (HIGH): SEC-SECRET-007 GitHub token regex is incomplete.**

PRD pattern `gh[ps]_` only matches:
- `ghp_` (Personal Access Token)
- `ghs_` (GitHub App installation token)

Missing (all valid GitHub token prefixes per GitHub docs):
- `gho_` (OAuth access token)
- `ghu_` (GitHub App user-to-server token)
- `ghr_` (GitHub App refresh token)

**Fix:** Change to `(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}` (matches tech research).

**FINDING-SEC-09 (MEDIUM): SEC-SECRET-002 private key regex misses OPENSSH/PGP types.**

PRD: `-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----`
Missing: OPENSSH PRIVATE KEY (used by ssh-keygen ed25519) and PGP PRIVATE KEY BLOCK.

**Fix:** Change to `-----BEGIN (?:RSA |EC |DSA |PGP |OPENSSH )?PRIVATE KEY`

**FINDING-SEC-10 (MEDIUM): SEC-SECRET-011 Slack token only catches bot tokens.**

PRD: `xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+`
Missing: `xoxp-` (user tokens), `xoxa-` (app tokens), `xoxr-` (refresh tokens), `xoxs-` (session tokens)

**Fix:** Change to `xox[baprs]-[0-9]+-[0-9A-Za-z-]+`

### Docker Security Patterns (DOCKER-001..008)

| Code | PRD Pattern | Issue |
|------|-------------|-------|
| DOCKER-001 | `^FROM\s+` without `^USER\s+` | OK — logic-based |
| DOCKER-002 | `^ENV\s+(?:PASSWORD\|SECRET\|API_KEY\|PRIVATE_KEY)\s*=` | LOW: Missing TOKEN, CREDENTIALS |
| DOCKER-003 | `^FROM\s+\S+:latest\b` or no tag | OK |
| DOCKER-004 | `^COPY\s+\.\s+\.` | **LOW:** Too narrow — misses `COPY . /app` |
| DOCKER-005 | No `^HEALTHCHECK\s+` | OK |
| DOCKER-006 | `privileged:\s*true` | OK |
| DOCKER-007 | `network_mode:\s*["']?host` | OK |
| DOCKER-008 | `cap_add:.*(?:SYS_ADMIN\|ALL)` | LOW: Missing NET_ADMIN, SYS_PTRACE |

**FINDING-SEC-11 (LOW): DOCKER-004 pattern too restrictive.**

`^COPY\s+\.\s+\.` requires destination to be `.` (current dir). Misses `COPY . /app`, `COPY . /usr/src/app`, etc.

**Fix:** Change to `^COPY\s+\.\s+` (no trailing `.` anchor) or better: `^\s*(?:COPY|ADD)\s+\.\s+`

**FINDING-SEC-12 (LOW): DOCKER-008 missing dangerous capabilities.**

PRD only checks for SYS_ADMIN and ALL. Missing NET_ADMIN and SYS_PTRACE which are also security-relevant.

**Fix:** Change to `cap_add:.*(?:SYS_ADMIN|NET_ADMIN|SYS_PTRACE|ALL)`

**FINDING-SEC-13 (LOW): No scan for Docker socket mount security.**

Project-level SEC-004 requires `docker.sock:ro` in generated compose files, but no DOCKER-xxx scan code verifies this. If a user or generated file has `docker.sock` without `:ro`, it won't be detected.

**Recommendation:** Add DOCKER-009 pattern: `docker\.sock(?!.*:ro)` to verify read-only socket mount.

### CORS Patterns (CORS-001..003)

| Code | PRD Pattern | Issue |
|------|-------------|-------|
| CORS-001 | `allow_origins=["*"]` or `allow_origins=\["?\*"?\]` | LOW: Quote matching is awkward |
| CORS-002 | `allow_credentials=True` + wildcard within same call | OK — multi-line logic |
| CORS-003 | `origin\s*=\s*request\.headers` | OK |

**FINDING-SEC-14 (LOW): CORS-001 second regex variant `\["?\*"?\]` has imprecise quoting.**

The pattern `\["?\*"?\]` matches `[*]`, `["*"]`, `[*"]`, and `["*]`. The last two are malformed Python. While this won't cause false negatives, a cleaner pattern would be `\[["']\*["']\]`.

### Adversarial Patterns (ADV-001..006)

All 6 adversarial patterns in REQ-039 through REQ-042 are verified against the tech research implementations:

| Code | PRD Description | Assessment |
|------|----------------|------------|
| ADV-001 | Dead events (publish/subscribe mismatch) | CORRECT — regex patterns match tech research |
| ADV-002 | Dead contracts (defined but never implemented) | CORRECT — route decorator matching |
| ADV-003 | Orphan services (no HTTP client/server) | CORRECT |
| ADV-004 | Naming inconsistency (camelCase/snake_case mix) | CORRECT |
| ADV-005 | Missing error handling (async without try) | CORRECT |
| ADV-006 | Race conditions (global mutable in async) | CORRECT |

TECH-022 correctly specifies that AdversarialScanner must be purely static (no MCP). Confirmed.

### Logging & Observability (LOG-001/004/005, TRACE-001, HEALTH-001)

| Code | PRD Pattern | Assessment |
|------|-------------|------------|
| LOG-001 | `print\s*\(` in .py excluding tests | CORRECT |
| LOG-004 | `console\.log\s*\(` in .ts/.js excluding tests | CORRECT |
| LOG-005 | `logging\.(?:info\|debug\|warning\|error)\(.*(?:password\|secret\|token\|api_key)` | CORRECT |
| TRACE-001 | httpx/requests without traceparent within 10 lines | CORRECT approach |
| HEALTH-001 | Services without /health, /healthz, or /ready | CORRECT |

No issues found in this category.

---

## 5. Severity Classification Verification

### PRD Scan Code Reference Table (lines 583-596)

| Code | PRD Severity | Standard Assessment | Verdict |
|------|-------------|---------------------|---------|
| SEC-001 | error | error (auth bypass) | CORRECT |
| SEC-002 | (not in table, in REQ-034) | critical | SHOULD ADD to table |
| SEC-003 | (not in table) | critical | SHOULD ADD |
| SEC-004 | (not in table) | high | SHOULD ADD |
| SEC-005 | (not in table) | critical | SHOULD ADD |
| SEC-006 | (not in table) | high | SHOULD ADD |
| CORS-001 | (not in table) | error | Referenced in scan table at line 1882 |
| DOCKER-001 | error | error | CORRECT |
| DOCKER-002 | critical | critical | CORRECT |
| DOCKER-006 | critical | critical | CORRECT |

**FINDING-SEC-15 (LOW): SEC-002..006 severity missing from REQ-034.**

REQ-034 defines the regex patterns but doesn't specify severity per scan code. The scan reference table at the end of the PRD does specify them. This is not technically wrong (the reference table is the source of truth), but it would improve clarity to include severity in the REQ itself.

---

## 6. Cross-Build Consistency

| Build | Security Claim | Consistent? |
|-------|---------------|-------------|
| Build 2 SEC-001 | No secrets as MCP env vars | Build 3 SEC-001 mirrors this |
| Build 2 SEC-003 | Strip securitySchemes from cached contracts | No conflict with Build 3 |
| Build 3 SEC-001 | No ANTHROPIC_API_KEY to builder subprocesses | Consistent with Build 2 |
| Build 3 SEC-002 | No hardcoded passwords in generated compose | New requirement, no conflict |
| Build 3 SEC-003 | Traefik dashboard disabled by default | New requirement, no conflict |
| Build 3 SEC-004 | Docker socket read-only mount | New requirement, no conflict |

**No cross-build conflicts found.**

---

## 7. Tech Research Document Issues

**FINDING-SEC-16 (LOW): Total count typo in BUILD3_TECH_SECURITY_OBS.md.**

Line 1906 states "Total: 30 scan codes across 7 categories" but the actual table lists 40 codes across 8 categories (JWT Security, CORS, Logging, Trace, Secrets, Docker, Adversarial, Health). Should be "40 scan codes across 8 categories".

---

## Complete Findings Summary

| ID | Severity | Category | Description | Fix Required |
|----|----------|----------|-------------|--------------|
| SEC-08 | **HIGH** | SEC-SECRET-007 | GitHub token regex `gh[ps]_` misses `gho_`, `ghu_`, `ghr_` | YES |
| SEC-02 | MEDIUM | SEC-003 | Regex misses PyJWT `options={"verify_signature": False}` dict key format | YES |
| SEC-03 | MEDIUM | SEC-004 | Same gap as SEC-003 for `verify_exp` | YES |
| SEC-05 | MEDIUM | REQ-029 | traceparent uses raw `uuid4()` with hyphens (invalid W3C format) | YES |
| SEC-09 | MEDIUM | SEC-SECRET-002 | Missing OPENSSH and PGP private key types | YES |
| SEC-10 | MEDIUM | SEC-SECRET-011 | Slack token regex only catches `xoxb-`, misses 4 other types | YES |
| SEC-01 | LOW | Tech Stack | detect-secrets listed but never used in any REQ | Recommend |
| SEC-04 | LOW | SEC-005 | Greedy `.+` in JWT hardcoded secret pattern | Optional |
| SEC-07 | LOW | Tech Research | Count says 30, should be 40 | Fix typo |
| SEC-11 | LOW | DOCKER-004 | Pattern requires `COPY . .` but misses `COPY . /app` | Recommend |
| SEC-12 | LOW | DOCKER-008 | Missing NET_ADMIN, SYS_PTRACE capabilities | Recommend |
| SEC-13 | LOW | Docker Socket | No scan code to verify `:ro` on docker.sock mount | Recommend |
| SEC-14 | LOW | CORS-001 | Second regex variant has imprecise quote matching | Optional |
| SEC-15 | LOW | REQ-034 | SEC-002..006 severity not specified in requirement text | Optional |

---

## Recommended Fixes

### HIGH Priority

**SEC-SECRET-007 (REQ-035 line 321):**
```
BEFORE: gh[ps]_[A-Za-z0-9_]{36,}
AFTER:  (?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}
```

### MEDIUM Priority

**SEC-003 (REQ-034 line 319):**
```
BEFORE: verify_signature:\s*False or verify_signature=False
AFTER:  (?:verify_signature|['"]verify_signature['"])\s*[:=]\s*False
```

**SEC-004 (REQ-034 line 319):**
```
BEFORE: verify_exp:\s*False or verify_exp=False
AFTER:  (?:verify_exp|['"]verify_exp['"])\s*[:=]\s*False
```

**REQ-029 traceparent (line 280):**
```
BEFORE: trace_id = str(uuid.uuid4())
AFTER:  trace_id = uuid.uuid4().hex  # 32 hex chars, no hyphens
```

**SEC-SECRET-002 (REQ-035 line 321):**
```
BEFORE: -----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----
AFTER:  -----BEGIN (?:RSA |EC |DSA |PGP |OPENSSH )?PRIVATE KEY
```

**SEC-SECRET-011 (REQ-035 line 321):**
```
BEFORE: xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+
AFTER:  xox[baprs]-[0-9]+-[0-9A-Za-z-]+
```

### LOW Priority (Recommended)

**DOCKER-004 (REQ-037):** `^\s*(?:COPY|ADD)\s+\.\s+` (remove trailing `.` anchor)
**DOCKER-008 (REQ-037):** `cap_add:.*(?:SYS_ADMIN|NET_ADMIN|SYS_PTRACE|ALL)`
**SEC-SECRET-001:** `(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}` (all AWS prefix types)
**Tech research line 1906:** Change "30" to "40"

---

## Verification Checklist

### detect-secrets
- [x] Python API: `SecretsCollection.scan_file()` — Context7 CONFIRMED (method, not standalone)
- [x] `transient_settings()` context manager — Context7 CONFIRMED
- [x] Plugin system: HexHighEntropyString, Base64HighEntropyString, AWSKeyDetector — Context7 CONFIRMED
- [x] Baseline file format — Context7 CONFIRMED (JSON dict keyed by filename)
- [x] Programmatic vs CLI usage — Context7 CONFIRMED (both available)
- [x] **PRD does NOT use detect-secrets** — uses custom regex instead

### PyJWT
- [x] `jwt.decode()` parameters: algorithms, options, audience, issuer — Context7 CONFIRMED
- [x] Algorithm enforcement: `algorithms=["RS256"]` — Context7 CONFIRMED (mandatory param)
- [x] Claim validation: exp, nbf, iss, aud — Context7 CONFIRMED (via options dict)
- [x] Error classes: ExpiredSignatureError, InvalidTokenError, etc. — Context7 CONFIRMED
- [ ] SEC-003/004 regex patterns need fix for options dict format — **MEDIUM**

### OpenTelemetry
- [x] `opentelemetry-api` and `opentelemetry-sdk` imports — Context7 CONFIRMED
- [x] W3C traceparent header format: `00-{trace_id}-{span_id}-{flags}` — Context7 CONFIRMED
- [x] Trace context propagation patterns — Context7 CONFIRMED (TraceContextTextMapPropagator)
- [x] SpanContext, TracerProvider setup — Context7 CONFIRMED
- [ ] REQ-029 traceparent construction uses raw uuid4() — **MEDIUM** (hyphens invalid)

### Scan Code Patterns (40 codes)
- [x] All patterns are valid Python regex — CONFIRMED
- [x] Count: 40 scan codes across 8 categories — CONFIRMED
- [ ] SEC-SECRET-007 false negative for 3 GitHub token types — **HIGH**
- [ ] SEC-SECRET-002 misses OPENSSH/PGP — **MEDIUM**
- [ ] SEC-SECRET-011 misses non-bot Slack tokens — **MEDIUM**
- [x] Severity classifications are reasonable — CONFIRMED
- [x] Adversarial patterns (ADV-001..006) are all purely static — CONFIRMED per TECH-022

### Docker Security
- [x] DOCKER-001..008 patterns are valid — CONFIRMED
- [ ] DOCKER-004 pattern too narrow — **LOW**
- [ ] DOCKER-008 missing capabilities — **LOW**
- [ ] No scan for docker.sock read-only — **LOW**
- [x] Socket mount security documented in SEC-004 (project-level) — CONFIRMED

---

*Audit completed. 1 HIGH, 5 MEDIUM, 8 LOW findings. All HIGH/MEDIUM have recommended fixes above.*
