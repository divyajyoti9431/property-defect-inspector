# Object Dimension Detector — Quick Start

## 1. Create & Activate Conda Environment

Open **Anaconda Prompt** and run:

```bash
cd "C:\Users\divya\OBJECT DETECTION"

# Create env from YAML (one-time)
conda env create -f environment.yml

# Activate
conda activate obj-detect
```

---

## 2. Run Modes

### A) Demo mode (no camera needed — uses a synthetic test image)
```bash
python detector.py --demo
```

### B) Your own image
```bash
python detector.py --image path\to\your_photo.jpg
```

### C) Capture from webcam, then measure
```bash
python detector.py --camera
```
> Press **SPACE** to snap, **ESC** to cancel.

---

## 3. Batch test on multiple synthetic images
```bash
# Generate 3 test images (metal plate, bracket, PCB)
python generate_test_images.py

# Run detector on all of them
python run_all_tests.py
```
Annotated results saved as `*_result.jpg` in the same folder.

---

## 4. Calibration (for real-world mm measurements)

Place an **A4 sheet** next to the object in the photo.
The script auto-detects it and computes pixels-per-mm.

Or pass calibration manually:
```bash
python detector.py --image photo.jpg --ppm 3.78
# 3.78 px/mm ≈ 96 DPI scanned image
```

---

## 5. Algorithm Summary

| Step | Technique | Why |
|------|-----------|-----|
| Preprocess | Grayscale → Gaussian blur → Otsu threshold | Robust to lighting |
| Object bbox | Largest external contour → `boundingRect` | Fast, no ML needed |
| Round holes | Hough Circle Transform | Optimised for circles |
| Non-round holes | Contour hierarchy (child contours) | Handles slots/rectangles |
| Scale | A4 reference auto-detect or manual ppm | No expensive sensor needed |

No GPU required. Runs on any machine with OpenCV.
