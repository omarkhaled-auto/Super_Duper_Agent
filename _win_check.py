import subprocess, os

print("=== Windows Python paths ===")
py_paths = [
    "/mnt/c/Users/Omar Khaled/AppData/Local/Programs/Python/Python313/python.exe",
    "/mnt/c/Users/Omar Khaled/AppData/Local/Programs/Python/Python311/python.exe",
]

for p in py_paths:
    if os.path.isfile(p):
        try:
            r = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=10)
            print(f"  {p}: {r.stdout.strip()} (exit {r.returncode})")
        except Exception as e:
            print(f"  {p}: Error {e}")
    else:
        print(f"  {p}: NOT FOUND")

# Try python.exe via PATH (Windows interop)
print("\n=== Windows python.exe interop ===")
try:
    r = subprocess.run(["python.exe", "--version"], capture_output=True, text=True, timeout=10)
    print(f"python.exe: {r.stdout.strip()} (exit {r.returncode})")
except Exception as e:
    print(f"python.exe: {e}")

# Try running agent-team with Windows Python
print("\n=== agent-team with Windows Python ===")
for p in py_paths:
    if os.path.isfile(p):
        try:
            r = subprocess.run(
                [p, "-m", "agent_team", "--help"],
                capture_output=True, text=True, timeout=15,
                cwd="/mnt/c/Projects/claude-agent-team"
            )
            print(f"  {p}: exit {r.returncode}")
            if r.stdout:
                print(f"    stdout: {r.stdout[:300]}")
            if r.stderr:
                print(f"    stderr: {r.stderr[:300]}")
        except Exception as e:
            print(f"  {p}: Error {e}")

# Check if claude.exe exists
print("\n=== Claude CLI ===")
claude_paths = [
    "/mnt/c/Users/Omar Khaled/.claude/local/claude.exe",
    "/mnt/c/Users/Omar Khaled/AppData/Local/Programs/claude/claude.exe",
    "/mnt/c/Program Files/claude/claude.exe",
]
for p in claude_paths:
    print(f"  {p}: {'EXISTS' if os.path.isfile(p) else 'NOT FOUND'}")

# Check npm global
try:
    r = subprocess.run(["npm.cmd", "root", "-g"], capture_output=True, text=True, timeout=10)
    npm_global = r.stdout.strip()
    print(f"\nnpm global: {npm_global}")
    claude_npm = os.path.join(npm_global, ".bin", "claude.exe")
    print(f"  claude via npm: {'EXISTS' if os.path.isfile(claude_npm) else 'NOT FOUND'}")
except Exception as e:
    print(f"\nnpm check: {e}")

# Check Windows ANTHROPIC_API_KEY more thoroughly
print("\n=== API Key deep check ===")
try:
    r = subprocess.run(
        ["powershell.exe", "-Command",
         "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')"],
        capture_output=True, text=True, timeout=10
    )
    val = r.stdout.strip()
    if val:
        print(f"User env: {val[:12]}...")
    else:
        print("User env: NOT SET")
except Exception as e:
    print(f"User env check: {e}")

try:
    r = subprocess.run(
        ["powershell.exe", "-Command",
         "[System.Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'Machine')"],
        capture_output=True, text=True, timeout=10
    )
    val = r.stdout.strip()
    if val:
        print(f"Machine env: {val[:12]}...")
    else:
        print("Machine env: NOT SET")
except Exception as e:
    print(f"Machine env check: {e}")

print("\n=== DONE ===")
