"""Classify Bayan XREF violations by root cause."""
import sys
sys.path.insert(0, "src")
from pathlib import Path
from agent_team.quality_checks import run_endpoint_xref_scan

bayan = Path(r"C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER")
violations = run_endpoint_xref_scan(bayan, scope=None)

function_url = []  # ${this.someFunc(...)} — can't resolve statically
field_var = []     # ${this.someField} — should have been resolved
simple_path = []   # /path/to/thing — true missing endpoint or normalization issue
other = []

for v in violations:
    msg = v.message
    # Extract the URL from the message
    if "calls " in msg:
        call_part = msg.split("calls ")[1].split(" but ")[0]
    else:
        call_part = ""

    if "${this." in call_part and "(" in call_part.split("}")[0]:
        function_url.append(v)
    elif "${this." in call_part or "${self." in call_part:
        field_var.append(v)
    elif "${environment." in call_part or "${" in call_part:
        other.append(v)
    else:
        simple_path.append(v)

print(f"Total violations: {len(violations)}")
print(f"  Function-call URLs (can't resolve): {len(function_url)}")
print(f"  Field variable URLs (should resolve): {len(field_var)}")
print(f"  Simple paths (true missing or FP):   {len(simple_path)}")
print(f"  Other template literals:              {len(other)}")
print()

if simple_path:
    print("Simple path violations (most likely REAL or edge case):")
    for v in simple_path:
        msg = v.message.split("calls ")[1].split(" but ")[0] if "calls " in v.message else ""
        print(f"  {v.check} {msg} [{v.file_path}:{v.line}]")

if field_var:
    print("\nField variable violations (should have been resolved):")
    for v in field_var:
        msg = v.message.split("calls ")[1].split(" but ")[0] if "calls " in v.message else ""
        print(f"  {v.check} {msg} [{v.file_path}:{v.line}]")

if function_url:
    print(f"\nFunction-call URL violations ({len(function_url)} — KNOWN LIMITATION):")
    for v in function_url[:5]:
        msg = v.message.split("calls ")[1].split(" but ")[0] if "calls " in v.message else ""
        print(f"  {v.check} {msg} [{v.file_path}:{v.line}]")
    if len(function_url) > 5:
        print(f"  ... and {len(function_url) - 5} more")
