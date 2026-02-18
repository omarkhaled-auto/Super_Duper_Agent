import subprocess, os

# Check claude version
r = subprocess.run(
    [r"C:\Users\Omar Khaled\AppData\Roaming\npm\claude.CMD", "--version"],
    capture_output=True, text=True, timeout=15
)
print(f"Claude CLI version: {r.stdout.strip()} (exit {r.returncode})")
if r.stderr:
    print(f"  stderr: {r.stderr.strip()[:200]}")

# Check if already authenticated by trying a simple operation
r2 = subprocess.run(
    [r"C:\Users\Omar Khaled\AppData\Roaming\npm\claude.CMD", "api-key"],
    capture_output=True, text=True, timeout=15
)
print(f"\nclaude api-key: exit {r2.returncode}")
print(f"  stdout: {r2.stdout.strip()[:200]}")
print(f"  stderr: {r2.stderr.strip()[:200]}")

# Check if claude is available on the WSL side too
import shutil
wsl_claude = shutil.which("claude")
print(f"\nWSL claude: {wsl_claude}")

# Check .claude config directory for auth state
config_dir = os.path.expanduser(r"~\.claude")
win_config = r"C:\Users\Omar Khaled\.claude"
print(f"\n.claude dir (Python home): {config_dir}, exists: {os.path.isdir(config_dir)}")
print(f".claude dir (Windows): {win_config}, exists: {os.path.isdir(win_config)}")

if os.path.isdir(win_config):
    for f in os.listdir(win_config):
        full = os.path.join(win_config, f)
        if os.path.isfile(full):
            size = os.path.getsize(full)
            print(f"  {f} ({size} bytes)")

# Try running agent-team with the new install
print("\n=== Test agent-team module ===")
r3 = subprocess.run(
    ["python.exe", "-m", "agent_team", "--version"],
    capture_output=True, text=True, timeout=15,
    cwd=r"C:\Projects\claude-agent-team"
)
print(f"agent-team --version: exit {r3.returncode}")
print(f"  stdout: {r3.stdout.strip()[:200]}")
print(f"  stderr: {r3.stderr.strip()[:200]}")
