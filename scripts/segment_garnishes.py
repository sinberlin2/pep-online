"""
Split the garnish palette into individual transparent cut-outs.

Input : brand/inputs/external-designs/pep-original/marketing/bg_removed/garnishes-citrus-background-removed.png
Output: .../marketing/garnishes/bg_removed/<slug>-background-removed.png
Output: .../marketing/garnishes/bg_removed/<slug>-background-removed.png
        + .../marketing/garnishes/garnishes.json (manifest)

Method: threshold the alpha channel to drop faint ghosts, find connected
components (8-connectivity, on a downscaled mask for speed — no numpy needed),
crop each solid piece, trim, and name it by colour + relative size.

Usage:
  python scripts/segment_garnishes.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONCEPT_DIR = PROJECT_ROOT / "brand" / "inputs" / "external-designs" / "pep-original"
SOURCE = CONCEPT_DIR / "marketing" / "bg_removed" / "garnishes-citrus-background-removed.png"
OUT_DIR = CONCEPT_DIR / "marketing" / "garnishes" / "bg_removed"
MANIFEST = CONCEPT_DIR / "marketing" / "garnishes" / "garnishes.json"

# Alpha at/above this counts as "solid" for finding pieces (drops faint ghosts).
ALPHA_SOLID = 100
# Alpha below this is erased inside each crop (removes faint halos/ghosts).
ALPHA_CLEAN = 70
# Downscale factor for component labelling.
SCALE = 4
# Ignore components smaller than this (in downscaled pixels) as noise.
MIN_COMPONENT = 60
# Padding (full-res px) added around each detected piece before trimming.
PAD = 8


def _components(mask: Image.Image, min_size: int) -> list[tuple[int, int, int, int]]:
    """Return bounding boxes (x0, y0, x1, y1) of 8-connected blobs in `mask`."""
    w, h = mask.size
    px = mask.load()
    seen = bytearray(w * h)
    boxes: list[tuple[int, int, int, int]] = []

    for sy in range(h):
        for sx in range(w):
            if px[sx, sy] == 0 or seen[sy * w + sx]:
                continue
            stack = [(sx, sy)]
            seen[sy * w + sx] = 1
            minx = maxx = sx
            miny = maxy = sy
            size = 0
            while stack:
                x, y = stack.pop()
                size += 1
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                if y < miny:
                    miny = y
                if y > maxy:
                    maxy = y
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                            if px[nx, ny]:
                                seen[ny * w + nx] = 1
                                stack.append((nx, ny))
            if size >= min_size:
                boxes.append((minx, miny, maxx, maxy))
    return boxes


def _avg_color(crop: Image.Image) -> tuple[int, int, int]:
    rgba = crop.getdata()
    r = g = b = n = 0
    for pr, pg, pb, pa in rgba:
        if pa > 200:
            r += pr
            g += pg
            b += pb
            n += 1
    if n == 0:
        return (0, 0, 0)
    return (r // n, g // n, b // n)


def _hue(rgb: tuple[int, int, int]) -> float:
    r, g, b = (c / 255.0 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    delta = mx - mn
    if delta == 0:
        return 0.0
    if mx == r:
        h = ((g - b) / delta) % 6
    elif mx == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4
    return h * 60.0


def _category(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if g >= r and g >= b and g > 80:
        return "mint"
    # citrus: orange (hue ~35°) vs lemon (hue ~50°)
    return "orange" if _hue(rgb) < 43 else "lemon"


def _clean_crop(crop: Image.Image) -> Image.Image:
    alpha = crop.getchannel("A").point(lambda a: a if a >= ALPHA_CLEAN else 0)
    crop.putalpha(alpha)
    trimmed = crop.getbbox()
    return crop.crop(trimmed) if trimmed else crop


def segment() -> list[dict[str, Any]]:
    if not SOURCE.is_file():
        raise SystemExit(f"Source garnish image not found: {SOURCE}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.open(SOURCE).convert("RGBA")
    w, h = image.size

    solid = image.getchannel("A").point(lambda a: 255 if a >= ALPHA_SOLID else 0)
    small = solid.resize((w // SCALE, h // SCALE), Image.BILINEAR).point(
        lambda v: 255 if v >= 128 else 0
    )
    # Light dilation (one pass) bridges thin stems within a sprig without
    # merging distinct, well-separated garnishes.
    small = small.filter(ImageFilter.MaxFilter(3)).point(lambda v: 1 if v >= 128 else 0)
    boxes = _components(small, MIN_COMPONENT)

    pieces: list[dict[str, Any]] = []
    for (x0, y0, x1, y1) in boxes:
        fx0 = max(0, x0 * SCALE - PAD)
        fy0 = max(0, y0 * SCALE - PAD)
        fx1 = min(w, (x1 + 1) * SCALE + PAD)
        fy1 = min(h, (y1 + 1) * SCALE + PAD)
        crop = _clean_crop(image.crop((fx0, fy0, fx1, fy1)))
        if crop.width < 16 or crop.height < 16:
            continue
        rgb = _avg_color(crop)
        pieces.append(
            {
                "crop": crop,
                "category": _category(rgb),
                "avgColor": rgb,
                "area": crop.width * crop.height,
                "centerX": (fx0 + fx1) / 2,
            }
        )

    # Name pieces: larger of a category = "slice", smaller orange = "wedge".
    manifest: list[dict[str, Any]] = []
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for p in pieces:
        by_cat.setdefault(p["category"], []).append(p)

    for cat, items in by_cat.items():
        items.sort(key=lambda p: p["area"], reverse=True)
        for i, p in enumerate(items):
            if cat == "mint":
                slug = "mint" if len(items) == 1 else ("mint-large", "mint-small", f"mint-{i}")[min(i, 2)]
            elif cat == "orange":
                slug = ("orange-slice", "orange-wedge", f"orange-{i}")[min(i, 2)]
            elif cat == "lemon":
                slug = "lemon-slice" if i == 0 else f"lemon-{i}"
            else:
                slug = f"{cat}-{i}"

            crop: Image.Image = p["crop"]
            out_path = OUT_DIR / f"{slug}-background-removed.png"
            crop.save(out_path, "PNG")
            rel = out_path.relative_to(PROJECT_ROOT).as_posix()
            manifest.append(
                {
                    "slug": slug,
                    "category": cat,
                    "src": rel,
                    "pixelWidth": crop.width,
                    "pixelHeight": crop.height,
                    "aspectRatio": round(crop.width / crop.height, 4),
                    "avgColor": list(p["avgColor"]),
                }
            )
            print(f"  {slug}: {crop.width}x{crop.height} -> {rel}")

    manifest.sort(key=lambda m: m["slug"])
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {len(manifest)} garnish cut-outs + manifest {MANIFEST.relative_to(PROJECT_ROOT)}")
    return manifest


if __name__ == "__main__":
    segment()
