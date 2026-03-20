"""
Writes a .env file from the current process environment so child
processes (uvicorn workers) can load the Anthropic API key.
"""
import os, sys
from pathlib import Path

key = os.environ.get("ANTHROPIC_API_KEY", "")
if not key:
    print("ERROR: ANTHROPIC_API_KEY is not set in the current environment.")
    print("Please set it before running the app:")
    print("  set ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)

env_path = Path(".env")
lines = []

# Keep existing non-ANTHROPIC lines if .env already exists
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if not line.startswith("ANTHROPIC_API_KEY"):
            lines.append(line)

lines.append(f"ANTHROPIC_API_KEY={key}")

env_path.write_text("\n".join(lines) + "\n")
print(f"[OK] .env written with ANTHROPIC_API_KEY ({key[:12]}...)")
