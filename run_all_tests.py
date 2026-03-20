"""
Batch-run the detector on all test images and print a summary report.
"""
import subprocess
import sys
from pathlib import Path

test_images = sorted(Path("test_images").glob("*.jpg"))

if not test_images:
    print("No test images found. Run: python generate_test_images.py")
    sys.exit(1)

print(f"Running detector on {len(test_images)} test images...\n")

for img_path in test_images:
    print(f"\n{'─'*55}")
    subprocess.run(
        [sys.executable, "detector.py", "--image", str(img_path), "--no-show", "--ppm", "3.0"],
        check=False
    )

print(f"\n{'='*55}")
print("  All tests complete. Check *_result.jpg for annotated outputs.")
