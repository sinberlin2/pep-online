"""
Extract individual flavour cans from the lineup image and remove backgrounds.

Uses rembg (local model). Optional: set REMOVEBG_API_KEY for remove.bg API per crop.

Outputs: brand/design-concepts/pep-original/product/flavours/bg_removed/{slug}-background-removed.png

Run (conda env pep-online):
  python scripts/segment_flavors.py
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image
from rembg import remove, new_session

ROOT = Path(__file__).resolve().parents[1]
CONCEPT_DIR = ROOT / "brand" / "design-concepts" / "pep-original"
LINEUP = CONCEPT_DIR / "marketing" / "originals" / "flavours-lineup.png"
OUT_DIR = CONCEPT_DIR / "product" / "flavours" / "bg_removed"
CROP_DIR = CONCEPT_DIR / "product" / "flavours" / "crops"

# Five cans left-to-right in flavours-lineup.png (1024×561)
FLAVOURS = [
    {"slug": "pineapple-lime", "name": "Pineapple Lime", "x0": 0.10, "x1": 0.28},
    {"slug": "orange-passionfruit", "name": "Orange Passionfruit", "x0": 0.24, "x1": 0.42},
    {"slug": "raspberry-lemon", "name": "Raspberry Lemon", "x0": 0.38, "x1": 0.56},
    {"slug": "mango-guava", "name": "Mango Guava", "x0": 0.52, "x1": 0.70},
    {"slug": "blueberry-acai", "name": "Blueberry Acai", "x0": 0.66, "x1": 0.88},
]


def remove_bg_api(image_bytes: bytes, api_key: str) -> bytes:
    import urllib.request

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image_file"; filename="crop.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://api.remove.bg/v1.0/removebg",
        data=body,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def remove_bg_local(image_bytes: bytes, session) -> bytes:
    return remove(image_bytes, session=session)


def crop_can(lineup: Image.Image, x0: float, x1: float) -> Image.Image:
    w, h = lineup.size
    left = int(w * x0)
    right = int(w * x1)
    top = int(h * 0.02)
    bottom = int(h * 0.98)
    return lineup.crop((left, top, right, bottom))


def main() -> None:
    if not LINEUP.exists():
        raise SystemExit(f"Missing lineup image: {LINEUP}")

    api_key = os.environ.get("REMOVEBG_API_KEY", "").strip()
    model = os.environ.get("REMBG_MODEL", "isnet-general-use")
    session = None if api_key else new_session(model)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CROP_DIR.mkdir(parents=True, exist_ok=True)

    lineup = Image.open(LINEUP).convert("RGBA")
    print(f"Lineup: {lineup.size[0]}x{lineup.size[1]}")
    print(f"Backend: {'remove.bg API' if api_key else f'rembg ({model})'}")

    for flavour in FLAVOURS:
        slug = flavour["slug"]
        crop = crop_can(lineup, flavour["x0"], flavour["x1"])
        crop_path = CROP_DIR / f"{slug}-crop.png"
        crop.save(crop_path)

        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        raw = buf.getvalue()

        if api_key:
            out_bytes = remove_bg_api(raw, api_key)
        else:
            out_bytes = remove_bg_local(raw, session)

        out_path = OUT_DIR / f"{slug}-background-removed.png"
        out_path.write_bytes(out_bytes)
        print(f"  {flavour['name']} -> {out_path.name}")

    print(f"\nDone. {len(FLAVOURS)} cans in {OUT_DIR}")


if __name__ == "__main__":
    main()
