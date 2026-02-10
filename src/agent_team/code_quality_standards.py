"""Non-configurable code quality standards for Agent Team.

Unlike UI standards (customizable via standards_file), these represent
professional competency -- always-on, non-negotiable.
"""
from __future__ import annotations

FRONTEND_STANDARDS = r"""
## FRONTEND CODE QUALITY STANDARDS (ALWAYS APPLIED)

LLMs produce tutorial-quality frontend code by default. These standards enforce production quality.

### Anti-Patterns (NEVER produce these)

**FRONT-001: Components Inside Render**
- NEVER define components inside other components' render functions.
- Inner components re-mount on every render, destroying state and killing performance.
- FIX: Extract to separate file or define at module scope.

**FRONT-002: God Components**
- NEVER write components exceeding 200 LOC or handling multiple responsibilities.
- FIX: Split by responsibility. One component = one job.

**FRONT-003: Derived State in useState**
- NEVER use useState + useEffect to compute values derivable from existing state/props.
- FIX: Compute during render: `const fullName = first + ' ' + last;`

**FRONT-004: useEffect for Everything**
- NEVER use useEffect for synchronous derivations or event-driven logic.
- FIX: Derive in render for computed values. Use event handlers for user actions.

**FRONT-005: Missing Effect Cleanup**
- NEVER leave useEffect without cleanup for subscriptions, timers, or fetch calls.
- FIX: Return cleanup function. Use AbortController for fetch. Cancel timers.

**FRONT-006: Stale Closures**
- NEVER omit dependencies from useCallback/useEffect/useMemo dependency arrays.
- FIX: Include all referenced variables. Use the exhaustive-deps lint rule.

**FRONT-007: any Type Abuse**
- NEVER use TypeScript `any` as a shortcut. It defeats the type system entirely.
- FIX: Use `unknown` + type guards, proper generics, or specific types.

**FRONT-008: Prop Drilling**
- NEVER pass props through 3+ component layers just to reach a deep child.
- FIX: Use Context, composition (children), or state management for deep data.

**FRONT-009: Waterfall Requests**
- NEVER chain sequential fetches that could run in parallel.
- FIX: Use Promise.all, parallel queries, or data loaders.

**FRONT-010: Missing Error Boundaries**
- NEVER leave component trees without error boundaries — one error whites out the screen.
- FIX: Wrap route-level and feature-level boundaries. Provide fallback UI.

**FRONT-011: Index/Random Keys**
- NEVER use `key={index}` on dynamic lists or `key={Math.random()}`.
- FIX: Use stable, unique identifiers from data (id, slug, etc.).

**FRONT-012: Unnecessary Re-renders**
- NEVER ignore re-render costs on expensive child components.
- FIX: Use React.memo for pure display components. Memoize callbacks passed as props.

**FRONT-013: Business Logic in UI**
- NEVER put API calls, complex validation, or data transformation inside components.
- FIX: Extract to hooks, services, or utility modules. Components render, hooks orchestrate.

**FRONT-014: Missing Loading/Error States**
- NEVER show blank screens during data loading or after errors.
- FIX: Every async UI needs: loading skeleton, error message with retry, empty state.

**FRONT-015: Div Instead of Semantic HTML**
- NEVER use `<div onClick>` when `<button>` exists. Never use `<div>` for navigation.
- FIX: Use semantic elements: button, a, nav, main, section, article, header, footer.

**FRONT-016: Duplicated Helper Functions**
- NEVER define the same helper function in two or more files.
- FIX: Extract to a shared `src/lib/` or `src/utils/` module and import from there.

**FRONT-017: No Max-Length on String Inputs**
- NEVER validate strings with only `z.string().min(1)` without a `.max()` constraint.
- FIX: Add `.max(500)` for short fields, `.max(2048)` for URLs/descriptions, appropriate limits for each field.

**FRONT-018: No URL Protocol Restriction**
- NEVER accept URLs with `z.string().url()` without restricting the protocol.
- `z.string().url()` accepts `file://`, `javascript:`, and other dangerous schemes.
- FIX: `.refine(url => url.startsWith('http'))` or use a custom URL validator that only allows http/https.

**FRONT-019: Mock Data in Services**
- NEVER use mock/stub/fake data in service files. Never use `of(mockData)`, `delay()` to simulate API calls, or hardcoded arrays as data sources.
- Every service method MUST make a REAL HTTP call to the backend API.
- FIX: Use HttpClient.get/post/put/delete with proper URLs. Map response DTOs to frontend models.
- If the backend endpoint doesn't exist yet, flag it as a blocker — do NOT create fake data.

**FRONT-020: DTO/Enum Mismatch**
- NEVER assume frontend enum values match backend enum values without verification.
- Backend may return numeric enums (0, 1, 2) while frontend uses string enums ('admin', 'manager').
- FIX: Create mapping functions (mapApiRole, mapTenderStatus) in model files. Apply in services.

**FRONT-021: Hardcoded Service Responses**
- NEVER return hardcoded objects from service methods. Every method must call a real API endpoint.
- Patterns to AVOID: `return of({...})`, `return new Observable(sub => sub.next({...}))`, `return Promise.resolve({...})`
- FIX: Return `this.http.get<T>(url)` or equivalent real HTTP call.

### Quality Rules

**State Management:**
- Colocate state. Lift only when truly shared. URL state for navigation-relevant values.
- Server state belongs in a cache layer (React Query, SWR), not useState.

**TypeScript:**
- Discriminated unions over optional fields. Narrow types at boundaries.
- Export types alongside components. No implicit any.

**Performance:**
- Virtualize lists > 100 items. Lazy-load routes and heavy components.
- Debounce user input. Avoid layout thrashing (batch DOM reads/writes).

**Accessibility:**
- Every interactive element keyboard-accessible. ARIA labels on icon-only buttons.
- Focus management on modals/dialogs. Color is never the ONLY indicator.
""".strip()

BACKEND_STANDARDS = r"""
## BACKEND CODE QUALITY STANDARDS (ALWAYS APPLIED)

LLMs generate tutorial-quality backend code by default. These standards enforce production quality.

### Anti-Patterns (NEVER produce these)

**BACK-001: SQL/NoSQL Injection**
- NEVER concatenate user input into query strings.
- FIX: Use parameterized queries, prepared statements, or ORM query builders.

**BACK-002: N+1 Queries**
- NEVER fetch a list then loop to query each item individually.
- FIX: Use eager loading, JOINs, batch fetches, or DataLoader pattern.

**BACK-003: Broad Exception Catch**
- NEVER write `catch(error) {}` or bare `except:` that swallows all errors silently.
- FIX: Catch specific exceptions. Log unexpected ones. Re-raise what you can't handle.

**BACK-004: Leaking Internal Errors**
- NEVER return stack traces, SQL errors, or internal paths in API responses.
- FIX: Map to generic messages in production. Log full details server-side.

**BACK-005: Missing Pagination**
- NEVER return an entire dataset without limit/offset or cursor pagination.
- FIX: Default page size. Max page size cap. Return total count and next cursor.

**BACK-006: Broken Object Authorization (IDOR)**
- NEVER access resources by ID without verifying the requester owns/can access them.
- FIX: Check ownership/permissions before every data access. Filter queries by user.

**BACK-007: Hardcoded Secrets**
- NEVER put API keys, passwords, or tokens directly in source code.
- FIX: Use environment variables, secret managers, or encrypted config.

**BACK-008: Missing Input Validation**
- NEVER trust client input without validation at the API boundary.
- FIX: Validate type, format, length, range. Use schema validation (Zod, Pydantic, Joi).

**BACK-009: No Rate Limiting**
- NEVER expose endpoints without rate limiting — especially auth and write operations.
- FIX: Apply rate limiting middleware. Stricter on auth endpoints.

**BACK-010: Missing Indexes**
- NEVER query columns used in WHERE/JOIN/ORDER BY without database indexes.
- FIX: Add indexes for query patterns. Monitor slow query logs.

**BACK-011: Synchronous Blocking**
- NEVER use synchronous I/O (readFileSync, synchronous HTTP) in request handlers.
- FIX: Use async/await for all I/O operations. Offload CPU-heavy work to workers.

**BACK-012: No Structured Logging**
- NEVER use console.log with plain strings in production code. Never log secrets.
- FIX: Use structured logging (JSON format) with levels, correlation IDs, and context.

**BACK-013: Missing Health Checks**
- NEVER deploy services without /health and /readiness endpoints.
- FIX: Health checks verify connectivity to dependencies. Return structured status.

**BACK-014: No Idempotency**
- NEVER allow retry of POST/PUT to create duplicate records or side effects.
- FIX: Use idempotency keys. Make operations safe to retry.

**BACK-015: SSRF Vulnerability**
- NEVER fetch user-supplied URLs without validation and allowlisting.
- FIX: Validate URL scheme and host. Block internal network ranges. Use allowlists.

**BACK-016: Non-transactional Multi-Step Writes**
- NEVER perform sequential deleteMany + createMany (or delete + create) without wrapping in a transaction.
- FIX: Use `$transaction()` (Prisma), `db.session` (SQLAlchemy), or equivalent atomic wrapper.

**BACK-017: Validation Result Discarded**
- NEVER call `schema.parse(body)` or `schema.validate(body)` without assigning the result.
- The parsed result contains sanitized data; ignoring it means raw input flows downstream.
- FIX: `req.body = schema.parse(req.body)` — always use the parsed/sanitized output.

**BACK-018: Unvalidated Route Parameters**
- NEVER use `Number(req.params.id)` or `parseInt(req.params.id)` without checking for NaN.
- FIX: Validate immediately after parsing; return 400 on invalid (e.g., `if (isNaN(id)) return res.status(400)...`).

**BACK-019: Unvalidated FK References**
- NEVER accept foreign key IDs from client input without verifying the referenced entity exists.
- FIX: Query the referenced entity first; return 404 if not found before proceeding with the operation.

**BACK-020: Manual Partial Schema**
- NEVER manually make each field optional when creating an update/patch schema.
- FIX: Use `createSchema.partial()` (Zod), `schema.copy(update=...)` (Pydantic), or equivalent.

### Quality Rules

**API Design:**
- Consistent naming: plural nouns for collections, HTTP verbs for actions.
- Standard status codes: 200 OK, 201 Created, 400 Bad Request, 401/403, 404, 409, 422, 500.
- Versioning strategy from day one. Consistent error response shape.

**Error Handling:**
- Define error hierarchy: base app error, domain errors, infrastructure errors.
- Map internal errors to API responses at the boundary layer only.
- Every async operation needs specific error handling (no bare catch-all).

**Security (OWASP):**
- Validate ALL input at system boundaries. Sanitize output.
- Authentication on every non-public endpoint. Authorization on every data access.
- CORS configured for specific origins only. Security headers set.

**Database:**
- Migrations for all schema changes. Never manual DDL in production.
- Connection pooling. Transaction boundaries match business operations.
- Soft delete with audit trail for user data.
""".strip()

CODE_REVIEW_STANDARDS = r"""
## CODE REVIEW QUALITY STANDARDS (ALWAYS APPLIED)

AI reviewers default to surface-level checks. These standards enforce deep review.

### Review Priority Order
1. **SECURITY** — vulnerabilities, injection, auth bypass, data exposure
2. **CORRECTNESS** — logic errors, edge cases, race conditions, data loss
3. **PERFORMANCE** — N+1 queries, missing indexes, unbounded operations
4. **ARCHITECTURE** — pattern violations, coupling, separation of concerns
5. **TESTING** — coverage gaps, flaky tests, missing edge case tests
6. **STYLE** — naming, formatting, documentation (lowest priority)

NEVER approve code with security issues just because it "works."

### Anti-Patterns (NEVER commit these review failures)

**REVIEW-001: Rubber-Stamp LGTM**
- NEVER approve without reading every changed line. "Looks good" is not a review.

**REVIEW-002: Syntax-Only Review**
- NEVER check only formatting/naming while ignoring logic, edge cases, and security.

**REVIEW-003: Context Blindness**
- NEVER review the diff in isolation. Read surrounding code to understand impact.

**REVIEW-004: Missing Security Check**
- NEVER skip OWASP screening. Check injection, auth, data exposure on every review.

**REVIEW-005: Edge Case Neglect**
- NEVER verify only the happy path. Test: null, empty, boundary, concurrent, error.

**REVIEW-006: Error Path Ignorance**
- NEVER skip tracing failure paths. What happens when the DB is down? API times out?

**REVIEW-007: Hallucinated API Accept**
- NEVER assume API methods exist without verifying. Check that called methods are real.

**REVIEW-008: Cross-File Blindness**
- NEVER ignore how changes impact other files. Check callers, importers, dependents.

**REVIEW-009: Incomplete Requirement**
- NEVER approve partial implementation. Every requirement either FULLY met or FAIL.

**REVIEW-010: Performance Blind Spot**
- NEVER ignore algorithmic complexity. O(n^2) loops, unbounded queries, missing caching.

**REVIEW-011: Test Quality Bypass**
- NEVER accept coverage % without checking test quality. Tests must assert behavior.

**REVIEW-012: Architecture Erosion**
- NEVER accept pattern violations. If the project uses repositories, don't allow direct DB.

**REVIEW-013: Missing Integration Test**
- NEVER skip cross-component verification. Unit tests alone don't catch wiring bugs.

**REVIEW-014: Dependency Blindness**
- NEVER ignore new dependencies. Check for vulnerabilities, license, maintenance status.

**REVIEW-015: Silent Regression**
- NEVER approve without considering if the change breaks existing functionality.

### Severity Classification
Every finding must be classified:
- **CRITICAL** — Security vulnerability, data loss, crash → BLOCKING (must fix before merge)
- **HIGH** — Logic error, missing validation, broken feature → BLOCKING (must fix)
- **MEDIUM** — Performance issue, missing test, pattern violation → Request changes (should fix)
- **LOW** — Style, naming, documentation → Comment (nice to fix, non-blocking)
""".strip()

TESTING_STANDARDS = r"""
## TESTING QUALITY STANDARDS (ALWAYS APPLIED)

AI-generated tests are the single biggest quality gap. These standards enforce meaningful tests.

### Anti-Patterns (NEVER produce these)

**TEST-001: Happy Path Only**
- NEVER test only the success case. Test: errors, edge cases, boundaries, empty, null.

**TEST-002: Phantom Assertions**
- NEVER write tests without real assertions. `assertTrue(true)` or no assert = no test.

**TEST-003: Implementation Testing**
- NEVER test internal method calls or private state. Test BEHAVIOR: input → output.

**TEST-004: Mock Madness**
- NEVER mock everything. If you're testing the mock, you're testing nothing.
- FIX: Mock external dependencies only (APIs, DBs, file system). Use real internal code.

**TEST-005: The Giant**
- NEVER write one test with 15+ unrelated assertions. One behavior per test case.

**TEST-006: Flaky by Design**
- NEVER depend on timing, execution order, random data, or network in tests.
- FIX: Deterministic data, isolated tests, controlled time, mocked external calls.

**TEST-007: No Cleanup**
- NEVER modify shared state (DB, files, globals) without cleanup/reset between tests.

**TEST-008: Unnamed Tests**
- NEVER write `test('test1')` or `def test_it():`. Names must describe the behavior tested.
- FIX: `test('returns 404 when user not found')`, `def test_rejects_expired_token():`.

**TEST-009: Missing Async Handling**
- NEVER let async tests complete before assertions run.
- FIX: Await promises. Use async test utilities. Verify async errors are caught.

**TEST-010: Snapshot Everything**
- NEVER snapshot every output blindly. Snapshots become stale approval stamps.
- FIX: Snapshot stable structures (API contracts). Assert specific values for logic.

**TEST-011: Excessive Setup**
- NEVER require 10+ mocks before testing starts. Flag the code as too coupled.

**TEST-012: Testing the Framework**
- NEVER verify that React renders or Express routes. The framework already tests that.
- FIX: Test YOUR logic — business rules, data transforms, conditional behavior.

**TEST-013: Silent Catcher**
- NEVER wrap test logic in try-catch that swallows errors.
- FIX: Let assertions throw. Use `expect(...).rejects` for expected errors.

**TEST-014: Hardcoded Environment**
- NEVER hardcode ports, absolute paths, or specific dates in tests.
- FIX: Use dynamic ports, relative/temp paths, and relative time.

**TEST-015: No Error Path Tests**
- NEVER test only success. Every API endpoint needs: 400, 401, 403, 404, 500 tests.

### Quality Rules

**Test Structure (AAA):**
- Arrange: Set up test data and mocks.
- Act: Execute the code under test (single action).
- Assert: Verify the expected outcome.
- Each section clearly identifiable. No mixing.

**Naming Convention:**
- `test_[behavior]_when_[condition]_then_[expected]` or
- `it('should [behavior] when [condition]')`.

**Coverage Strategy:**
- Unit tests: business logic, data transforms, validators.
- Integration tests: cross-module flows, database queries, API endpoints.
- Prefer integration tests for wiring verification over mocked unit tests.

**Mocking Strategy:**
- Mock at boundaries: external APIs, databases, file system, time.
- Never mock the module under test.
- If a test needs >5 mocks, the code needs refactoring, not more mocks.
""".strip()

DEBUGGING_STANDARDS = r"""
## DEBUGGING QUALITY STANDARDS (ALWAYS APPLIED)

AI debuggers default to surface-level fixes. These standards enforce root-cause debugging.

### Anti-Patterns (NEVER commit these debugging failures)

**DEBUG-001: Symptom Fixing**
- NEVER add a null check without understanding WHY the value is null.
- FIX: Trace back to the source. Fix the root cause, not the symptom.

**DEBUG-002: Shotgun Debugging**
- NEVER make random changes hoping something works.
- FIX: Form a hypothesis, test it, proceed based on evidence.

**DEBUG-003: No Reproduction**
- NEVER claim a bug is fixed without first reproducing it.
- FIX: Reproduce reliably first. Verify fix eliminates the reproduction.

**DEBUG-004: Skip the Hypothesis**
- NEVER jump to code changes without analyzing the problem first.
- FIX: Read error message → form hypothesis → validate → then fix.

**DEBUG-005: Console.log Only**
- NEVER rely solely on console.log for debugging.
- FIX: Use debuggers, structured logging, profilers, network inspectors as appropriate.

**DEBUG-006: No Regression Test**
- NEVER fix a bug without adding a test that catches the exact failure.
- FIX: Write a failing test first, then fix the code, then verify test passes.

**DEBUG-007: Ignoring Stack Trace**
- NEVER skip reading the full error message and stack trace.
- FIX: Read every frame. The root cause is often several frames deep.

**DEBUG-008: Confirmation Bias**
- NEVER assume the cause without evidence. "It must be X" without proof is dangerous.
- FIX: Let data drive the diagnosis. Test multiple hypotheses.

**DEBUG-009: Broad Error Suppression**
- NEVER add broader try-catch to "fix" errors. You're hiding bugs.
- FIX: Handle specific errors. Let unexpected ones surface and be investigated.

**DEBUG-010: Collateral Damage**
- NEVER ship a fix that breaks other functionality.
- FIX: Run full test suite after fixing. Check callers of modified code.

### 6-Step Debugging Methodology
1. **Reproduce** — Create reliable reproduction steps. Confirm the bug exists.
2. **Hypothesize** — Based on error message, stack trace, and code reading, form theories.
3. **Validate** — Test hypothesis with targeted investigation (logging, breakpoints, tests).
4. **Fix** — Apply the minimum change that addresses the root cause.
5. **Verify** — Confirm the fix resolves the reproduction. Run related tests.
6. **Prevent** — Add regression test. Document root cause for team knowledge.
""".strip()

E2E_TESTING_STANDARDS = r"""
## E2E TESTING QUALITY STANDARDS (APPLIED DURING E2E PHASE)

E2E tests verify the application works from the user's perspective. These standards
prevent common pitfalls that make E2E tests unreliable or meaningless.

### Anti-Patterns (NEVER produce these)

**E2E-001: Hardcoded Timeouts**
- NEVER use setTimeout, time.sleep, or fixed delays in E2E tests.
- FIX: Use waitFor, waitForResponse, waitForSelector, or page.waitForLoadState.

**E2E-002: Hardcoded Ports/URLs**
- NEVER hardcode localhost:3000 or any specific port in test files.
- FIX: Use configurable base URL via process.env.BASE_URL or test config.

**E2E-003: Mock Data in E2E**
- NEVER use mock data, stubs, or fake responses in E2E tests.
- E2E tests must hit the REAL running server with REAL API calls.
- FIX: Start the actual server, seed test data, make real HTTP calls.

**E2E-004: Empty Test Bodies**
- NEVER write test functions with no assertions. An empty test proves nothing.
- FIX: Every test must assert: status codes, response data, visible elements, or navigation state.

**E2E-005: Test Independence**
- NEVER rely on test execution order. Each test must work in isolation.
- FIX: Clean state per test (fresh user, reset DB, clear storage). Use beforeEach/afterEach.

**E2E-006: Fragile Selectors**
- NEVER use CSS class selectors (.btn-primary) or DOM structure (div > span:nth-child(2)).
- FIX: Use stable selectors: data-testid, getByRole, getByText, getByLabel.

**E2E-007: Happy Path Only**
- NEVER test only the success scenario for each workflow.
- FIX: Include both happy path (valid input → success) and error path (invalid input → error message).

**E2E-008: No Server Lifecycle**
- NEVER assume the server is already running. Tests must manage server startup/shutdown.
- FIX: Use webServer config (Playwright) or beforeAll/afterAll hooks to start/stop server.

**E2E-009: Weak API Assertions**
- NEVER assert only response status (200 OK) without checking the body.
- FIX: Verify response status + body structure + data integrity (correct values, not just shape).

**E2E-010: Missing Visual Verification**
- NEVER skip verifying that UI elements are actually visible after actions.
- FIX: After navigation, verify element visible. After form submit, verify success state.
  Use toBeVisible(), toHaveText(), toHaveURL() assertions.
""".strip()

ARCHITECTURE_QUALITY_STANDARDS = r"""
## ARCHITECTURE QUALITY STANDARDS (ALWAYS APPLIED)

AI architects reproduce tutorial-level architecture. These standards enforce production patterns.

### Quality Rules

**File Structure:**
- Prefer grouping by feature over type: `/features/auth/` not `/controllers/ + /models/ + /services/`.
- Each feature directory contains its routes, services, models, tests.
- Shared code in `/shared/` or `/common/` only when genuinely reused by 3+ features.

**Error Handling Architecture:**
- Define error hierarchy upfront: base app error → domain errors → infrastructure errors.
- Each layer catches its own errors and wraps for the layer above.
- API boundary maps all errors to standard HTTP responses.
- Never let infrastructure errors (DB, network) leak to clients.

**Dependency Flow:**
- Dependencies flow ONE direction: UI → Application → Domain → Infrastructure.
- No circular imports. No infrastructure code importing from UI.
- External services behind interfaces (repository pattern, adapter pattern).
- Dependency injection or factory pattern for testability.

**Scalability:**
- Design for N+1 avoidance from the start. Batch operations where possible.
- Pagination built into every list endpoint. No unbounded queries.
- Caching strategy documented: what to cache, TTL, invalidation.
- Async processing for anything >100ms (email, file processing, external API calls).

**Backward Compatibility:**
- Additive changes only for public APIs (new fields, new endpoints).
- Breaking changes require versioning and migration path.
- Database migrations should be reversible where possible; use multi-step migrations for destructive changes.
- Feature flags for gradual rollouts.

**Shared Utilities:**
- Identify helpers needed by 2+ files at architecture time — place in /lib/ or /utils/.
- Every route/component file that duplicates a helper is an architecture failure.
- Shared module created in first coding wave; consumers import from it.
""".strip()

DATABASE_INTEGRITY_STANDARDS = r"""## DATABASE INTEGRITY QUALITY STANDARDS

### Anti-Patterns (NEVER produce these)

**DB-001: Enum Type Mismatch (ORM vs Raw SQL)**
- NEVER compare an enum column as an integer in raw SQL when the ORM stores it as a string (or vice versa).
- The ORM model type and raw query comparison type MUST match exactly.
- FIX: Use the same type representation in both ORM and raw queries. If ORM uses string enum, raw SQL must compare to strings.

**DB-002: Boolean Type Mismatch (ORM vs Raw SQL)**
- NEVER compare a boolean column as 0/1 in raw SQL when the ORM stores it as true/false (or vice versa).
- FIX: Match the database engine's boolean representation consistently. Use parameterized queries.

**DB-003: DateTime Format Mismatch**
- NEVER hardcode date format strings in raw SQL that differ from the ORM's serialization format.
- FIX: Use parameterized queries for dates. Let the ORM/driver handle serialization.

**DB-004: Missing Default Value**
- NEVER leave boolean or enum properties without an explicit default in entity/model definitions.
- Every boolean MUST have `= false` or `= true`. Every enum MUST have a default member.
- FIX: Add explicit defaults to all boolean and enum properties.

**DB-005: Nullable Property Without Null Check**
- NEVER access a nullable property without a null guard.
- `entity.NullableField.Method()` without `?.` or null check = NullReferenceException.
- FIX: Use null-conditional access (`?.`) or explicit null checks before property access.

**DB-006: FK Without Navigation Property**
- NEVER leave a FK column (`TenderId`, `UserId`) without a corresponding navigation property.
- Without navigation, eager loading (`Include()`) silently returns null.
- FIX: Add navigation property matching the FK name (minus the `Id` suffix).

**DB-007: Navigation Property Without Inverse**
- ALWAYS define the inverse navigation when using navigation properties.
- Without inverse, the ORM cannot properly track changes in both directions.
- FIX: Add `ICollection<Child>` on the parent and parent reference on the child.

**DB-008: FK With No Relationship Configuration**
- NEVER rely on convention-only FK detection for complex relationships.
- Without explicit `.HasMany().WithOne()` or `@relation`, the ORM may not generate correct cascade behavior.
- FIX: Add explicit relationship configuration in entity configuration classes.

### Quality Rules

**Seed Data Completeness:**
- ALL seeded records MUST satisfy the application's standard query filters.
- If the user listing filters on `isActive=true`, seeded users MUST have `isActive=true`.
- Every role defined in the system MUST have at least one seeded account.

**Enum/Status Registry:**
- Every entity with a status/enum field MUST have a complete registry of valid values.
- The DB representation, API representation, and frontend representation MUST be documented.
- State transitions MUST be explicitly defined (which transitions are valid, which are not).
""".strip()

API_CONTRACT_STANDARDS = r"""
## API Contract Verification Standards

### API-001: Backend DTO Field Missing
**Severity:** error
The backend DTO/model class is missing a field that is specified in the SVC-xxx wiring table.
Every field listed in the Response DTO schema must exist as a property in the backend class.
For C# backends, verify PascalCase property names (they serialize to camelCase JSON).

### API-002: Frontend Model Field Mismatch
**Severity:** error
The frontend model/interface uses a different field name than specified in the SVC-xxx wiring table.
Field names must EXACTLY match the contract — no renaming, aliasing, or re-casing.
For TypeScript consuming C# APIs: use the camelCase serialized form, not PascalCase.

### API-003: Type Mismatch
**Severity:** warning
A field's type in the backend or frontend doesn't match the SVC-xxx contract.
Common issues: using `string` for numeric IDs, missing enum mappers, raw Date vs ISO string.
""".strip()


_AGENT_STANDARDS_MAP: dict[str, list[str]] = {
    "code-writer": [FRONTEND_STANDARDS, BACKEND_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS],
    "code-reviewer": [CODE_REVIEW_STANDARDS, DATABASE_INTEGRITY_STANDARDS, API_CONTRACT_STANDARDS],
    "test-runner": [TESTING_STANDARDS, E2E_TESTING_STANDARDS],
    "debugger": [DEBUGGING_STANDARDS],
    "architect": [ARCHITECTURE_QUALITY_STANDARDS, DATABASE_INTEGRITY_STANDARDS],
}


def get_standards_for_agent(agent_name: str) -> str:
    """Return concatenated quality standards for the given agent.

    Returns an empty string for agents without quality standards
    (planner, researcher, task-assigner, security-auditor, etc.).
    """
    standards = _AGENT_STANDARDS_MAP.get(agent_name, [])
    return "\n\n".join(standards) if standards else ""
