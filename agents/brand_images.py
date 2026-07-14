"""
Generate the editorial BRAND BOARD (brand-board.png) for a direction.

Generated DIRECTLY from the strategy (`brand/directions/<slug>/strategy/positioning.json`) plus
ONE design theme (from `brand/directions/<slug>/identity/design-themes.json`): the image model
invents a palette + type FROM the theme description and shows them on the board (wordmark, slim
can, illustration elements, palette swatches, type specimen, badges, label layout). There is no
separate colour-palette / typography / board-brief JSON — read colours/type off the board by hand.

Pick the theme with --theme <id>; default is the first theme matching the direction's positioning.

Saved to brand/directions/<slug>/identity/images/brand-board.png

Usage:
  python -m agents.brand_images --positioning 3
  python -m agents.brand_images --positioning 3 --theme theme-02
  python -m agents.brand_images --positioning 3 --quality hd
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import paths  # noqa: E402

from agents.llm.env import get_openai_api_key, load_project_env

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(p: Path) -> dict | list:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _resolve_slug(arg: str) -> str:
    aliases = {
        "1": "functional-protein", "functional": "functional-protein", "functional-protein": "functional-protein",
        "2": "lifestyle", "lifestyle": "lifestyle",
        "3": "social", "social": "social",
    }
    return aliases.get(arg.strip().lower(), arg.strip().lower())


def _dalle(client, *, prompt: str, size: str, quality: str) -> bytes:
    q = {"standard": "medium", "hd": "high"}.get(quality, quality)
    resp = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size=size,
        quality=q,
        n=1,
    )
    return base64.b64decode(resp.data[0].b64_json)


# ---------------------------------------------------------------------------
# Brand board (single editorial visual-direction sheet)
# ---------------------------------------------------------------------------

def _pick_theme(themes: list, theme_id: str | None, active_id) -> dict:
    """Choose the design theme to render. Explicit --theme wins; else the first theme whose
    positioningLeaning matches the active direction; else the first theme."""
    if not themes:
        raise SystemExit("design-themes.json has no themes — run brand_identity first.")
    if theme_id:
        for t in themes:
            if t.get("id") == theme_id or t.get("name") == theme_id:
                return t
        raise SystemExit(f"Theme '{theme_id}' not found. Available: {[t.get('id') for t in themes]}")
    for t in themes:
        if str(t.get("positioningLeaning")) == str(active_id):
            return t
    return themes[0]


def _gen_brand_board(client, positioning: dict, theme: dict, product: dict, quality: str, images_dir: Path) -> dict | None:
    """One editorial brand board generated DIRECTLY from the strategy + ONE design theme.

    The image model invents the palette and typography FROM the theme description — there is
    no color-palette.json / typography.json / board-brief.json anymore. Colours/type are read
    off the board later by hand."""
    facts = product.get("productFacts", {})
    protein = facts.get("protein", "7g")
    tagline = product.get("tagline", "Feel good. Have fun.")
    occasions = ", ".join(positioning.get("occasions", [])[:5])
    personality = ", ".join(positioning.get("personalityAdjectives", [])[:8])
    one_liner = positioning.get("oneLiner", "a premium protein drink for social moments")

    prompt = f"""Create a polished editorial BRAND BOARD for the drinks brand PEP on a warm off-white background. Include, as labelled zones: a large PEP wordmark, a slim 330ml aluminium can packaging concept, a row of reusable illustration elements, a COLOUR PALETTE swatch row with hex labels, a TYPOGRAPHY DIRECTION specimen, small product badges, and a label-layout panel.

Brand (from strategy):
- PEP is {one_liner}
- Personality: {personality}
- Social occasions: {occasions}
- On-pack tagline: "{tagline}"; a small "{protein} protein" badge

Express ONE design direction — INVENT a cohesive premium palette and type FROM this description (do not copy any specific competitor):
- Look: {theme.get('name', '')} — {theme.get('baseTreatment', '')}
- Colour: {theme.get('colorTreatment', '')}
- Finish: {theme.get('finish', '')}
- Typography: {theme.get('typographyFeel', '')}
- Energy: {theme.get('energy', '')}

Requirements:
- Derive 6-8 cohesive palette swatches and a display + supporting type pairing that fit the direction above, and SHOW them on the board (swatches with invented hex labels; a short type specimen).
- Slim can front-facing with a slight three-quarter angle, flavour-led illustrations, small protein badge.
- Render "PEP" very clearly and large. No leaves or botanical motifs. Do not invent extra brand names, slogans, taglines, or websites beyond the above. No duplicate or misspelled logos.

Vector-friendly, graphic, premium. A first-pass visual direction sheet.
"""

    size = "1536x1024"
    print(f"  [brand-board] gpt-image-2 ({quality}, {size}) from theme '{theme.get('id')}' — {theme.get('name', '')} ...")
    try:
        img_bytes = _dalle(client, prompt=prompt, size=size, quality=quality)
        out_path = images_dir / "brand-board.png"
        out_path.write_bytes(img_bytes)
        print("    saved -> brand-board.png")
        return {
            "id": "brand-board",
            "name": "Brand identity board",
            "type": "board",
            "size": size,
            "quality": quality,
            "theme": theme.get("id"),
            "themeName": theme.get("name"),
            "file": "images/brand-board.png",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def generate(*, slug: str, quality: str = "standard", theme_id: str | None = None) -> Path:
    load_project_env()
    api_key = get_openai_api_key()

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    identity_dir = paths.direction_identity(slug)
    product: dict = _read_json(paths.PRODUCT_PROFILE)  # type: ignore[assignment]
    positioning: dict = _read_json(paths.direction_strategy(slug) / "positioning.json")  # type: ignore[assignment]
    themes = _read_json(identity_dir / "design-themes.json")

    if not positioning:
        raise SystemExit(f"No positioning.json for '{slug}'. Run brand_run first.")
    if not themes:
        raise SystemExit(f"No design-themes.json at {identity_dir}. Run brand_identity first.")
    theme = _pick_theme(themes, theme_id, positioning.get("activeId"))  # type: ignore[arg-type]

    images_dir = identity_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    manifest = []

    print("\n-- Brand board (gpt-image-2) --")
    result = _gen_brand_board(client, positioning, theme, product, quality, images_dir)
    if result:
        manifest.append(result)

    # Write/merge manifest
    manifest_path = images_dir / "manifest.json"
    existing = []
    if manifest_path.is_file():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    merged = {item["id"]: item for item in existing}
    for item in manifest:
        merged[item["id"]] = item
    manifest_path.write_text(json.dumps(list(merged.values()), indent=2) + "\n", encoding="utf-8")
    print(f"\nManifest updated -> {manifest_path}")

    return images_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the brand board (gpt-image-2)")
    parser.add_argument("--positioning", default=None)
    parser.add_argument("--quality", default="standard", choices=["standard", "hd"],
                        help="Image quality: standard (medium) or hd (high)")
    parser.add_argument("--theme", default=None,
                        help="Design theme id/name from design-themes.json (default: first theme matching the direction)")
    args = parser.parse_args()

    if not args.positioning:
        choice_path = paths.CHOICE
        if choice_path.is_file():
            choice = json.loads(choice_path.read_text(encoding="utf-8"))
            args.positioning = choice.get("positioningSlug", "")
        if not args.positioning:
            raise SystemExit("Pass --positioning or set brand/inputs/choice.json positioningSlug")

    slug = _resolve_slug(args.positioning)

    print(f"Generating brand board for [{slug}] ...")
    out = generate(slug=slug, quality=args.quality, theme_id=args.theme)
    print(f"\nDone. Assets at: {out}")


if __name__ == "__main__":
    main()
