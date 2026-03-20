# Object Dimension Detector 📐

A **zero-cost classical Computer Vision** prototype that measures:
- ✅ Object **Width** & **Height** (in mm)
- ✅ **Hole dimensions** — circular bores (Ø diameter) and rectangular slots (W × H)

No GPU, no ML model, no paid API — pure **OpenCV**.

---

## Demo Output

| Original | Hole Mask | Detected Dimensions |
|----------|-----------|---------------------|
| Raw photo of industrial part | Dark-pixel mask inside object | Annotated with W, H, hole Ø |

---

## Algorithm

```
Image Input
    │
    ▼
[1] Multi-scale Canny edges + largest contour fill  →  Object mask
    │
    ▼
[2] boundingRect on mask  →  Width × Height (px → mm)
    │
    ▼
[3] Dark threshold inside mask
    ├── Hough Circle Transform  →  Round holes (Ø diameter)
    └── Contour hierarchy       →  Slots & rectangular holes
    │
    ▼
[4] Annotated output image + terminal report
```

| Step | Technique | Cost |
|------|-----------|------|
| Segmentation | Multi-scale Canny + flood-fill | O(n) |
| Width / Height | `cv2.boundingRect` | O(1) |
| Round holes | `cv2.HoughCircles` | O(n log n) |
| Slot holes | Contour hierarchy | O(n) |
| Scale | Pixels-per-mm (PPM) factor | — |

---

## Setup

### Using Anaconda (recommended)
```bash
conda env create -f environment.yml
conda activate obj-detect
```

### Using pip only
```bash
pip install opencv-python numpy matplotlib imutils Pillow scipy
```

---

## Run

```bash
# Demo — synthetic test image (no camera needed)
python detector.py --demo

# Your own image
python detector.py --image path/to/photo.jpg

# Webcam capture → measure
python detector.py --camera

# Realistic industrial part
python detect_realistic.py

# Batch test
python generate_test_images.py
python run_all_tests.py
```

---

## Calibration (real-world mm)

Place an **A4 sheet** beside the object — auto-detected.

Or supply manually:
```bash
python detector.py --image photo.jpg --ppm 3.78
```
> `3.78 px/mm` ≈ 96 DPI scan. Adjust for your camera/distance.

---

## Project Structure

```
├── detector.py              # Main pipeline (camera / image / demo)
├── detect_realistic.py      # Tuned detector for realistic industrial parts
├── generate_test_images.py  # Synthetic test image generator
├── run_all_tests.py         # Batch runner
├── environment.yml          # Conda environment
└── README.md
```

---

## Requirements

- Python 3.10
- opencv-python 4.9
- numpy, matplotlib, imutils, Pillow, scipy
