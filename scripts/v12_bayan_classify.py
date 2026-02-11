"""v12 validation: Classify Bayan frontend calls by pattern type."""
import sys
sys.path.insert(0, "src")
from pathlib import Path
from agent_team.quality_checks import (
    _extract_frontend_http_calls,
    _extract_backend_routes_dotnet,
    _normalize_api_path,
)

bayan = Path(r"C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER")

fe = _extract_frontend_http_calls(bayan, scope=None)
be = _extract_backend_routes_dotnet(bayan, scope=None)

# Classify frontend calls by pattern
function_calls = []  # ${this.someFunction(...)}
variable_calls = []  # ${this.someVar}
simple_paths = []    # /tenders/... (no template var prefix)

for c in fe:
    first_seg = c.path.split("/")[0]
    if "(" in first_seg:
        function_calls.append(c)
    elif "${" in first_seg:
        variable_calls.append(c)
    else:
        simple_paths.append(c)

print(f"Frontend calls by pattern:")
print(f"  Function-based URL: {len(function_calls)}")
print(f"  Variable-based URL: {len(variable_calls)}")
print(f"  Simple path:        {len(simple_paths)}")
print()

# Check which simple-path calls match backend
be_norms = set()
for r in be:
    norm = _normalize_api_path(r.path)
    be_norms.add((r.method, norm))

matched_simple = 0
unmatched_simple = []
for c in simple_paths:
    norm = _normalize_api_path(c.path)
    if (c.method, norm) in be_norms:
        matched_simple += 1
    else:
        unmatched_simple.append(c)

print(f"Simple-path calls: {len(simple_paths)} total, {matched_simple} matched, {len(unmatched_simple)} unmatched")
for c in unmatched_simple:
    norm = _normalize_api_path(c.path)
    svc = c.file_path.split("/")[-1]
    print(f"  UNMATCHED: {c.method} {c.path} -> norm: {norm} [{svc}:{c.line}]")
print()

# Variable-based calls normalization
print(f"Variable-based URLs (normalization issue):")
for c in variable_calls[:10]:
    norm = _normalize_api_path(c.path)
    print(f"  {c.method:6s} {c.path[:60]:60s} -> {norm}")
print()

# Function-based calls normalization
print(f"Function-based URLs (normalization issue):")
for c in function_calls[:10]:
    norm = _normalize_api_path(c.path)
    print(f"  {c.method:6s} {c.path[:60]:60s} -> {norm}")
print()

# Backend routes sample
print(f"Backend routes sample (first 10):")
for r in be[:10]:
    norm = _normalize_api_path(r.path)
    print(f"  {r.method:6s} {r.path[:55]:55s} -> {norm}")
