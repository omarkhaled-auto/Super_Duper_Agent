import subprocess, os, glob

print("=== Search for claude executable ===")
# Check common npm global paths
npm_paths = glob.glob("/mnt/c/Users/Omar Khaled/AppData/Roaming/npm/claude*")
print(f"npm global: {npm_paths}")

# Check node_modules/.bin
node_paths = glob.glob("/mnt/c/Users/Omar Khaled/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/cli*")
print(f"node_modules: {node_paths[:5]}")

# Look in Program Files
for d in ["/mnt/c/Program Files", "/mnt/c/Program Files (x86)"]:
    claudes = glob.glob(f"{d}/**/claude*", recursive=False)
    if claudes:
        print(f"  {d}: {claudes[:5]}")

# Check if claude is an npm package
try:
    r = subprocess.run(
        ["node.exe", "-e", "console.log(require.resolve('@anthropic-ai/claude-code'))"],
        capture_output=True, text=True, timeout=10
    )
    print(f"node resolve: {r.stdout.strip()}")
except Exception as e:
    print(f"node resolve: {e}")

# Look for .venv or venv directories
print("\n=== Virtual environments ===")
venv_patterns = [
    "/mnt/c/Projects/claude-agent-team/.venv",
    "/mnt/c/Projects/claude-agent-team/venv",
    "/mnt/c/Projects/claude-agent-team/.env",
    "/mnt/c/Users/Omar Khaled/OneDrive/Desktop/claude-agent-team/.venv",
    "/mnt/c/Users/Omar Khaled/OneDrive/Desktop/claude-agent-team/venv",
]
for p in venv_patterns:
    exists = os.path.isdir(p)
    if exists:
        # Check for python in it
        py = os.path.join(p, "Scripts", "python.exe")
        py2 = os.path.join(p, "bin", "python3")
        print(f"  {p}: EXISTS (python.exe={os.path.isfile(py)}, python3={os.path.isfile(py2)})")
    else:
        print(f"  {p}: NOT FOUND")

# Check pip list in Windows Python for agent-team or claude
print("\n=== pip packages (Python 3.11) ===")
try:
    r = subprocess.run(
        ["python.exe", "-m", "pip", "list", "--format=columns"],
        capture_output=True, text=True, timeout=30
    )
    lines = r.stdout.strip().split("\n")
    relevant = [l for l in lines if any(k in l.lower() for k in ["agent", "claude", "anthropic", "sdk"])]
    print(f"  Total packages: {len(lines)}")
    print(f"  Relevant: {relevant}")
except Exception as e:
    print(f"  pip list error: {e}")

# Check pip list in Python 3.13
print("\n=== pip packages (Python 3.13) ===")
py313 = "/mnt/c/Users/Omar Khaled/AppData/Local/Programs/Python/Python313/python.exe"
try:
    r = subprocess.run(
        [py313, "-m", "pip", "list", "--format=columns"],
        capture_output=True, text=True, timeout=30
    )
    lines = r.stdout.strip().split("\n")
    relevant = [l for l in lines if any(k in l.lower() for k in ["agent", "claude", "anthropic", "sdk"])]
    print(f"  Total packages: {len(lines)}")
    print(f"  Relevant: {relevant}")
except Exception as e:
    print(f"  pip list error: {e}")

# Check WSL pip
print("\n=== pip packages (WSL Python 3.12) ===")
try:
    r = subprocess.run(
        ["python3", "-m", "pip", "list", "--format=columns"],
        capture_output=True, text=True, timeout=30
    )
    lines = r.stdout.strip().split("\n")
    relevant = [l for l in lines if any(k in l.lower() for k in ["agent", "claude", "anthropic", "sdk"])]
    print(f"  Total packages: {len(lines)}")
    print(f"  Relevant: {relevant}")
except Exception as e:
    print(f"  pip list error: {e}")

# Check DeepAgent
print("\n=== DeepAgent (from PATH) ===")
deep = "/mnt/c/Program Files/DeepAgent/bin"
if os.path.isdir(deep):
    print(f"  Contents: {os.listdir(deep)[:10]}")

print("\n=== DONE ===")
