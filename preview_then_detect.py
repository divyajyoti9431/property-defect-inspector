"""
1. Generates a complex industrial part image
2. Shows it to you for preview
3. Asks for confirmation before running the detector
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import subprocess


# ─── Generate a complex object ────────────────────────────────────────────────

def create_complex_object(path="complex_object.jpg"):
    """
    Simulates an industrial bracket / flange plate with:
      - 1 large central circular bore
      - 4 corner mounting holes (circular)
      - 2 elongated slots (rectangular)
      - 1 small vent hole
      - Chamfered corners and inner shoulder ring
    """
    H, W = 720, 1000
    img = np.ones((H, W, 3), dtype=np.uint8) * 220   # light background

    # ── Main plate body ──────────────────────────────────────────────────────
    pts = np.array([
        [100, 80], [900, 80], [940, 120],
        [940, 600], [900, 640], [100, 640],
        [60,  600], [60,  120]
    ], dtype=np.int32)
    cv2.fillPoly(img, [pts], (90, 95, 100))       # dark steel color
    cv2.polylines(img, [pts], True, (55, 58, 62), 4)

    # ── Inner shoulder ring (raised boss) ───────────────────────────────────
    cv2.circle(img, (500, 360), 160, (75, 80, 85), -1)
    cv2.circle(img, (500, 360), 160, (50, 53, 58),  3)

    # ── Large central bore ──────────────────────────────────────────────────
    cv2.circle(img, (500, 360), 90, (220, 220, 220), -1)
    cv2.circle(img, (500, 360), 90, (180, 180, 180),  2)

    # ── 4 corner mounting holes ──────────────────────────────────────────────
    for cx, cy in [(170, 150), (830, 150), (170, 570), (830, 570)]:
        cv2.circle(img, (cx, cy), 36, (220, 220, 220), -1)
        cv2.circle(img, (cx, cy), 36, (175, 175, 175),  2)

    # ── 2 elongated slots ───────────────────────────────────────────────────
    # Left slot
    cv2.rectangle(img, (155, 280), (215, 440), (220, 220, 220), -1)
    cv2.rectangle(img, (155, 280), (215, 440), (175, 175, 175),  2)
    # Right slot
    cv2.rectangle(img, (785, 280), (845, 440), (220, 220, 220), -1)
    cv2.rectangle(img, (785, 280), (845, 440), (175, 175, 175),  2)

    # ── Small vent hole ──────────────────────────────────────────────────────
    cv2.circle(img, (500, 180), 20, (220, 220, 220), -1)
    cv2.circle(img, (500, 180), 20, (175, 175, 175),  2)

    # ── Realistic surface texture (gradient + noise) ─────────────────────────
    noise = np.random.randint(-18, 18, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # ── Soft lighting gradient ───────────────────────────────────────────────
    light = np.zeros((H, W), dtype=np.float32)
    cv2.circle(light, (300, 200), 500, 1.0, -1)
    light = cv2.GaussianBlur(light, (301, 301), 0)
    for c in range(3):
        img[:, :, c] = np.clip(
            img[:, :, c].astype(np.float32) + light * 18, 0, 255
        ).astype(np.uint8)

    cv2.imwrite(path, img)
    return path, img


# ─── Preview window ──────────────────────────────────────────────────────────

def show_preview(img_bgr, path):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#1e1e1e')

    # Full image
    axes[0].imshow(img_rgb)
    axes[0].set_title("Complex Industrial Part — Full View", color='white', fontsize=13)
    axes[0].axis('off')

    # Annotated legend
    axes[1].imshow(img_rgb)
    axes[1].set_title("Feature Map (before detection)", color='white', fontsize=13)
    axes[1].axis('off')

    # Overlay feature labels on right panel
    labels = [
        (500, 360, "Central Bore\n(large circle)", "red"),
        (170, 150, "Mounting Hole\n(×4 corners)", "cyan"),
        (185, 360, "Elongated Slot\n(×2 sides)",  "yellow"),
        (500, 180, "Vent Hole",                    "lime"),
        (500, 490, "Inner Boss\n(shoulder ring)",  "orange"),
    ]
    for tx, ty, label, col in labels:
        axes[1].annotate(
            label,
            xy=(tx, ty), xytext=(tx + 60, ty + 60),
            fontsize=8, color=col,
            arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
            bbox=dict(boxstyle="round,pad=0.3", fc="#1e1e1e", ec=col, alpha=0.85)
        )

    legend_items = [
        mpatches.Patch(color='red',    label='Central bore (Ø90 px radius)'),
        mpatches.Patch(color='cyan',   label='4× Mounting holes (Ø36 px radius)'),
        mpatches.Patch(color='yellow', label='2× Rectangular slots (60×160 px)'),
        mpatches.Patch(color='lime',   label='1× Small vent hole (Ø20 px radius)'),
    ]
    axes[1].legend(handles=legend_items, loc='lower left',
                   facecolor='#2a2a2a', edgecolor='gray',
                   labelcolor='white', fontsize=8)

    for ax in axes:
        ax.set_facecolor('#1e1e1e')

    plt.suptitle(f"PREVIEW  ·  {path}  ·  {img_bgr.shape[1]}×{img_bgr.shape[0]} px",
                 color='white', fontsize=11, y=1.01)
    plt.tight_layout()
    plt.savefig("complex_object_preview.png", dpi=120, bbox_inches='tight',
                facecolor='#1e1e1e')
    print("\n  Preview saved → complex_object_preview.png")
    plt.show()


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  STEP 1 — Generating complex industrial part image...")
    print("=" * 55)
    path, img = create_complex_object()
    print(f"  Saved → {path}")
    print(f"  Size  : {img.shape[1]} × {img.shape[0]} px")

    print("\n  STEP 2 — Opening PREVIEW window...")
    print("  (Close the window to continue)\n")
    show_preview(img, path)

    # Ask user before running detector
    print("\n" + "=" * 55)
    answer = input("  Run dimension detector on this image? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes"):
        print("\n  STEP 3 — Running detector...\n")
        subprocess.run(
            [sys.executable, "detector.py", "--image", path, "--ppm", "3.0"],
            check=False
        )
    else:
        print("  Skipped. Run manually with:")
        print(f"    python detector.py --image {path} --ppm 3.0")
