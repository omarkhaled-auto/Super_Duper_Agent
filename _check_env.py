import os, sys

# Check CLAUDECODE env var
print(f"CLAUDECODE: {os.environ.get('CLAUDECODE', 'NOT SET')}")
print(f"CLAUDE_CODE: {os.environ.get('CLAUDE_CODE', 'NOT SET')}")

# Check all claude-related env vars
for k, v in sorted(os.environ.items()):
    if 'CLAUDE' in k.upper() or 'ANTHROPIC' in k.upper():
        print(f"  {k}={v[:50] if len(v) > 50 else v}")

# Check if claude CLI works
import subprocess
try:
    r = subprocess.run(['claude', '--version'], capture_output=True, text=True, timeout=10)
    print(f"claude --version: {r.stdout.strip()}")
    print(f"claude stderr: {r.stderr.strip()[:200]}")
except Exception as e:
    print(f"claude error: {e}")

# Check if running inside Claude Code
print(f"TERM: {os.environ.get('TERM', 'NOT SET')}")
print(f"TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'NOT SET')}")
