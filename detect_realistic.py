"""
Dimension Detector — Realistic Industrial Part
===============================================
Optimised pipeline for machined metal parts on contrasting backgrounds.

Algorithm (all classical CV, zero cost):
  Step 1  Canny edges → largest filled contour  → object mask
  Step 2  Bounding rectangle of mask            → Width & Height
  Step 3  Dark-pixel threshold inside mask      → hole candidates
  Step 4  Hough Circles (round holes) +
          Contour hierarchy (slots/rect holes)
  Step 5  Pixel-per-mm scale → real dimensions

Run:
    python detect_realistic.py
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

IMAGE_PATH = "realistic_part.jpg"
PPM        = 3.0          # pixels per mm  (adjust for your real photo)
MM         = lambda px: round(px / PPM, 1)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Segment object from background
# ══════════════════════════════════════════════════════════════════════════════

def segment_object(gray):
    """
    Canny + largest-contour fill.
    Robust to gradients and texture — better than plain Otsu on real photos.
    """
    blur = cv2.GaussianBlur(gray, (9, 9), 0)

    # Multi-scale Canny: merge two threshold pairs → catch both sharp & soft edges
    e1 = cv2.Canny(blur, 20,  80)
    e2 = cv2.Canny(blur, 50, 150)
    edges = cv2.bitwise_or(e1, e2)

    # Dilate to close edge gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges  = cv2.dilate(edges, kernel, iterations=2)

    # Fill the largest closed region → object mask
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    obj_cnt = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [obj_cnt], -1, 255, thickness=cv2.FILLED)

    # Morphological close to seal any gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)),
                             iterations=3)
    return mask, obj_cnt


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Object bounding box
# ══════════════════════════════════════════════════════════════════════════════

def object_bbox(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(cnt), cnt


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Hole detection inside the object
# ══════════════════════════════════════════════════════════════════════════════

def detect_holes(gray, object_mask):
    """
    Inside the object mask, dark pixels = holes.
    Uses Hough Circles (fast, circular) + contour hierarchy (slots).
    """
    # Isolate object interior
    interior = cv2.bitwise_and(gray, gray, mask=object_mask)

    # Threshold for very dark pixels (holes / bores)
    _, dark = cv2.threshold(interior, 55, 255, cv2.THRESH_BINARY_INV)
    # Remove background leakage
    dark = cv2.bitwise_and(dark, dark, mask=object_mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    dark   = cv2.morphologyEx(dark, cv2.MORPH_OPEN,  kernel, iterations=1)
    dark   = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, kernel, iterations=2)

    holes = []

    # ── Hough Circles (round holes) ───────────────────────────────────────────
    h_img, w_img = gray.shape
    blur = cv2.GaussianBlur(gray, (11, 11), 2)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp       = 1.2,
        minDist  = 30,
        param1   = 60,
        param2   = 25,
        minRadius= 10,
        maxRadius= 120,
    )

    obj_cnts, _ = cv2.findContours(object_mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    obj_cnt = max(obj_cnts, key=cv2.contourArea) if obj_cnts else None

    if circles is not None:
        for cx, cy, r in np.round(circles[0]).astype(int):
            if obj_cnt is not None:
                if cv2.pointPolygonTest(obj_cnt, (float(cx), float(cy)), False) < 0:
                    continue
            # Verify it overlaps a dark region
            test_mask = np.zeros_like(gray)
            cv2.circle(test_mask, (cx, cy), max(1, r - 4), 255, -1)
            overlap = cv2.countNonZero(cv2.bitwise_and(dark, test_mask))
            if overlap < 0.3 * (np.pi * r * r):
                continue
            holes.append({
                "kind"  : "circle",
                "center": (int(cx), int(cy)),
                "radius": int(r),
                "bbox"  : (cx - r, cy - r, 2 * r, 2 * r),
            })

    # ── Contour hierarchy (slots / rectangular holes) ─────────────────────────
    cnts, hier = cv2.findContours(dark, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is not None:
        for i, (cnt, h) in enumerate(zip(cnts, hier[0])):
            area = cv2.contourArea(cnt)
            if area < 300:
                continue
            bx, by, bw, bh = cv2.boundingRect(cnt)
            cx, cy = bx + bw // 2, by + bh // 2

            if obj_cnt is not None:
                if cv2.pointPolygonTest(obj_cnt, (float(cx), float(cy)), False) < 0:
                    continue

            # Skip if already captured by Hough
            if any(abs(hh["center"][0] - cx) < 20 and abs(hh["center"][1] - cy) < 20
                   for hh in holes):
                continue

            aspect = bw / max(bh, 1)
            kind   = "circle" if 0.75 < aspect < 1.35 else "slot"
            holes.append({
                "kind"  : kind,
                "center": (cx, cy),
                "radius": min(bw, bh) // 2,
                "bbox"  : (bx, by, bw, bh),
            })

    return holes, dark


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Visualise & report
# ══════════════════════════════════════════════════════════════════════════════

def draw_results(image, bbox, cnt, holes):
    out = image.copy()
    x, y, w, h = bbox

    # ── Object bounding box ───────────────────────────────────────────────────
    cv2.rectangle(out, (x, y), (x + w, y + h), (0, 220, 60), 2)

    # Width dimension line (below object)
    ly = y + h + 28
    cv2.arrowedLine(out, (x, ly), (x + w, ly), (0, 220, 60), 2, tipLength=0.03)
    cv2.arrowedLine(out, (x + w, ly), (x, ly), (0, 220, 60), 2, tipLength=0.03)
    label_w = f"W = {MM(w)} mm  ({w} px)"
    cv2.putText(out, label_w, (x + w // 2 - 90, ly - 7),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 60), 2, cv2.LINE_AA)

    # Height dimension line (left of object)
    lx = max(x - 55, 10)
    cv2.arrowedLine(out, (lx, y), (lx, y + h), (0, 220, 60), 2, tipLength=0.03)
    cv2.arrowedLine(out, (lx, y + h), (lx, y), (0, 220, 60), 2, tipLength=0.03)
    label_h = f"H={MM(h)}mm"
    cv2.putText(out, label_h, (max(lx - 50, 2), y + h // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 60), 2, cv2.LINE_AA)

    # ── Holes ─────────────────────────────────────────────────────────────────
    colors = {"circle": (0, 80, 255), "slot": (255, 140, 0)}
    for i, hole in enumerate(holes, 1):
        col = colors.get(hole["kind"], (200, 0, 200))
        cx, cy = hole["center"]
        r  = hole["radius"]
        bx, by, bw, bh = [int(v) for v in hole["bbox"]]

        if hole["kind"] == "circle":
            cv2.circle(out, (cx, cy), r,  col, 2, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), 3,  col, -1)
            tag = f"H{i} Ø{MM(2*r)}mm"
            cv2.putText(out, tag, (cx - 38, cy - r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, col, 2, cv2.LINE_AA)
            # Diameter line
            cv2.line(out, (cx - r, cy), (cx + r, cy), col, 1, cv2.LINE_AA)
        else:
            cv2.rectangle(out, (bx, by), (bx + bw, by + bh), col, 2)
            tag = f"H{i} {MM(bw)}×{MM(bh)}mm"
            cv2.putText(out, tag, (bx, by - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, col, 2, cv2.LINE_AA)

    return out


def print_report(bbox, holes):
    x, y, w, h = bbox
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║        DIMENSION DETECTION RESULTS           ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Object Width  : {MM(w):>7} mm   ({w} px)".ljust(47) + "║")
    print(f"║  Object Height : {MM(h):>7} mm   ({h} px)".ljust(47) + "║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Holes detected: {len(holes)}".ljust(47) + "║")
    for i, hole in enumerate(holes, 1):
        cx, cy = hole["center"]
        if hole["kind"] == "circle":
            d = MM(2 * hole["radius"])
            print(f"║  Hole {i:>2} [circle]  Ø {d:>6} mm  @ ({cx},{cy})".ljust(47) + "║")
        else:
            bx, by, bw, bh = hole["bbox"]
            print(f"║  Hole {i:>2} [slot]    {MM(bw):>5}×{MM(bh):<5} mm  @ ({cx},{cy})".ljust(47) + "║")
    print("╚══════════════════════════════════════════════╝")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n  Loading  →  {IMAGE_PATH}")
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print(f"[ERROR] Cannot open '{IMAGE_PATH}'. Run generate_realistic.py first.")
        return

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    print(f"  Image size : {W} × {H} px   |   Scale : {PPM} px/mm\n")

    # ── Step 1: segment ───────────────────────────────────────────────────────
    print("  [1/4] Segmenting object ...")
    obj_mask, _ = segment_object(gray)
    if obj_mask is None:
        print("  [ERROR] Could not segment object.")
        return

    # ── Step 2: bounding box ──────────────────────────────────────────────────
    print("  [2/4] Computing bounding box ...")
    result = object_bbox(obj_mask)
    if result is None:
        print("  [ERROR] No bounding box found.")
        return
    bbox, obj_cnt = result

    # ── Step 3: holes ─────────────────────────────────────────────────────────
    print("  [3/4] Detecting holes ...")
    holes, dark_mask = detect_holes(gray, obj_mask)

    # ── Step 4: draw + report ─────────────────────────────────────────────────
    print("  [4/4] Rendering results ...")
    annotated = draw_results(image, bbox, obj_cnt, holes)
    print_report(bbox, holes)

    # Save
    out_path = "realistic_part_detected.jpg"
    cv2.imwrite(out_path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"  Annotated image saved → {out_path}")

    # ── Matplotlib display ────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('#0d0d0d')

    panels = [
        (cv2.cvtColor(image,     cv2.COLOR_BGR2RGB), "Original Image",      'gray'),
        (dark_mask,                                   "Hole Mask (Step 3)",  'gray'),
        (cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), "Detected Dimensions", 'gray'),
    ]

    for ax, (data, title, cmap) in zip(axes, panels):
        ax.imshow(data, cmap=cmap if data.ndim == 2 else None)
        ax.set_title(title, color='white', fontsize=12, pad=8)
        ax.set_facecolor('#0d0d0d')
        ax.axis('off')

    # Legend
    legend = [
        mpatches.Patch(color='#00DC3C', label='Object bounding box (W × H)'),
        mpatches.Patch(color='#0050FF', label='Circular holes (Ø diameter)'),
        mpatches.Patch(color='#FF8C00', label='Slots (W × H)'),
    ]
    fig.legend(handles=legend, loc='lower center', ncol=3,
               facecolor='#1a1a1a', edgecolor='gray',
               labelcolor='white', fontsize=10, framealpha=0.9,
               bbox_to_anchor=(0.5, 0.01))

    plt.suptitle("Object Dimension Detection  ·  realistic_part.jpg",
                 color='white', fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig("realistic_part_result.png", dpi=130,
                bbox_inches='tight', facecolor='#0d0d0d')
    print("  Full result panel saved → realistic_part_result.png\n")
    plt.show()


if __name__ == "__main__":
    main()
