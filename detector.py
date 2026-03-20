"""
Object Dimension Detector
=========================
Algorithm: Classical Computer Vision (OpenCV)
- Contour detection  → object bounding box (Width × Height)
- Hough Circles + contour hierarchy → hole dimensions
- Pixel-per-metric calibration via A4 reference sheet OR manual entry

Usage:
  python detector.py --image <path>        # measure from saved image
  python detector.py --camera              # capture from webcam then measure
  python detector.py --demo               # run on generated test image
"""

import cv2
import numpy as np
import argparse
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ─────────────────────────────────────────────
#  CALIBRATION
#  Default: pixels-per-millimeter from an A4
#  sheet placed next to the object.
#  A4 = 297 × 210 mm.  Adjust if you use a
#  different known reference.
# ─────────────────────────────────────────────
A4_WIDTH_MM  = 210.0   # short edge
A4_HEIGHT_MM = 297.0   # long edge

PIXELS_PER_MM_DEFAULT = None   # calibrated at runtime


# ─── helpers ──────────────────────────────────

def preprocess(image: np.ndarray) -> np.ndarray:
    """Grayscale → Gaussian blur → adaptive threshold → morphology clean-up."""
    gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (7, 7), 0)
    # Otsu thresholding (works well for objects on contrasting backgrounds)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Close small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, binary, iterations=2)
    return binary


def find_object_contour(binary: np.ndarray):
    """Return the largest external contour (assumed = the object)."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    # Largest by area, ignoring very small noise
    valid = [c for c in contours if cv2.contourArea(c) > 1000]
    if not valid:
        return None
    return max(valid, key=cv2.contourArea)


def detect_holes(gray: np.ndarray, binary: np.ndarray, object_contour):
    """
    Detect holes inside the object using two complementary methods:
      1. Hough Circle Transform  (fast, good for round holes)
      2. Contour hierarchy       (catches non-circular holes too)
    Returns list of dicts with keys: 'type', 'bbox' (x,y,w,h), 'center', 'radius'(opt)
    """
    holes = []
    h_img, w_img = gray.shape[:2]

    # --- Method 1: Hough Circles ---
    blur = cv2.GaussianBlur(gray, (9, 9), 2)
    min_r = max(5,  min(h_img, w_img) // 60)
    max_r = max(20, min(h_img, w_img) // 8)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_r * 3,
        param1=80,
        param2=30,
        minRadius=min_r,
        maxRadius=max_r,
    )
    if circles is not None:
        circles = np.round(circles[0]).astype(int)
        for (cx, cy, r) in circles:
            # Only keep circles inside the object contour
            if object_contour is not None:
                if cv2.pointPolygonTest(object_contour, (float(cx), float(cy)), False) < 0:
                    continue
            holes.append({
                "type"  : "circular",
                "center": (cx, cy),
                "radius": r,
                "bbox"  : (cx - r, cy - r, 2 * r, 2 * r),
            })

    # --- Method 2: Contour hierarchy (catches non-circular holes) ---
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is not None:
        hierarchy = hierarchy[0]
        for i, (cnt, h) in enumerate(zip(contours, hierarchy)):
            parent = h[3]
            if parent < 0:
                continue   # external contour, skip
            area = cv2.contourArea(cnt)
            if area < 200:
                continue   # noise
            x, y, w, w_h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + w_h // 2
            # Check it's inside the main object
            if object_contour is not None:
                if cv2.pointPolygonTest(object_contour, (float(cx), float(cy)), False) < 0:
                    continue
            # Avoid duplicating with Hough results
            already = any(
                abs(hh["center"][0] - cx) < 15 and abs(hh["center"][1] - cy) < 15
                for hh in holes
            )
            if already:
                continue
            aspect = w / max(w_h, 1)
            holes.append({
                "type"  : "circular" if 0.7 < aspect < 1.3 else "rectangular",
                "center": (cx, cy),
                "radius": min(w, w_h) // 2,
                "bbox"  : (x, y, w, w_h),
            })

    return holes


def calibrate_ppm(image: np.ndarray):
    """
    Auto-calibrate pixels-per-mm by finding the largest rectangle
    that matches A4 proportions (±15%).  Falls back to manual entry.
    """
    gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur   = cv2.GaussianBlur(gray, (7, 7), 0)
    edges  = cv2.Canny(blur, 30, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_ppm = None
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            ratio = w / max(h, 1)
            a4_ratio = A4_WIDTH_MM / A4_HEIGHT_MM   # ~0.707
            if abs(ratio - a4_ratio) < 0.15 * a4_ratio or abs(ratio - 1/a4_ratio) < 0.15:
                ppm_w = w / A4_WIDTH_MM
                ppm_h = h / A4_HEIGHT_MM
                best_ppm = (ppm_w + ppm_h) / 2
                print(f"[CAL] A4 reference detected  →  {best_ppm:.3f} px/mm")
                break

    if best_ppm is None:
        print("\n[CAL] Could not auto-detect A4 reference sheet.")
        print("      Place a credit card (85.6 × 54 mm) or A4 sheet next to the object.")
        try:
            val = input("      Enter known pixel width of reference object (or press Enter to skip): ").strip()
            if val:
                mm  = float(input("      Width in mm: ").strip())
                best_ppm = float(val) / mm
                print(f"[CAL] Manual calibration  →  {best_ppm:.3f} px/mm")
        except Exception:
            pass

    return best_ppm


def px_to_mm(px, ppm):
    if ppm and ppm > 0:
        return px / ppm
    return None


# ─── measurement ──────────────────────────────

def measure(image_path: str, show: bool = True, ppm_override: float = None):
    """Full pipeline: load → calibrate → measure → visualise."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"[ERROR] Cannot open '{image_path}'")
        return

    print(f"\n{'='*55}")
    print(f"  Image : {Path(image_path).name}")
    print(f"  Size  : {image.shape[1]} × {image.shape[0]} px")
    print(f"{'='*55}")

    # 1. Calibration
    ppm = ppm_override or calibrate_ppm(image)
    unit = "mm" if ppm else "px"

    def fmt(px_val):
        if ppm:
            return f"{px_to_mm(px_val, ppm):.1f} {unit}"
        return f"{px_val} {unit}"

    # 2. Pre-process
    binary = preprocess(image)
    gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Find main object
    obj_cnt = find_object_contour(binary)
    if obj_cnt is None:
        print("[WARN] No object contour found. Try better lighting or contrast.")
        return

    x, y, w, h = cv2.boundingRect(obj_cnt)

    print(f"\n  OBJECT DIMENSIONS")
    print(f"  ├─ Width  : {fmt(w)}")
    print(f"  └─ Height : {fmt(h)}")

    # 4. Find holes
    holes = detect_holes(gray, binary, obj_cnt)
    if holes:
        print(f"\n  HOLES DETECTED : {len(holes)}")
        for i, hole in enumerate(holes, 1):
            hx, hy, hw, hh = hole["bbox"]
            if hole["type"] == "circular":
                diameter = 2 * hole["radius"]
                print(f"  ├─ Hole {i} [circle]  diameter = {fmt(diameter)}"
                      f"  center=({hole['center'][0]}, {hole['center'][1]})")
            else:
                print(f"  ├─ Hole {i} [rect]    {fmt(hw)} × {fmt(hh)}"
                      f"  @ ({hx}, {hy})")
    else:
        print("\n  HOLES : none detected")

    print()

    # 5. Visualise
    if show:
        out = image.copy()

        # Main bounding box
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 200, 0), 2)
        # Width arrow
        mid_y = y + h + 20
        cv2.arrowedLine(out, (x, mid_y), (x + w, mid_y), (0, 200, 0), 2, tipLength=0.05)
        cv2.arrowedLine(out, (x + w, mid_y), (x, mid_y), (0, 200, 0), 2, tipLength=0.05)
        cv2.putText(out, f"W={fmt(w)}", (x + w // 2 - 40, mid_y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 0), 2)
        # Height arrow
        mid_x = x - 30
        cv2.arrowedLine(out, (mid_x, y), (mid_x, y + h), (0, 200, 0), 2, tipLength=0.05)
        cv2.arrowedLine(out, (mid_x, y + h), (mid_x, y), (0, 200, 0), 2, tipLength=0.05)
        cv2.putText(out, f"H={fmt(h)}", (max(0, mid_x - 60), y + h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 0), 2)

        # Holes
        for i, hole in enumerate(holes, 1):
            cx, cy = hole["center"]
            r = hole["radius"]
            cv2.circle(out, (cx, cy), r, (0, 0, 255), 2)
            cv2.circle(out, (cx, cy), 3, (0, 0, 255), -1)
            label = f"H{i} {fmt(2*r)}" if hole["type"] == "circular" else f"H{i}"
            cv2.putText(out, label, (cx - 20, cy - r - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 80, 255), 2)

        # Save annotated result
        result_path = Path(image_path).stem + "_result.jpg"
        cv2.imwrite(result_path, out)
        print(f"  Annotated image saved → {result_path}")

        # Show
        out_rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        plt.figure(figsize=(10, 7))
        plt.imshow(out_rgb)
        plt.title("Object Dimension Detection", fontsize=14)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(Path(image_path).stem + "_annotated.png", dpi=120)
        plt.show()


# ─── camera capture ───────────────────────────

def capture_from_camera(output_path: str = "captured.jpg") -> str:
    """Open webcam, preview, press SPACE to capture, ESC to cancel."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] No webcam found.")
        return None

    print("\n[CAM] Press SPACE to capture  |  ESC to cancel")
    captured = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Overlay guide
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 255), 2)
        cv2.putText(frame, "Place object inside box", (w//4, h//4 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, "SPACE=capture  ESC=quit", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.imshow("Camera - Object Dimension Detector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 32:   # SPACE
            cv2.imwrite(output_path, frame)
            captured = output_path
            print(f"[CAM] Captured → {output_path}")
            break
        elif key == 27:  # ESC
            print("[CAM] Cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured


# ─── demo mode ────────────────────────────────

def create_demo_image(path: str = "demo_object.jpg"):
    """
    Synthesise a test image: white background, grey rectangular plate,
    two circular holes, one rectangular slot.
    """
    img = np.ones((600, 800, 3), dtype=np.uint8) * 240  # light grey bg

    # Main object (dark plate)
    cv2.rectangle(img, (150, 100), (650, 500), (80, 80, 80), -1)
    cv2.rectangle(img, (150, 100), (650, 500), (50, 50, 50), 3)

    # Circular hole 1
    cv2.circle(img, (280, 250), 45, (240, 240, 240), -1)
    cv2.circle(img, (280, 250), 45, (200, 200, 200), 2)

    # Circular hole 2
    cv2.circle(img, (520, 250), 35, (240, 240, 240), -1)
    cv2.circle(img, (520, 250), 35, (200, 200, 200), 2)

    # Rectangular slot
    cv2.rectangle(img, (330, 380), (470, 430), (240, 240, 240), -1)
    cv2.rectangle(img, (330, 380), (470, 430), (200, 200, 200), 2)

    # Add slight noise for realism
    noise = np.random.randint(-15, 15, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(path, img)
    print(f"[DEMO] Test image created → {path}")
    return path


# ─── CLI ──────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Object Dimension Detector (OpenCV)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--image",  "-i", help="Path to an existing image file")
    group.add_argument("--camera", "-c", action="store_true", help="Capture from webcam")
    group.add_argument("--demo",   "-d", action="store_true", help="Run on a synthetic demo image")
    ap.add_argument("--ppm", type=float, default=None,
                    help="Manual pixels-per-mm calibration (skip auto-detect)")
    ap.add_argument("--no-show", action="store_true", help="Skip interactive display")
    args = ap.parse_args()

    if args.demo:
        path = create_demo_image()
        measure(path, show=not args.no_show, ppm_override=args.ppm)

    elif args.camera:
        path = capture_from_camera()
        if path:
            measure(path, show=not args.no_show, ppm_override=args.ppm)

    elif args.image:
        if not os.path.exists(args.image):
            print(f"[ERROR] File not found: {args.image}")
            sys.exit(1)
        measure(args.image, show=not args.no_show, ppm_override=args.ppm)


if __name__ == "__main__":
    main()
