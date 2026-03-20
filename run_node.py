import subprocess
import sys
import os

script_path = r'C:\Users\divya\OBJECT DETECTION\create_doc.js'
cwd = r'C:\Users\divya\OBJECT DETECTION'

# Try to find node
node_paths = [
    'node',
    r'C:\Program Files\nodejs\node.exe',
    r'C:\Program Files (x86)\nodejs\node.exe',
    os.path.expanduser(r'~\AppData\Roaming\nvm\current\node.exe'),
]

node_cmd = None
for p in node_paths:
    try:
        result = subprocess.run([p, '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            node_cmd = p
            print(f"Found node at: {p}, version: {result.stdout.strip()}")
            break
    except (FileNotFoundError, subprocess.TimeoutExpired):
        continue

if not node_cmd:
    print("ERROR: node not found in common locations")
    sys.exit(1)

print(f"Running: {node_cmd} {script_path}")
result = subprocess.run([node_cmd, script_path], capture_output=True, text=True, cwd=cwd, timeout=60)
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
sys.exit(result.returncode)
