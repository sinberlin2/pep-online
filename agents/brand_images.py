"""
Generate the single editorial BRAND BOARD (brand-board.png) for a direction.

One polished visual-direction sheet showing the wordmark, a slim-can concept,
reusable illustration elements, badges, colour-palette swatches (with the real hex
values), typography direction, and label layout. Palette, fonts, and tagline are
injected from the generated identity files; motifs, direction badges, and art
direction come from the identity's boardBrief (grounded in the positioning), so the
board renders the invented identity per direction rather than hardcoded values.

Saved to brand/directions/<slug>/identity/images/brand-board.png

Usage:
  python -m agents.brand_images --positioning 2
  python -m agents.brand_images --positioning lifestyle --quality hd
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

def _gen_brand_board(client, palette: dict, typography: dict, product: dict, positioning: dict, board_brief: dict, quality: str, images_dir: Path) -> dict | None:
    """One polished editorial brand board that renders the invented identity:
    wordmark, slim-can concept, illustration elements, badges, palette swatches, type direction.

    Direction-aware: palette/fonts/tagline come from the identity files, the factual badges
    come from the product profile, and the motifs / direction badges / art direction come
    from the identity's boardBrief (which brand_identity grounds in the positioning) — so the
    same template adapts to each direction (e.g. social -> '0.0%', 'social serve' + cocktail
    garnish; functional -> recovery cues). Falls back to positioning + neutral defaults when
    no boardBrief is present."""
    swatches = []
    for group in ("primary", "secondary", "background"):
        for sw in palette.get(group, []):
            swatches.append(f"{sw['name']} {sw['hex']}")
    swatch_line = "; ".join(swatches) or "the brand palette"

    display = typography.get("display", {}).get("family", "a confident display")
    body = typography.get("body", {}).get("family", "a clean supporting sans")

    tagline = product.get("tagline", "Feel good. Have fun.")
    facts = product.get("productFacts", {})
    protein = facts.get("protein", "7g")

    # Factual product badges (always present, direction-neutral) ...
    badges = [f"{protein} protein"]
    if facts.get("calories"):
        badges.append(f"{facts['calories']} cal")
    if facts.get("glutenFree"):
        badges.append("gluten-free")
    # ... plus direction-appropriate badges suggested by the identity boardBrief.
    for b in board_brief.get("badges", []):
        if b and b not in badges:
            badges.append(b)
    badge_line = ", ".join(f'"{b}"' for b in badges)

    # Illustration motifs: boardBrief if available, else a neutral flavour-led default.
    motifs = [m for m in board_brief.get("motifs", []) if m]
    motif_line = ", ".join(motifs) or "mango slice, coconut half, passionfruit, citrus wedge, sparkle/starburst"

    # Art direction: boardBrief if available, else positioning mood + designConcept.
    art_direction = (board_brief.get("artDirection") or "").strip()
    if not art_direction:
        visual = positioning.get("visual", {})
        art_bits = [visual.get("mood", "").strip(), visual.get("designConcept", "").strip()]
        art_direction = " ".join(b for b in art_bits if b) or "Premium, clean, flavour-forward."

    prompt = f"""Create a polished visual identity board for the brand PEP, including a logo, slim can packaging concept, illustration elements, badges, colour palette, typography direction, and label layout.

Brand: PEP

Composition:
One clean editorial brand board on a warm off-white background. Include these zones:

1. A large bold PEP wordmark in the upper left, premium confident custom lettering, clean and distinctive.
2. A hero slim 330ml aluminium can on the right, front-facing with a slight three-quarter angle. The can label uses the PEP wordmark, the tagline "{tagline}", flavour-led illustration motifs, and a small subtle "{protein} protein" badge.
3. Separate reusable illustration elements: {motif_line}. Flat vector-like illustrations, warm, premium, flavour-forward. No leaves or botanical motifs.
4. Colour palette swatches with hex labels, using exactly these brand colours: {swatch_line}.
5. Typography direction: a confident display style (in the spirit of {display}) for the logo and an elegant supporting sans (in the spirit of {body}) for details, with a clear editorial hierarchy.
6. Small badges: {badge_line}.

Art direction:
{art_direction} Vector-friendly, graphic, premium.

Text constraints:
Render "PEP" very clearly and large. Keep other text minimal and readable; do not invent extra brand names, slogans, taglines, or websites beyond what is specified above. No misspelled or duplicate logos. Only use the hex codes and words specified above.

Output intent:
Beautiful first-pass visual direction sheet that can guide later extraction into reusable logo, fruit icons, label assets, and can mockups.
"""

    size = "1536x1024"
    print(f"  [brand-board] gpt-image-2 ({quality}, {size}) ...")
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
            "file": "images/brand-board.png",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def generate(*, slug: str, quality: str = "standard") -> Path:
    load_project_env()
    api_key = get_openai_api_key()

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    identity_dir = paths.direction_identity(slug)
    palette: dict = _read_json(identity_dir / "color-palette.json")  # type: ignore[assignment]
    typography: dict = _read_json(identity_dir / "typography.json")  # type: ignore[assignment]
    product: dict = _read_json(paths.PRODUCT_PROFILE)  # type: ignore[assignment]
    positioning: dict = _read_json(paths.direction_strategy(slug) / "positioning.json")  # type: ignore[assignment]
    board_brief: dict = _read_json(identity_dir / "board-brief.json")  # type: ignore[assignment]

    if not palette:
        raise SystemExit(f"No color-palette.json found at {identity_dir}. Run brand_identity first.")

    images_dir = identity_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    manifest = []

    print("\n-- Brand identity board (gpt-image-2) --")
    result = _gen_brand_board(client, palette, typography, product, positioning, board_brief, quality, images_dir)
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
    args = parser.parse_args()

    if not args.positioning:
        choice_path = paths.CHOICE
        if choice_path.is_file():
            choice = json.loads(choice_path.read_text(encoding="utf-8"))
            args.positioning = choice.get("positioningSlug", "")
        if not args.positioning:
            raise SystemExit("Pass --positioning or set company/choice.json positioningSlug")

    slug = _resolve_slug(args.positioning)

    print(f"Generating brand board for [{slug}] ...")
    out = generate(slug=slug, quality=args.quality)
    print(f"\nDone. Assets at: {out}")


if __name__ == "__main__":
    main()
