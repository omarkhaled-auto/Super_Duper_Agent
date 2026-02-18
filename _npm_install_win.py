import subprocess, os, sys

# This runs with Windows Python via python.exe
print("Installing @anthropic-ai/claude-code via npm...")

# Method 1: Use node directly with npm-cli.js
node_path = r"C:\Program Files\nodejs\node.exe"
npm_cli = r"C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js"

if os.path.isfile(node_path) and os.path.isfile(npm_cli):
    print(f"Using node at: {node_path}")
    print(f"Using npm-cli at: {npm_cli}")
    r = subprocess.run(
        [node_path, npm_cli, "install", "-g", "@anthropic-ai/claude-code"],
        capture_output=True, text=True, timeout=300
    )
    print(f"Exit code: {r.returncode}")
    if r.stdout:
        print(f"STDOUT (last 2000):\n{r.stdout[-2000:]}")
    if r.stderr:
        print(f"STDERR (last 2000):\n{r.stderr[-2000:]}")
else:
    print(f"node exists: {os.path.isfile(node_path)}")
    print(f"npm-cli exists: {os.path.isfile(npm_cli)}")

    # Method 2: find npm-cli.js
    for root, dirs, files in os.walk(r"C:\Program Files\nodejs"):
        for f in files:
            if "npm" in f.lower():
                print(f"  Found: {os.path.join(root, f)}")

# Verify
print("\n=== Verify claude CLI ===")
import shutil
claude_path = shutil.which("claude")
print(f"claude in PATH: {claude_path}")

# Check npm global bin
try:
    r = subprocess.run(
        [node_path, npm_cli, "bin", "-g"],
        capture_output=True, text=True, timeout=10
    )
    npm_bin = r.stdout.strip()
    print(f"npm global bin: {npm_bin}")
    claude_exe = os.path.join(npm_bin, "claude.cmd")
    print(f"claude.cmd exists: {os.path.isfile(claude_exe)}")
except Exception as e:
    print(f"Error: {e}")
