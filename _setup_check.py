import os, sys, subprocess, shutil

print("=== Claude CLI ===")
claude_path = shutil.which("claude")
print(f"claude in PATH: {claude_path}")

# Try running claude --version
try:
    r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
    print(f"claude --version: {r.stdout.strip()} (exit {r.returncode})")
    if r.stderr:
        print(f"  stderr: {r.stderr.strip()[:200]}")
except Exception as e:
    print(f"claude --version failed: {e}")

print("\n=== Windows ANTHROPIC_API_KEY ===")
# Check if Windows env var is accessible
try:
    r = subprocess.run(
        ["powershell.exe", "-Command", "echo $env:ANTHROPIC_API_KEY"],
        capture_output=True, text=True, timeout=10
    )
    val = r.stdout.strip()
    if val:
        print(f"Windows env: {val[:12]}...")
    else:
        print("Windows env: NOT SET")
except Exception as e:
    print(f"PowerShell check failed: {e}")

print("\n=== agent_team install ===")
# Check if agent_team is importable
try:
    sys.path.insert(0, "/mnt/c/Projects/claude-agent-team/src")
    from agent_team import cli
    print("Import via sys.path OK")
except Exception as e:
    print(f"Import via sys.path: {e}")

# Check if pip installed
try:
    r = subprocess.run([sys.executable, "-m", "pip", "show", "agent-team"],
                      capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        print(f"pip installed: YES")
        for line in r.stdout.split("\n")[:3]:
            print(f"  {line}")
    else:
        print("pip installed: NO")
except Exception as e:
    print(f"pip check failed: {e}")

# Check if running as module works
print("\n=== Module run test ===")
try:
    r = subprocess.run(
        [sys.executable, "-m", "agent_team", "--help"],
        capture_output=True, text=True, timeout=15,
        cwd="/mnt/c/Projects/claude-agent-team"
    )
    print(f"python3 -m agent_team --help: exit {r.returncode}")
    if r.stdout:
        print(f"  stdout (first 200): {r.stdout[:200]}")
    if r.stderr:
        print(f"  stderr (first 200): {r.stderr[:200]}")
except Exception as e:
    print(f"Module run failed: {e}")

print("\n=== DONE ===")
