import os, sys, pathlib

print("=== Python ===")
print(f"Version: {sys.version}")
print(f"Exec: {sys.executable}")

print("\n=== API Key ===")
key = os.environ.get("ANTHROPIC_API_KEY", "")
if key:
    print(f"SET: {key[:12]}...")
else:
    print("NOT SET!")
    # Check .env file
    env_path = pathlib.Path("/mnt/c/Projects/claude-agent-team/.env")
    if env_path.exists():
        print(f".env file exists at {env_path}")
        for line in env_path.read_text().strip().split("\n"):
            if "ANTHROPIC" in line:
                k, v = line.split("=", 1)
                print(f"  {k}={v[:12]}...")

print("\n=== Super-team ===")
st = pathlib.Path("/mnt/c/Projects/super-team/src")
if st.exists():
    dirs = sorted([d.name for d in st.iterdir() if d.is_dir()])
    print(f"src/ directories: {dirs}")
else:
    print(f"NOT FOUND: {st}")

print("\n=== Agent-team-v15 ===")
at = pathlib.Path("/mnt/c/Projects/agent-team-v15/src/agent_team")
if at.exists():
    files = sorted([f.name for f in at.iterdir() if f.is_file()])
    print(f"agent_team files: {files[:15]}...")
else:
    print(f"NOT FOUND: {at}")

print("\n=== .agent-team stale state ===")
stale = pathlib.Path("/mnt/c/Projects/super-team/.agent-team")
print(f"Exists: {stale.exists()}")

print("\n=== agent-team module ===")
try:
    from agent_team import cli
    print("Import OK")
except Exception as e:
    print(f"Import error: {e}")
