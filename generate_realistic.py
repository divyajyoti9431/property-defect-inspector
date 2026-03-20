"""
Generates a photorealistic industrial metal flange plate image
using layered noise, specular highlights, edge shadows, and
sub-pixel rendering — no camera or 3D engine needed.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


# ── Noise / texture helpers ───────────────────────────────────────────────────

def perlin_like_noise(h, w, scale=40, octaves=5):
    """Stack multiple resolutions of random noise → organic metal grain."""
    result = np.zeros((h, w), dtype=np.float32)
    amp, freq, total = 1.0, 1.0, 0.0
    for _ in range(octaves):
        size = (max(2, int(h / (scale * freq))), max(2, int(w / (scale * freq))))
        layer = np.random.rand(*size).astype(np.float32)
        layer = cv2.resize(layer, (w, h), interpolation=cv2.INTER_CUBIC)
        result += layer * amp
        total += amp
        amp  *= 0.55
        freq *= 2.0
    return (result / total)          # 0..1


def metal_texture(h, w, base_val=105, grain=28):
    """Brushed steel surface: directional streaks + fine grain."""
    # Horizontal brush streaks
    streaks = np.random.rand(h, 1).astype(np.float32)
    streaks = np.tile(streaks, (1, w))
    streaks = cv2.GaussianBlur(streaks, (1, 51), 0)

    # Fine random grain
    grain_n = np.random.rand(h, w).astype(np.float32)
    grain_n = cv2.GaussianBlur(grain_n, (3, 3), 0)

    tex = (streaks * 0.55 + grain_n * 0.45)
    tex = (tex - tex.min()) / (tex.max() - tex.min() + 1e-6)
    gray_tex = (base_val + tex * grain).astype(np.uint8)

    # BGR — slight cool tint for steel
    b = np.clip(gray_tex.astype(np.int16) + 8,  0, 255).astype(np.uint8)
    g = gray_tex
    r = np.clip(gray_tex.astype(np.int16) - 6,  0, 255).astype(np.uint8)
    return cv2.merge([b, g, r])


def radial_light(h, w, cx, cy, radius, intensity=60):
    """Soft specular highlight blob."""
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    light = np.clip(1.0 - dist / radius, 0, 1) ** 2
    return (light * intensity).astype(np.float32)


def draw_circle_hole(img, mask, cx, cy, r):
    """Cut a circular hole with inner chamfer, shadow ring, and bore glint."""
    # Outer shadow ring
    for dr in range(8, 0, -1):
        alpha = (8 - dr) / 8 * 0.6
        overlay = img.copy()
        cv2.circle(overlay, (cx, cy), r + dr, (30, 30, 35), -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    # Hole bore — dark with subtle inner-wall gradient
    cv2.circle(img,  (cx, cy), r, (28, 30, 34), -1)

    # Inner chamfer highlight (top-left glint)
    chamfer = img.copy()
    cv2.ellipse(chamfer, (cx - r//6, cy - r//6),
                (r, r), 0, 200, 310, (180, 185, 195), r // 4)
    cv2.addWeighted(chamfer, 0.45, img, 0.55, 0, img)

    # Tiny specular glint on bore edge
    glint_x = int(cx - r * 0.55)
    glint_y = int(cy - r * 0.55)
    cv2.circle(img, (glint_x, glint_y), max(2, r // 7), (230, 235, 240), -1)
    cv2.circle(img, (glint_x, glint_y), max(2, r // 7),
               (255, 255, 255), 1, cv2.LINE_AA)

    cv2.circle(mask, (cx, cy), r, 0, -1)


def draw_slot_hole(img, mask, x1, y1, x2, y2):
    """Rectangular slot with chamfer edges, shadow, and inner darkness."""
    pw, ph = x2 - x1, y2 - y1
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    # Shadow border
    for d in range(6, 0, -1):
        alpha = (6 - d) / 6 * 0.55
        overlay = img.copy()
        cv2.rectangle(overlay, (x1 - d, y1 - d), (x2 + d, y2 + d),
                      (25, 25, 30), -1)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    # Bore interior
    cv2.rectangle(img, (x1, y1), (x2, y2), (28, 30, 34), -1)

    # Top/left highlight edge (chamfer glint)
    cv2.line(img, (x1, y1), (x2, y1), (160, 165, 175), 2, cv2.LINE_AA)
    cv2.line(img, (x1, y1), (x1, y2), (155, 160, 170), 2, cv2.LINE_AA)

    # Bottom/right shadow edge
    cv2.line(img, (x1, y2), (x2, y2), (18, 18, 22), 2, cv2.LINE_AA)
    cv2.line(img, (x2, y1), (x2, y2), (18, 18, 22), 2, cv2.LINE_AA)

    cv2.rectangle(mask, (x1, y1), (x2, y2), 0, -1)


# ── Main image builder ────────────────────────────────────────────────────────

def generate(out_path="realistic_part.jpg"):
    H, W = 800, 1100
    rng = np.random.default_rng(42)

    # ── 1. Background — concrete / workbench ──────────────────────────────────
    bg_noise = perlin_like_noise(H, W, scale=20, octaves=6)
    bg = (bg_noise * 55 + 40).astype(np.uint8)
    bg_color = cv2.merge([bg, bg, np.clip(bg.astype(np.int16) - 8, 0, 255).astype(np.uint8)])
    img = bg_color.copy()

    # ── 2. Part silhouette (chamfered rectangle) ──────────────────────────────
    chamfer = 38
    pts = np.array([
        [110 + chamfer, 90],
        [990 - chamfer, 90],
        [990,           90  + chamfer],
        [990,           710 - chamfer],
        [990 - chamfer, 710],
        [110 + chamfer, 710],
        [110,           710 - chamfer],
        [110,           90  + chamfer],
    ], dtype=np.int32)

    # Base metal surface
    metal = metal_texture(H, W, base_val=108, grain=32)
    part_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(part_mask, [pts], 255)

    img[part_mask == 255] = metal[part_mask == 255]

    # ── 3. Global lighting: key light top-left, fill bottom-right ─────────────
    key  = radial_light(H, W, cx=250,  cy=180,  radius=700, intensity=45)
    fill = radial_light(H, W, cx=900,  cy=680,  radius=600, intensity=18)
    light_map = (key + fill).astype(np.float32)
    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        ch[part_mask == 255] = np.clip(
            ch[part_mask == 255] + light_map[part_mask == 255], 0, 255)
        img[:, :, c] = ch.astype(np.uint8)

    # ── 4. Part outline shadow / depth edge ───────────────────────────────────
    edge_shadow = np.zeros((H, W), dtype=np.float32)
    cv2.polylines(edge_shadow[np.newaxis], [pts[np.newaxis]], True, 1.0, 22)
    edge_shadow = cv2.GaussianBlur(edge_shadow.squeeze(), (21, 21), 0)
    shadow_layer = img.copy()
    for c in range(3):
        ch = shadow_layer[:, :, c].astype(np.float32)
        shadow_layer[:, :, c] = np.clip(ch - edge_shadow * 55, 0, 255).astype(np.uint8)
    cv2.addWeighted(shadow_layer, 0.5, img, 0.5, 0, img)

    # ── 5. Inner raised boss ring ─────────────────────────────────────────────
    boss_cx, boss_cy, boss_r = 550, 400, 175
    boss_tex = metal_texture(H, W, base_val=118, grain=22)

    boss_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(boss_mask, (boss_cx, boss_cy), boss_r, 255, -1)
    img[boss_mask == 255] = boss_tex[boss_mask == 255]

    # Boss rim highlight + shadow
    cv2.circle(img, (boss_cx, boss_cy), boss_r,     (60, 62, 70),  3, cv2.LINE_AA)
    cv2.circle(img, (boss_cx, boss_cy), boss_r - 1, (175, 180, 188), 2, cv2.LINE_AA)

    boss_light = radial_light(H, W, cx=boss_cx - 60, cy=boss_cy - 70, radius=220, intensity=30)
    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        ch[boss_mask == 255] = np.clip(
            ch[boss_mask == 255] + boss_light[boss_mask == 255], 0, 255)
        img[:, :, c] = ch.astype(np.uint8)

    # ── 6. Holes & slots ──────────────────────────────────────────────────────
    hole_mask = np.ones((H, W), dtype=np.uint8) * 255

    # Central bore (large)
    draw_circle_hole(img, hole_mask, 550, 400, 92)

    # 4 corner mounting holes
    for cx, cy in [(200, 170), (900, 170), (200, 630), (900, 630)]:
        draw_circle_hole(img, hole_mask, cx, cy, 38)

    # 2 vertical elongated slots
    draw_slot_hole(img, hole_mask, 165, 295, 235, 505)   # left
    draw_slot_hole(img, hole_mask, 865, 295, 935, 505)   # right

    # Top-center vent hole
    draw_circle_hole(img, hole_mask, 550, 165, 22)

    # Two small dowel holes near boss
    draw_circle_hole(img, hole_mask, 420, 245, 15)
    draw_circle_hole(img, hole_mask, 680, 245, 15)

    # ── 7. Part boundary hard edge ────────────────────────────────────────────
    cv2.polylines(img, [pts], True, (45, 46, 52), 3, cv2.LINE_AA)

    # ── 8. Drop shadow on background ─────────────────────────────────────────
    drop = np.zeros((H, W), dtype=np.float32)
    shadow_pts = pts + np.array([10, 12])
    cv2.fillPoly(drop, [shadow_pts], 1.0)
    drop = cv2.GaussianBlur(drop, (35, 35), 0)
    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        bg_region = part_mask == 0
        ch[bg_region] = np.clip(
            ch[bg_region] - drop[bg_region] * 70, 0, 255)
        img[:, :, c] = ch.astype(np.uint8)

    # ── 9. Final lens vignette ────────────────────────────────────────────────
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = ((X - W/2)**2 / (W/2)**2 + (Y - H/2)**2 / (H/2)**2)
    vig = np.clip(vig * 0.35, 0, 1)
    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        img[:, :, c] = np.clip(ch * (1 - vig), 0, 255).astype(np.uint8)

    # ── Save ──────────────────────────────────────────────────────────────────
    cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 97])
    print(f"  Saved → {out_path}  ({W}×{H} px)")
    return out_path, img


# ── Preview ───────────────────────────────────────────────────────────────────

def preview(img_bgr, path):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#111')
    ax.imshow(img_rgb)
    ax.set_facecolor('#111')
    ax.axis('off')

    plt.tight_layout(pad=0)
    preview_path = path.replace('.jpg', '_preview.jpg')
    plt.savefig(preview_path, dpi=130, bbox_inches='tight', facecolor='#111')
    print(f"  Preview saved → {preview_path}\n")
    plt.show()
    return preview_path


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess, sys

    print("=" * 55)
    print("  Generating realistic industrial part image...")
    print("=" * 55)
    path, img = generate("realistic_part.jpg")

    print("\n  Opening preview — close window to continue.")
    preview(img, path)

    print("=" * 55)
    ans = input("  Run dimension detector on this image? [Y/n]: ").strip().lower()
    if ans in ("", "y", "yes"):
        print("\n  Running detector...\n")
        subprocess.run(
            [sys.executable, "detector.py", "--image", path, "--ppm", "3.0"],
            check=False
        )
    else:
        print(f"\n  Run later with:\n    python detector.py --image {path} --ppm 3.0")
