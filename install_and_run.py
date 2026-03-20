"""
Bootstrap: installs all dependencies then immediately runs the demo.
Run this ONCE from Anaconda Prompt:

    python install_and_run.py

"""
import subprocess
import sys
import importlib

PACKAGES = [
    ("cv2",         "opencv-python==4.9.0.80"),
    ("numpy",       "numpy==1.26.4"),
    ("matplotlib",  "matplotlib==3.8.4"),
    ("imutils",     "imutils==0.5.4"),
    ("PIL",         "Pillow==10.3.0"),
    ("scipy",       "scipy==1.13.0"),
]

def pip_install(pkg_name):
    print(f"  Installing {pkg_name} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg_name, "--quiet"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [WARN] pip returned non-zero for {pkg_name}:\n{result.stderr[:300]}")
    else:
        print(f"  ✓ {pkg_name}")

print("=" * 50)
print("  Checking / installing required packages")
print("=" * 50)

for import_name, pip_name in PACKAGES:
    try:
        importlib.import_module(import_name)
        print(f"  ✓ {import_name} already installed")
    except ImportError:
        pip_install(pip_name)

print("\nAll packages ready — launching detector demo...\n")

# Run demo
result = subprocess.run(
    [sys.executable, "detector.py", "--demo"],
    cwd=__file__.rsplit("\\", 1)[0] if "\\" in __file__ else "."
)
sys.exit(result.returncode)
