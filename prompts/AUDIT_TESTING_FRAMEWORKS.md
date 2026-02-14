# Audit Report: Testing Frameworks in Build 3 PRD

> Audited: 2026-02-14
> Reviewer: Testing Frameworks Technical Reviewer
> Sources: Schemathesis GitHub (stable), pact-python v3 source code (main branch), Testcontainers Python v4 (GitHub + readthedocs), httpx (encode/httpx), pytest-asyncio docs, Context7 library research

---

## Executive Summary

The Build 3 PRD contains **5 CRITICAL issues**, **3 HIGH issues**, and **4 MEDIUM issues** across testing framework usage. The most severe problems are in the Pact Python section, where the PRD describes an API that does not match the actual v3 library. The Schemathesis section has significant API discrepancies in programmatic usage patterns. The pytest-asyncio and httpx sections are accurate.

---

## 1. Schemathesis 4.x

### 1.1 Schema Loaders

| Claim in PRD | Actual API | Verdict |
|---|---|---|
| `schemathesis.openapi.from_url()` | `schemathesis.openapi.from_url()` | CORRECT |
| `schemathesis.openapi.from_path()` | `schemathesis.openapi.from_path()` | CORRECT |
| `schemathesis.openapi.from_dict()` | `schemathesis.openapi.from_dict()` | CORRECT |

**Note:** The PRD also uses `schemathesis.from_url()` (without `.openapi.`) in TECH-011. In Schemathesis 4.x, the correct namespace is `schemathesis.openapi.from_url()`. The top-level `schemathesis.from_url()` may still exist as a legacy alias but is not the canonical path.

**TECH-011 text:** "Schemathesis must use `schemathesis.openapi.from_url()` for live service testing" -- this is CORRECT.

### 1.2 @schema.parametrize() Decorator

| Claim | Actual | Verdict |
|---|---|---|
| `@schema.parametrize()` generates pytest test cases | Confirmed by Context7 docs and official examples | CORRECT |
| PRD correctly distinguishes decorator usage (generate_test_file) from programmatic usage (run_against_service) | Correct separation in REQ-019 and REQ-020 | CORRECT |

### 1.3 case.call() and case.validate_response()

**CRITICAL ISSUE (SCHEMA-CRITICAL-1): Programmatic iteration API is wrong**

REQ-019 describes:
```python
for path, methods in schema.items():
    for method, operation in methods.items():
        case = operation.make_case()
        response = case.call(base_url=base_url)
        case.validate_response(response)
```

**Actual API (from Context7 + source docs):**
- `schema["/path"]["METHOD"]` returns an `APIOperation` object
- `operation.Case(...)` creates a case (not `operation.make_case()`)
- `case.call()` is correct
- `case.validate_response(response)` exists on the Case object
- BUT `schema.items()` iteration pattern is not documented -- the documented pattern is `schema[path][method]` indexing

**FIX for REQ-019:** Replace `operation.make_case()` with `operation.Case()` or use `case.call_and_validate()` pattern. The iteration should be based on schema operations, not Python dict-like iteration. A safer programmatic approach:

```python
schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)

@schema.parametrize()
def test_api(case):
    response = case.call()
    case.validate_response(response)
```

Or for non-pytest programmatic use:
```python
schema = schemathesis.openapi.from_url(openapi_url)
for api_operation in schema.get_all_operations():
    case = api_operation.make_case()  # This may work but is not canonical
    response = case.call(base_url=base_url)
    api_operation.validate_response(response)
```

**Severity: CRITICAL** -- The programmatic iteration pattern will likely fail at runtime.

### 1.4 Exception Classes

**CRITICAL ISSUE (SCHEMA-CRITICAL-2): schemathesis.exceptions.CheckFailed may not exist in v4**

TECH-012 states:
> `case.validate_response()` raises `schemathesis.exceptions.CheckFailed` on failure

**Actual behavior (from Context7 docs):**
- The Context7 docs show `validate_response()` "raises a validation error" but do NOT mention `CheckFailed` specifically
- The Schemathesis reference shows `operation.validate_response()` raises `FailureGroup`
- The `schemathesis.exceptions` module path does not appear in the Schemathesis v4 Context7 results
- The tech research doc (BUILD3_TECH_TESTING.md) line 189 states: `operation.validate_response(response, case=None)` raises `FailureGroup on failure`

**The PRD contradicts itself:**
- TECH-012: "catch `schemathesis.exceptions.CheckFailed`"
- BUILD3_TECH_TESTING.md line 189: "raises `FailureGroup` on failure"

**FIX:** The exception class should be verified against the actual installed version. Based on the tech research doc (which is more recent), the exception is likely `FailureGroup`, not `CheckFailed`. The PRD should say:
```python
from schemathesis.failures import FailureGroup  # or check actual module
```

**Severity: CRITICAL** -- Using wrong exception class means violations will never be caught.

### 1.5 Stateful Testing

| Claim | Actual | Verdict |
|---|---|---|
| `@schema.parametrize(stateful=Stateful.links)` | Not found in v4 docs. V4 uses `schema.as_state_machine()` pattern | INCORRECT |

**HIGH ISSUE (SCHEMA-HIGH-1): Stateful testing API has changed**

The PRD does not directly use `stateful=Stateful.links` in any requirement, but the PRD should be aware that stateful testing in Schemathesis v4 uses `schema.as_state_machine()`, NOT `@schema.parametrize(stateful=...)`.

**Severity: HIGH** -- Only relevant if stateful testing is implemented.

### 1.6 Custom Checks and Hooks

| Claim | Actual | Verdict |
|---|---|---|
| `@schemathesis.check` decorator | Confirmed: `@schemathesis.check` with `(ctx: CheckContext, response, case)` signature | CORRECT |
| `@schemathesis.hook` decorator | Confirmed: `@schemathesis.hook` with multiple hook types | CORRECT |

### 1.7 Build 1 PRD Cross-Reference

Build 1 PRD (line 17) specifies **Schemathesis 4.10.1**. Build 3 specifies **schemathesis 4.x**. These are compatible. Build 1 uses:
- `schemathesis.openapi.from_path()` -- CORRECT
- `schemathesis.openapi.from_url()` -- CORRECT
- `@schema.parametrize()` -- CORRECT
- `case.call_and_validate()` -- CORRECT

No issues in Build 1's Schemathesis usage.

---

## 2. Pact Python v3

### 2.1 Consumer Side

| Claim | Actual | Verdict |
|---|---|---|
| `from pact import Pact` | `from pact import Pact` | CORRECT |
| `Pact(consumer, provider)` constructor | Confirmed from `__init__.py` | CORRECT |
| `upon_receiving()` chain | Confirmed: returns `HttpInteraction` | CORRECT |
| `with_request(method, path)` | Confirmed | CORRECT |
| `will_respond_with(status, headers, body)` | Confirmed | CORRECT |
| `pact.serve()` as context manager | Confirmed: `with pact.serve() as srv:` | CORRECT |

### 2.2 Matching DSL

| Claim | Actual | Verdict |
|---|---|---|
| `like()`, `each_like()`, `term()`, `Format` | V3 uses `match.like()`, `match.each_like()`, `match.regex()` -- NO `term()` or `Format` | MIXED |

**MEDIUM ISSUE (PACT-MEDIUM-1): Matching DSL names changed in v3**

The PRD tech stack says "pact-python 3.2.1+" but the matching functions `term()` and `Format` are from the v2 API. In pact-python v3:
- `term()` is replaced by `match.regex(value, regex=pattern)`
- `Format` does not exist
- `like()` is `match.like(value)` or `match.type(value)`
- `each_like()` is `match.each_like(value, min=N)`

The PRD does not directly use `term()` or `Format` in requirements, so this is informational. The tech research doc (BUILD3_TECH_TESTING.md) correctly documents the v3 matching DSL.

**Severity: MEDIUM** -- Agent might use legacy API if not careful.

### 2.3 Provider Verification

**CRITICAL ISSUE (PACT-CRITICAL-1): Verifier.verify() return type and exception class are WRONG**

REQ-021 and TECH-013 state:
> `verifier.verify()` returns None on success and raises `pact.error.PactVerificationError` on failure

**Actual API (verified from pact-python source code at `src/pact/verifier.py`):**

```python
def verify(self) -> Self:
    """Verify the interactions.

    Returns:
        Whether the interactions were verified successfully.

    Raises:
        RuntimeError:
            If no transports have been set.
    """
```

Key findings from the actual source code:
1. `verify()` returns `Self` (the Verifier instance), NOT `None`
2. `verify()` raises `RuntimeError` if no transports are set
3. The underlying `pact_ffi.verifier_execute()` call raises on FFI-level verification failure
4. **There is NO `PactVerificationError` raised by Verifier.verify()**

The `PactVerificationError` class EXISTS in `pact.error` but it is used by `Pact.verify()` (consumer-side message verification), NOT by `Verifier.verify()` (provider-side verification). These are completely different methods on different classes:
- `Pact.verify(handler, kind)` -- consumer message verification, raises `PactVerificationError`
- `Verifier.verify()` -- provider verification, raises FFI-level errors

**FIX for REQ-021:**
```python
# WRONG (PRD):
try:
    verifier.verify()
except PactVerificationError as e:
    ...

# CORRECT:
try:
    verifier.verify()
except Exception as e:
    # pact_ffi raises on verification failure
    # Extract details from verifier.results or verifier.output()
    ...
```

**Severity: CRITICAL** -- Catching wrong exception means verification failures will crash instead of being handled.

**CRITICAL ISSUE (PACT-CRITICAL-2): Verifier.add_transport() signature is WRONG**

REQ-021 uses:
```python
Verifier(provider_name).add_transport(url=provider_url)
```

**Actual signature (from source):**
```python
def add_transport(
    self,
    *,
    url: str | URL | None = None,
    protocol: str | None = None,
    port: int | None = None,
    path: str | None = None,
    scheme: str | None = None,
) -> Self:
```

The `url` parameter IS supported as a keyword-only argument. However, the PRD uses positional-style `add_transport(url=provider_url)` which IS correct as a keyword argument. BUT the source shows that when `url` is provided, the host is extracted and compared with `self._host` (which defaults to "localhost"). If the provider URL host is NOT "localhost", this will raise `ValueError: Host mismatch`.

**FIX:** The PRD should note that the Verifier must be initialized with the correct host:
```python
from yarl import URL
provider_parsed = URL(provider_url)
verifier = Verifier(provider_name, host=provider_parsed.host)
verifier.add_transport(url=provider_url)
```

Or use explicit parameters:
```python
verifier = Verifier(provider_name)
verifier.add_transport(protocol="http", port=8080, path="/", scheme="http")
```

**Severity: CRITICAL** -- Will fail at runtime when provider is not on localhost.

### 2.4 Verifier.set_state() vs state_handler()

**HIGH ISSUE (PACT-HIGH-1): set_state() method does not exist, it is state_handler()**

REQ-021 uses:
```python
verifier.set_state(url=f"{provider_url}/_pact/state", teardown=True)
```

**Actual API (from source):**
```python
# Method is state_handler(), not set_state()
verifier.state_handler(
    handler=StateHandlerUrl(f"{provider_url}/_pact/state"),
    teardown=True,
    body=True,  # REQUIRED when using URL
)
```

OR using the internal method:
```python
# Alternative with URL string
verifier.state_handler(
    StateHandlerUrl(f"{provider_url}/_pact/state"),
    teardown=True,
    body=True,
)
```

Note: The `body` parameter is REQUIRED when providing a URL handler.

**FIX for REQ-021:**
Replace `verifier.set_state(url=..., teardown=True)` with `verifier.state_handler(StateHandlerUrl(url), teardown=True, body=True)`

**Severity: HIGH** -- Will raise `AttributeError` at runtime.

### 2.5 Tech Research Doc (BUILD3_TECH_TESTING.md) Accuracy

The tech research doc at lines 605-698 describes the Verifier API. Checking it:

| Tech Doc Claim | Actual | Verdict |
|---|---|---|
| `Verifier(name, host)` constructor | Correct | CORRECT |
| `add_transport(protocol, port, path, scheme, url)` | Correct (keyword-only) | CORRECT |
| `add_source(source)` | Correct | CORRECT |
| `set_state(url, teardown, body)` | **WRONG** -- method is `state_handler()` | INCORRECT |
| `verify() -> None` raises on failure | **WRONG** -- returns `Self`, FFI raises | INCORRECT |

The tech research doc has the SAME errors as the PRD. The `set_state()` method and `verify()` return type are wrong in both places.

---

## 3. Testcontainers Python v4

### 3.1 DockerCompose Class

| Claim | Actual | Verdict |
|---|---|---|
| `DockerCompose(context, compose_file_name)` | Confirmed from API docs | CORRECT |
| `compose.waiting_for({...})` context manager | Confirmed: returns context manager | CORRECT |
| `get_service_host(service, port)` | Confirmed | CORRECT |
| `get_service_port(service, port)` | Confirmed | CORRECT |
| `exec_in_container(service_name, command)` | Confirmed | CORRECT |

### 3.2 Wait Strategies

| Claim | Actual | Verdict |
|---|---|---|
| `wait_for_logs()` utility | Exists as `LogMessageWaitStrategy` in `testcontainers.core.waiting_utils` | PARTIALLY CORRECT |
| `wait_for_http()` utility | Exists as `HttpWaitStrategy` in `testcontainers.core.waiting_utils` | PARTIALLY CORRECT |

**MEDIUM ISSUE (TC-MEDIUM-1): Wait strategy function names are class names**

The PRD tech stack line 18 says "DockerCompose with wait strategies" which is correct. The PRD does not explicitly use `wait_for_logs()` or `wait_for_http()` as function calls. The actual API uses:
- `LogMessageWaitStrategy("message")` -- class, not function
- `HttpWaitStrategy(port).for_status_code(200)` -- class, not function
- `PortWaitStrategy(port)` -- class
- `ExecWaitStrategy(command)` -- class

Since the PRD does not prescribe specific wait strategy usage in requirements, this is informational.

**Severity: MEDIUM** -- Agent may look for wrong function names.

### 3.3 Container Lifecycle

| Claim | Actual | Verdict |
|---|---|---|
| Context manager usage (`with compose:`) | Confirmed | CORRECT |
| `start()` / `stop()` manual lifecycle | Confirmed for individual containers | CORRECT |
| `DockerCompose` as context manager | Confirmed: `with compose.waiting_for({...}):` | CORRECT |

### 3.4 Network Configuration

The PRD does not make specific claims about Testcontainers network configuration. The DockerCompose class delegates to Docker Compose for networking. No issues.

---

## 4. pytest + pytest-asyncio

### 4.1 asyncio_mode Configuration

| Claim | Actual | Verdict |
|---|---|---|
| `asyncio_mode = "auto"` in pytest config | Confirmed from Context7 docs | CORRECT |
| pytest-asyncio 0.24.x+ | Compatible | CORRECT |

**Configuration options (from Context7):**
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
asyncio_default_test_loop_scope = function
```

The `auto` mode means async tests don't need `@pytest.mark.asyncio` decorator.

### 4.2 Event Loop Scope

**MEDIUM ISSUE (PYTEST-MEDIUM-1): Missing loop_scope configuration guidance**

The PRD specifies `asyncio_mode = "auto"` but does not mention `asyncio_default_fixture_loop_scope` or `asyncio_default_test_loop_scope`. In pytest-asyncio 0.24+, the default loop scope is `function`, meaning each test gets its own event loop. If fixtures are session-scoped async fixtures, they need explicit `loop_scope="session"`.

This could cause issues with session-scoped async fixtures (e.g., database connections, HTTP clients) if not configured.

**Severity: MEDIUM** -- May cause "Event loop is closed" errors with session-scoped fixtures.

---

## 5. httpx

### 5.1 AsyncClient Usage

| Claim | Actual | Verdict |
|---|---|---|
| `httpx.AsyncClient` with `timeout=30.0` | Confirmed: `async with httpx.AsyncClient(timeout=30.0) as client:` | CORRECT |
| `follow_redirects=True` | Confirmed: supported parameter | CORRECT |

### 5.2 ASGITransport for Testing

| Claim | Actual | Verdict |
|---|---|---|
| `httpx.ASGITransport(app=app)` | Confirmed from Context7 docs | CORRECT |

**Confirmed correct pattern:**
```python
transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
    r = await client.get("/")
```

### 5.3 Timeout Configuration

| Claim | Actual | Verdict |
|---|---|---|
| `timeout=30.0` for simple timeout | Correct: applies to all operations | CORRECT |
| Fine-grained `httpx.Timeout()` | Available: `httpx.Timeout(10.0, connect=5.0, read=30.0)` | CORRECT |

No issues with httpx usage in the PRD.

---

## 6. Cross-Build References

### Build 1 PRD Testing References

Build 1 uses Schemathesis correctly:
- `schemathesis.openapi.from_path()` for local spec files (TECH-014)
- `@schema.parametrize()` for generated test code (TECH-013)
- `case.call_and_validate()` for automatic validation (TECH-014)

No conflicts with Build 3.

### Build 2 PRD Testing References

Build 2 has no direct testing framework references (delegates to agent-team CLI). No conflicts.

---

## Issue Summary

### CRITICAL (5 issues)

| ID | Location | Issue | Fix |
|---|---|---|---|
| SCHEMA-CRITICAL-1 | REQ-019 | `operation.make_case()` is not canonical API; programmatic iteration pattern may not work | Use `schema.get_all_operations()` or `@schema.parametrize()` pattern |
| SCHEMA-CRITICAL-2 | TECH-012 | `schemathesis.exceptions.CheckFailed` may not exist; tech doc says `FailureGroup` | Verify actual exception class; likely `FailureGroup` from `schemathesis.failures` |
| PACT-CRITICAL-1 | REQ-021, TECH-013 | `Verifier.verify()` returns `Self` not `None`; does NOT raise `PactVerificationError` | Use `try/except Exception` and check `verifier.results` for failure details |
| PACT-CRITICAL-2 | REQ-021 | `add_transport(url=...)` requires host match with Verifier's host parameter | Initialize `Verifier(name, host=actual_host)` or use explicit transport params |
| PACT-CRITICAL-3 | TECH-013 | `pact.error.PactVerificationError` is for consumer `Pact.verify()`, NOT provider `Verifier.verify()` | Change import and exception handling; use FFI-level exception or generic Exception |

### HIGH (3 issues)

| ID | Location | Issue | Fix |
|---|---|---|---|
| PACT-HIGH-1 | REQ-021 | `verifier.set_state()` does not exist; actual method is `verifier.state_handler()` | Replace with `verifier.state_handler(StateHandlerUrl(url), teardown=True, body=True)` |
| SCHEMA-HIGH-1 | General | Stateful testing uses `schema.as_state_machine()`, not `parametrize(stateful=...)` | Update any stateful testing references |
| PACT-HIGH-2 | BUILD3_TECH_TESTING.md | Tech research doc has same errors as PRD (set_state, verify return type) | Fix in both documents |

### MEDIUM (4 issues)

| ID | Location | Issue | Fix |
|---|---|---|---|
| PACT-MEDIUM-1 | General | `term()` and `Format` are v2 matching DSL; v3 uses `match.regex()` | Use v3 matching module functions |
| TC-MEDIUM-1 | General | Wait strategies are classes (`LogMessageWaitStrategy`), not functions | Use class-based wait strategy API |
| PYTEST-MEDIUM-1 | TECH | Missing `asyncio_default_fixture_loop_scope` config | Add `asyncio_default_fixture_loop_scope = function` (or session if needed) |
| SCHEMA-MEDIUM-1 | REQ-019 | `schema.items()` dict-like iteration not documented; use operation API | Use `schema.get_all_operations()` or similar |

---

## Recommended Fixes

### Fix 1: REQ-019 (Schemathesis programmatic API)

**Current (WRONG):**
```python
for path, methods in schema.items():
    for method, operation in methods.items():
        case = operation.make_case()
        response = case.call(base_url=base_url)
        case.validate_response(response)
```

**Proposed:**
```python
schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)
for operation in schema.get_all_operations():
    for case in operation.make_case():  # generates test cases
        response = case.call()
        case.validate_response(response)
```

Or use the simpler approach with `call_and_validate()`:
```python
schema = schemathesis.openapi.from_url(openapi_url, base_url=base_url)
# Use schema indexing for specific operations
for path in schema:
    for method in schema[path]:
        operation = schema[path][method]
        case = operation.Case()
        response = case.call()
        operation.validate_response(response)
```

### Fix 2: TECH-012 (Schemathesis exception class)

**Current (WRONG):**
```
case.validate_response() raises schemathesis.exceptions.CheckFailed
```

**Proposed:**
```
operation.validate_response(response) raises schemathesis.failures.FailureGroup on failure.
The Case-level case.validate_response() also raises FailureGroup.
Import via: from schemathesis.failures import FailureGroup
```

### Fix 3: REQ-021 (Pact Verifier)

**Current (WRONG):**
```python
from pact import Verifier
verifier = Verifier(provider_name).add_transport(url=provider_url)
verifier.add_source(str(pf))
verifier.set_state(url=f"{provider_url}/_pact/state", teardown=True)
try:
    verifier.verify()
except PactVerificationError as e:
    # handle failure
```

**Proposed:**
```python
from pact import Verifier
from pact.types import StateHandlerUrl
from yarl import URL

provider_parsed = URL(provider_url)
verifier = (
    Verifier(provider_name, host=provider_parsed.host)
    .add_transport(url=provider_url)
    .add_source(str(pf))
    .state_handler(
        StateHandlerUrl(f"{provider_url}/_pact/state"),
        teardown=True,
        body=True,
    )
)
try:
    verifier.verify()
except Exception as e:
    # FFI-level exception on verification failure
    # Extract details from verifier.output(strip_ansi=True) or verifier.results
    violations = parse_verifier_output(verifier.output(strip_ansi=True))
```

### Fix 4: TECH-013 (Pact exception handling)

**Current (WRONG):**
```
Pact provider verification must use from pact import Verifier (NOT pact.v3.verifier).
The Verifier(name).add_transport(url=url).add_source(path).verify() method returns None
on success and raises pact.error.PactVerificationError on failure.
There is NO VerifyResult class -- use try/except pattern
```

**Proposed:**
```
Pact provider verification must use from pact import Verifier (NOT pact.v3.verifier -- v3
was moved to top-level in v3 release). The Verifier(name, host=host).add_transport(url=url)
.add_source(path).verify() method returns Self on success. On verification failure, the
underlying pact_ffi.verifier_execute() raises an exception. Use try/except Exception and
inspect verifier.results (dict) or verifier.output(strip_ansi=True) for failure details.
There is NO VerifyResult class. Note: pact.error.PactVerificationError exists but is for
consumer Pact.verify() message verification, NOT provider Verifier.verify().
```

### Fix 5: BUILD3_TECH_TESTING.md (Section 2.3)

The tech research document at lines 660-665 shows `set_state()` method. This should be updated to `state_handler()` with the correct signature.

Line 698 shows `verify() -> None`. This should be `verify() -> Self`.

---

## Verified Correct Claims

The following claims in the PRD are verified correct and need no changes:

1. **Schemathesis schema loaders** (`from_url`, `from_path`, `from_dict` under `schemathesis.openapi`)
2. **Schemathesis `@schema.parametrize()`** decorator for generated test files
3. **Schemathesis `case.call()`** method signature
4. **Schemathesis `@schemathesis.check`** and `@schemathesis.hook` decorators
5. **Pact consumer API** (`Pact`, `upon_receiving`, `with_request`, `will_respond_with`, `serve()`)
6. **Pact `from pact import Verifier`** import path (v3 moved to top-level)
7. **Pact `Verifier.add_source()`** method
8. **Testcontainers `DockerCompose`** class and constructor
9. **Testcontainers wait strategies** (`LogMessageWaitStrategy`, `HttpWaitStrategy`)
10. **pytest-asyncio `asyncio_mode = "auto"`** configuration
11. **httpx `AsyncClient`** with `timeout=30.0`
12. **httpx `ASGITransport`** for in-process testing
13. **httpx `follow_redirects=True`** parameter
14. **Docker Compose v2** syntax (`docker compose` not `docker-compose`)
