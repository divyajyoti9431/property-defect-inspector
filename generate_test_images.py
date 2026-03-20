"""
Generate a variety of synthetic test images to validate the detector
without needing a physical camera.
"""
import cv2
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("test_images")
OUTPUT_DIR.mkdir(exist_ok=True)


def add_noise(img, level=12):
    noise = np.random.randint(-level, level, img.shape, dtype=np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)


# ── Test 1: Metal plate with two round holes ──────────────────────────────────
def test_metal_plate():
    img = np.ones((640, 960, 3), dtype=np.uint8) * 230
    cv2.rectangle(img, (120, 80), (840, 560), (100, 100, 105), -1)
    cv2.rectangle(img, (120, 80), (840, 560), (60, 60, 65),  4)
    cv2.circle(img, (300, 300), 70,  (230, 230, 230), -1)
    cv2.circle(img, (300, 300), 70,  (190, 190, 190), 2)
    cv2.circle(img, (660, 300), 55,  (230, 230, 230), -1)
    cv2.circle(img, (660, 300), 55,  (190, 190, 190), 2)
    img = add_noise(img)
    path = OUTPUT_DIR / "test1_metal_plate.jpg"
    cv2.imwrite(str(path), img)
    print(f"Created: {path}")


# ── Test 2: Bracket with slot and two small holes ─────────────────────────────
def test_bracket():
    img = np.ones((500, 700, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (80, 60), (620, 440), (70, 75, 80), -1)
    cv2.rectangle(img, (80, 60), (620, 440), (40, 45, 50), 3)
    # Long slot
    cv2.rectangle(img, (200, 180), (500, 240), (200, 200, 200), -1)
    cv2.rectangle(img, (200, 180), (500, 240), (160, 160, 160), 2)
    # Small round holes
    cv2.circle(img, (160, 350), 30, (200, 200, 200), -1)
    cv2.circle(img, (540, 350), 30, (200, 200, 200), -1)
    img = add_noise(img)
    path = OUTPUT_DIR / "test2_bracket.jpg"
    cv2.imwrite(str(path), img)
    print(f"Created: {path}")


# ── Test 3: PCB-like board with multiple holes ────────────────────────────────
def test_pcb():
    img = np.ones((480, 640, 3), dtype=np.uint8) * 210
    cv2.rectangle(img, (60, 50), (580, 430), (30, 90, 30), -1)
    cv2.rectangle(img, (60, 50), (580, 430), (20, 60, 20), 4)
    # Mounting holes (4 corners)
    for cx, cy in [(110, 100), (530, 100), (110, 380), (530, 380)]:
        cv2.circle(img, (cx, cy), 20, (210, 210, 210), -1)
        cv2.circle(img, (cx, cy), 20, (170, 170, 170), 2)
    # Central connector hole
    cv2.rectangle(img, (240, 200), (400, 280), (210, 210, 210), -1)
    cv2.rectangle(img, (240, 200), (400, 280), (170, 170, 170), 2)
    img = add_noise(img, 8)
    path = OUTPUT_DIR / "test3_pcb.jpg"
    cv2.imwrite(str(path), img)
    print(f"Created: {path}")


if __name__ == "__main__":
    test_metal_plate()
    test_bracket()
    test_pcb()
    print("\nAll test images generated in ./test_images/")
