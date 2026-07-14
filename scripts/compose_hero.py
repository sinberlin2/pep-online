"""
Deterministic hero composition helpers.

The agent (`agents.hero_run`) *chooses* which assets to use and where they go;
this module does the pixel work:

  * expose an allow-listed asset library (can, glass, and the individual garnish
    cut-outs produced by `scripts/segment_garnishes.py`) with real dimensions,
  * render a layout spec into a single preview PNG (so a vision model can look
    at it), and
  * turn an approved layout spec into `css/hero-generated.css` that the live
    site consumes.

A layout layer references an asset by `key` (never a raw path), so the agent can
only place assets that actually exist. Each layer renders to an
`<img class="hero-layer hero-layer--{key}">` on the page.

Run standalone to (re)render the last approved layout:

  python scripts/compose_hero.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESIGN_CONCEPT = "pep-original"
CONCEPT_REL = f"brand/inputs/external-designs/{DESIGN_CONCEPT}"
CONCEPT_DIR = PROJECT_ROOT / "brand" / "inputs" / "external-designs" / DESIGN_CONCEPT

# Fixed product assets (always available).
PRODUCT_ASSETS: dict[str, str] = {
    "can": f"{CONCEPT_REL}/product/bg_removed/pep-can-background-removed.png",
    "glass": f"{CONCEPT_REL}/product/bg_removed/pep-glass-background-removed.png",
}
# Individual garnish cut-outs come from this manifest (segment_garnishes.py).
GARNISH_MANIFEST = CONCEPT_DIR / "marketing" / "garnishes" / "garnishes.json"

CANVAS_ASPECT = (4, 5)  # width : height, matches .hero-product
DEFAULT_BACKGROUND = "#faf6f0"  # --pep-cream


def asset_library() -> dict[str, dict[str, Any]]:
    """All placeable assets keyed by slug, with real pixel dimensions."""
    library: dict[str, dict[str, Any]] = {}
    for key, rel in PRODUCT_ASSETS.items():
        path = PROJECT_ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"Product asset missing: {rel}")
        with Image.open(path) as img:
            w, h = img.size
        library[key] = {
            "key": key,
            "category": "product",
            "src": rel,
            "pixelWidth": w,
            "pixelHeight": h,
            "aspectRatio": round(w / h, 4),
        }
    if GARNISH_MANIFEST.is_file():
        for item in json.loads(GARNISH_MANIFEST.read_text(encoding="utf-8")):
            library[item["slug"]] = {
                "key": item["slug"],
                "category": item.get("category", "garnish"),
                "src": item["src"],
                "pixelWidth": item["pixelWidth"],
                "pixelHeight": item["pixelHeight"],
                "aspectRatio": item["aspectRatio"],
            }
    return library


def build_manifest() -> list[dict[str, Any]]:
    """Allow-listed assets for the agent (products first, then garnishes)."""
    library = asset_library()
    order = {"product": 0, "garnish": 1, "lemon": 1, "orange": 1, "mint": 1}
    return sorted(
        library.values(), key=lambda a: (order.get(a["category"], 2), a["key"])
    )


def _apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 0.999:
        return image
    opacity = max(0.0, min(1.0, opacity))
    alpha = image.getchannel("A").point(lambda a: int(a * opacity))
    image.putalpha(alpha)
    return image


def render_layout(
    layout: dict[str, Any],
    *,
    out_path: Path,
    canvas_width: int = 1000,
    transparent: bool = False,
    trim: bool = False,
) -> Path:
    """Composite the layers described by `layout` into a single PNG.

    transparent=True keeps an alpha background (for baking a reusable lockup);
    trim=True crops away empty margins so only the artwork remains (relative
    positioning between layers is preserved).
    """
    library = asset_library()
    canvas_height = round(canvas_width * CANVAS_ASPECT[1] / CANVAS_ASPECT[0])
    if transparent:
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    else:
        bg = layout.get("canvasBackground") or DEFAULT_BACKGROUND
        try:
            bg_rgb = ImageColor.getrgb(bg)
        except ValueError:
            bg_rgb = ImageColor.getrgb(DEFAULT_BACKGROUND)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), bg_rgb + (255,))

    layers = sorted(layout.get("layers", []), key=lambda layer: layer.get("z", 0))
    for layer in layers:
        asset = library.get(layer.get("key"))
        if not asset:
            continue
        with Image.open(PROJECT_ROOT / asset["src"]) as raw:
            sprite = raw.convert("RGBA")

        target_w = max(1, round(float(layer.get("widthPct", 40)) / 100.0 * canvas_width))
        scale = target_w / sprite.width
        target_h = max(1, round(sprite.height * scale))
        sprite = sprite.resize((target_w, target_h), Image.LANCZOS)

        rotation = float(layer.get("rotationDeg", 0) or 0)
        if abs(rotation) > 0.01:
            sprite = sprite.rotate(-rotation, expand=True, resample=Image.BICUBIC)

        sprite = _apply_opacity(sprite, float(layer.get("opacity", 1) or 1))

        center_x = float(layer.get("centerXPct", 50)) / 100.0 * canvas_width
        bottom_offset = float(layer.get("bottomPct", 0)) / 100.0 * canvas_height
        left = round(center_x - sprite.width / 2)
        top = round(canvas_height - bottom_offset - sprite.height)
        canvas.alpha_composite(sprite, (left, top))

    if trim:
        bbox = canvas.getbbox()
        if bbox:
            canvas = canvas.crop(bbox)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if transparent:
        canvas.save(out_path, "PNG")
    else:
        canvas.convert("RGB").save(out_path, "PNG")
    return out_path


def _fmt(value: float) -> str:
    return f"{round(float(value), 2):g}"


def layout_to_css(layout: dict[str, Any]) -> str:
    """Render an approved layout spec as overriding CSS for the live hero."""
    def rules_block() -> str:
        rules: list[str] = []
        for layer in sorted(layout.get("layers", []), key=lambda layer: layer.get("z", 0)):
            key = layer.get("key")
            if not key:
                continue
            transform = f"translateX(-50%) rotate({_fmt(layer.get('rotationDeg', 0))}deg)"
            rules.append(
                "\n".join(
                    [
                        f".hero-layer--{key} {{",
                        f"  width: {_fmt(layer.get('widthPct', 40))}%;",
                        f"  left: {_fmt(layer.get('centerXPct', 50))}%;",
                        f"  bottom: {_fmt(layer.get('bottomPct', 0))}%;",
                        f"  z-index: {int(layer.get('z', 1))};",
                        f"  opacity: {_fmt(layer.get('opacity', 1))};",
                        f"  transform: {transform};",
                        "}",
                    ]
                )
            )
        return "\n\n".join(rules)

    body = rules_block()
    layout_id = layout.get("id", "hero-layout")
    header = (
        "/* Generated by the hero composition agent. Do not edit by hand. */\n"
        f"/* Layout: {layout_id} - {layout.get('label', '')} */\n"
    )
    return f"{header}\n{body}\n"


def html_layer_tags(layout: dict[str, Any], *, indent: str = "            ") -> str:
    """Build the <img> tags for index.html (in z-order, back to front)."""
    library = asset_library()
    lines: list[str] = []
    for i, layer in enumerate(
        sorted(layout.get("layers", []), key=lambda layer: layer.get("z", 0))
    ):
        asset = library.get(layer.get("key"))
        if not asset:
            continue
        key = layer["key"]
        prio = ' fetchpriority="high"' if key == "can" else ""
        lines.append(
            f'{indent}<img class="hero-layer hero-layer--{key}" '
            f'src="{asset["src"]}?v=1" alt=""{prio} />'
        )
    return "\n".join(lines)


if __name__ == "__main__":
    layout_path = PROJECT_ROOT / "experiments" / "hero" / "hero-layout.json"
    if not layout_path.is_file():
        raise SystemExit("No approved layout found. Run: python -m agents.hero_run")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    preview = render_layout(
        layout, out_path=PROJECT_ROOT / "experiments" / "hero" / "hero-preview.png"
    )
    (PROJECT_ROOT / "site" / "css" / "hero-generated.css").write_text(
        layout_to_css(layout), encoding="utf-8"
    )
    print(f"Rendered {preview}")
    print("Updated site/css/hero-generated.css")
    print("\nindex.html hero layers:")
    print(html_layer_tags(layout))
