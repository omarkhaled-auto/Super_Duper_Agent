"""Validate v12 XREF extraction bug fixes against real codebases."""
import sys
sys.path.insert(0, "src")
from pathlib import Path
from agent_team.quality_checks import (
    _normalize_api_path,
    _extract_frontend_http_calls,
    _extract_backend_routes_dotnet,
    _extract_backend_routes_express,
    run_endpoint_xref_scan,
)

# ---- BUG-3 fix: base URL variable stripping ----
print("=" * 60)
print("BUG-3 FIX VALIDATION: Base URL variable stripping")
print("=" * 60)
tests = [
    ("${this.apiUrl}/auth/login", "/auth/login"),
    ("${environment.apiUrl}/tasks", "/tasks"),
    ("${this.baseUrl}/users/${id}", "/users/{param}"),
    ("/tenders/${tenderId}/approval", "/tenders/{param}/approval"),
    ("${this.apiUrl}", "/"),
    ("${this.importUrl(tenderId)}/boq", "/{param}/boq"),  # function call has . so stripped
]
passes = 0
for input_path, expected in tests:
    result = _normalize_api_path(input_path)
    ok = result == expected
    passes += ok
    status = "PASS" if ok else "FAIL"
    print(f"  {status}: {input_path!r} -> {result!r} (expected {expected!r})")
print(f"  Result: {passes}/{len(tests)} passed")
print()

# ---- BUG-5 fix: ASP.NET ~ override ----
print("=" * 60)
print("BUG-5 FIX VALIDATION: ASP.NET ~ route override")
print("=" * 60)
bayan = Path(r"C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER")
if bayan.exists():
    be = _extract_backend_routes_dotnet(bayan, scope=None)
    # Find the exceptions route
    exceptions_routes = [r for r in be if "exceptions" in r.path.lower()]
    print(f"  Backend routes with 'exceptions': {len(exceptions_routes)}")
    for r in exceptions_routes:
        norm = _normalize_api_path(r.path)
        print(f"    {r.method} {r.path} -> norm: {norm} [{r.file_path}:{r.line}]")
        # Should NOT have double prefix like /api/tenders/{param}/evaluation/api/tenders/{param}/exceptions
        if "evaluation" in norm and "exceptions" in norm:
            print("    FAIL: ~ override not working, path has both evaluation AND exceptions")
        else:
            print("    PASS: ~ override correctly separates the path")
else:
    print("  SKIP: Bayan not found")
print()

# ---- BUG-4 fix: Express mount prefix resolution ----
print("=" * 60)
print("BUG-4 FIX VALIDATION: Express mount prefix resolution")
print("=" * 60)
taskflow = Path(r"C:\Users\Omar Khaled\test-projects\taskflow-pro-v10.2")
if taskflow.exists():
    be_express = _extract_backend_routes_express(taskflow, scope=None)
    print(f"  Express routes extracted: {len(be_express)}")
    for r in be_express[:20]:
        norm = _normalize_api_path(r.path)
        has_prefix = r.path.startswith("/api/")
        print(f"    {'OK' if has_prefix else 'NO PREFIX'} {r.method:6s} {r.path:40s} -> {norm} [{r.file_path}:{r.line}]")
    prefix_count = sum(1 for r in be_express if r.path.startswith("/api/"))
    print(f"  Routes with /api/ prefix: {prefix_count}/{len(be_express)}")
    if prefix_count == len(be_express) and len(be_express) > 0:
        print("  PASS: All routes have mount prefix applied")
    elif prefix_count > 0:
        print("  PARTIAL: Some routes have prefix, some don't")
    else:
        print("  FAIL: No routes have mount prefix")
else:
    print("  SKIP: TaskFlow Pro not found")
print()

# ---- BUG-1 + BUG-2 fix: Variable refs + dedup ----
print("=" * 60)
print("BUG-1 + BUG-2 FIX VALIDATION: Variable refs + dedup")
print("=" * 60)
if taskflow.exists():
    fe = _extract_frontend_http_calls(taskflow, scope=None)
    print(f"  Frontend calls extracted: {len(fe)}")
    for c in fe:
        norm = _normalize_api_path(c.path)
        print(f"    {c.method:6s} {c.path:55s} -> {norm} [{c.file_path}:{c.line}]")

    # Check for duplicates (same line+file)
    seen = set()
    dupes = 0
    for c in fe:
        key = (c.file_path, c.line)
        if key in seen:
            dupes += 1
            print(f"    DUPE: {c.method} {c.path} at {c.file_path}:{c.line}")
        seen.add(key)
    print(f"  Duplicates: {dupes} (should be 0)")

    # Check variable resolution
    var_calls = [c for c in fe if not c.path.startswith(("$", "/", "http"))]
    quoted_calls = [c for c in fe if c.path.startswith(("$", "/", "http"))]
    print(f"  Variable-resolved calls: {len(var_calls)}")
    print(f"  Quoted URL calls: {len(quoted_calls)}")
else:
    print("  SKIP: TaskFlow Pro not found")
print()

# ---- Full XREF scan on TaskFlow Pro ----
print("=" * 60)
print("FULL XREF SCAN: TaskFlow Pro")
print("=" * 60)
if taskflow.exists():
    violations = run_endpoint_xref_scan(taskflow, scope=None)
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    {v.check} [{v.severity}] {v.file_path}:{v.line} - {v.message[:80]}")
    if len(violations) == 0:
        print("  PASS: No false positives!")
    else:
        print(f"  CHECK: {len(violations)} violations to review")
else:
    print("  SKIP: TaskFlow Pro not found")
print()

# ---- Full XREF scan on Bayan ----
print("=" * 60)
print("FULL XREF SCAN: Bayan")
print("=" * 60)
if bayan.exists():
    violations = run_endpoint_xref_scan(bayan, scope=None)
    print(f"  Violations: {len(violations)}")
    for v in violations[:15]:
        print(f"    {v.check} [{v.severity}] {v.file_path}:{v.line} - {v.message[:80]}")
    if len(violations) > 15:
        print(f"    ... and {len(violations) - 15} more")
    # Compare to previous: 28 violations (all false positive)
    print(f"  Previous: 28 violations (all FP)")
    print(f"  Now:      {len(violations)} violations")
    improvement = 28 - len(violations)
    print(f"  Improvement: {improvement} fewer violations")
else:
    print("  SKIP: Bayan not found")
