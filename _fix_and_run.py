import subprocess, os, glob, sys

# 1. Check if old source still exists
old_path = "/mnt/c/Users/Omar Khaled/OneDrive/Desktop/claude-agent-team"
new_path = "/mnt/c/Projects/claude-agent-team"
print(f"Old path exists: {os.path.isdir(old_path)}")
print(f"New path exists: {os.path.isdir(new_path)}")

# 2. Check what agent-team resolves to currently
try:
    r = subprocess.run(
        ["python.exe", "-c", "import agent_team; print(agent_team.__file__)"],
        capture_output=True, text=True, timeout=10,
        cwd="/mnt/c/Projects/claude-agent-team"
    )
    print(f"agent_team.__file__: {r.stdout.strip()}")
    print(f"  stderr: {r.stderr.strip()[:200]}")
except Exception as e:
    print(f"Check failed: {e}")

# 3. Try running agent-team with python.exe from C:\Projects\claude-agent-team
print("\n=== Try python.exe -m agent_team ===")
try:
    r = subprocess.run(
        ["python.exe", "-m", "agent_team", "--version"],
        capture_output=True, text=True, timeout=15,
        cwd="/mnt/c/Projects/claude-agent-team"
    )
    print(f"exit: {r.returncode}")
    print(f"stdout: {r.stdout[:200]}")
    print(f"stderr: {r.stderr[:200]}")
except Exception as e:
    print(f"Error: {e}")

# 4. Search for claude CLI more aggressively
print("\n=== Claude CLI search ===")
search_dirs = [
    "/mnt/c/Users/Omar Khaled/.claude",
    "/mnt/c/Users/Omar Khaled/AppData/Local",
    "/mnt/c/Users/Omar Khaled/AppData/Roaming/npm",
]
for d in search_dirs:
    if os.path.isdir(d):
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.lower().startswith("claude") and (f.endswith(".exe") or f.endswith(".cmd")):
                    full = os.path.join(root, f)
                    print(f"  FOUND: {full}")
            # Don't recurse too deep
            depth = root.replace(d, "").count(os.sep)
            if depth > 3:
                dirs.clear()

# 5. Check npm claude-code
print("\n=== npm claude check ===")
try:
    r = subprocess.run(
        ["node.exe", "-e", "try{console.log(require.resolve('@anthropic-ai/claude-code'))}catch(e){console.log('not found')}"],
        capture_output=True, text=True, timeout=10
    )
    print(f"node resolve: {r.stdout.strip()}")
except Exception as e:
    print(f"  Error: {e}")

# npm list global
try:
    r = subprocess.run(
        ["/mnt/c/Program Files/nodejs/npm.cmd", "list", "-g", "--depth=0"],
        capture_output=True, text=True, timeout=15
    )
    lines = [l for l in r.stdout.split("\n") if "claude" in l.lower()]
    print(f"npm global claude: {lines}")
except Exception as e:
    pass

# Try npx
try:
    r = subprocess.run(
        ["/mnt/c/Program Files/nodejs/npx.cmd", "which", "@anthropic-ai/claude-code"],
        capture_output=True, text=True, timeout=10
    )
    print(f"npx: {r.stdout.strip()}")
except Exception as e:
    pass

print("\n=== DONE ===")
