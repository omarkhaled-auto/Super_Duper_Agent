import subprocess, os

print("Installing @anthropic-ai/claude-code via npm...")

# Use cmd.exe to run npm since .cmd files don't work in WSL bash
r = subprocess.run(
    ["cmd.exe", "/c", "npm install -g @anthropic-ai/claude-code"],
    capture_output=True, text=True, timeout=300,
    cwd="C:\\Projects\\claude-agent-team"
)

print(f"Exit code: {r.returncode}")
if r.stdout:
    print(f"STDOUT:\n{r.stdout[-2000:]}")
if r.stderr:
    print(f"STDERR:\n{r.stderr[-2000:]}")

# Verify installation
print("\n=== Verify ===")
r2 = subprocess.run(
    ["cmd.exe", "/c", "claude --version"],
    capture_output=True, text=True, timeout=15
)
print(f"claude --version: {r2.stdout.strip()} (exit {r2.returncode})")
if r2.stderr:
    print(f"  stderr: {r2.stderr.strip()[:200]}")
