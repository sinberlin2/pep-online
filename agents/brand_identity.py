"""
Pass 1.5 — brand identity: colour palette, typography system, and mockup briefs.

Invents a complete visual identity from the brand strategy (positioning.json).
By default runs in direction mode (pure invention — no existing design assets).
Pass --from-design to also feed the pep-original design images to the model
(useful only when extracting/refining from an existing visual concept).

Usage:
  python -m agents.brand_identity
  python -m agents.brand_identity --positioning 2
  python -m agents.brand_identity --provider anthropic
  python -m agents.brand_identity --from-design   # extract from pep-original assets
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import paths  # noqa: E402

from agents.brand_schemas import BRAND_IDENTITY_SCHEMA
from agents.llm.env import get_anthropic_api_key, get_openai_api_key, load_project_env

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "brand_identity.md"

PROVIDER_DEFAULTS = {
    "openai": {"model": "gpt-5.5"},
    "anthropic": {"model": "claude-opus-4-8"},
}

# Key design images to pass to the vision model (in priority order).
# Only files that actually exist are sent.
DESIGN_IMAGE_CANDIDATES = [
    paths.PROVIDED / "pep-original" / "marketing" / "originals" / "pep-flyer.png",
    paths.PROVIDED / "pep-original" / "marketing" / "originals" / "design-reference-full.png",
    paths.PROVIDED / "pep-original" / "identity" / "originals" / "logo-pep.png",
    paths.PROVIDED / "pep-original" / "product" / "bg_removed" / "pep-can-background-removed.png",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path) or "{}")


def _llm_backend(provider: str):
    if provider == "anthropic":
        from agents.llm.anthropic_client import make_client, vision_json
        get_anthropic_api_key()
        return make_client(), vision_json
    if provider == "openai":
        from agents.llm.openai_client import make_client, vision_json
        get_openai_api_key()
        return make_client(), vision_json
    raise SystemExit(f"Unknown provider {provider!r} (use openai or anthropic)")


def _competitor_block(positioning: dict) -> str:
    lines = ["## Competitor tiers for visual inspiration", ""]

    in_line = positioning.get("inLineBrands", [])
    if in_line:
        lines.append("### Tier 1 — inLineBrands (direct peers — borrow freely)")
        for b in in_line:
            patterns = "; ".join(b.get("designPatterns", []))
            lines.append(f"- **{b['name']}** ({b.get('category', '')}): {patterns}")
        lines.append("")

    mismatch = positioning.get("positioningFitTypeMismatch", [])
    if mismatch:
        lines.append("### Tier 2 — positioningFitTypeMismatch (adjacent visual language — selective borrowing)")
        for b in mismatch:
            lines.append(
                f"- **{b['name']}** ({b.get('category', '')}): "
                f"branding fits={b.get('whyBrandingFits', '')} | "
                f"type mismatch={b.get('typeMismatch', '')}"
            )
        lines.append("")

    peers = positioning.get("peerBrandsOtherPositionings", [])
    if peers:
        lines.append("### Tier 3 — peerBrandsOtherPositionings (cross-lane — note what to avoid AND what might transfer)")
        for b in peers:
            lines.append(
                f"- **{b['name']}** (positioning {b.get('positioning_id', '?')}): "
                f"{b.get('whyNotActive', '')}"
            )
        lines.append("")

    anti = positioning.get("antiReferences", [])
    if anti:
        lines.append("### Hard anti-references (never use visually)")
        for b in anti:
            lines.append(f"- **{b['name']}**: {b.get('why', '')}")
        lines.append("")

    return "\n".join(lines)


def _user_message(positioning: dict, from_design: bool = False) -> str:
    product = _read_json(paths.PRODUCT_PROFILE)

    design_block = ""
    if from_design:
        existing_ds = _read_json(paths.PROVIDED / "pep-original" / "extracted" / "design-system.json")
        design_block = f"""
## Existing extracted design tokens (from pep-original concept)
These are the confirmed colours and fonts from the existing PEP design.
Use these as your extraction foundation — refine and systematise what you observe.
```json
{json.dumps(existing_ds, indent=2)}
```

## Attached design images
The images show the existing PEP design concept. Extract and confirm colours, fonts, and layout patterns from them.
"""
    else:
        design_block = """
## Invention mode
You are inventing a fresh visual identity for this brand direction.
Do NOT reference or constrain yourself to any existing PEP design.
Invent colours, typography, and layout language that best express the strategy below.
"""

    visual = positioning.get("visual", {})

    # In invention mode the typography and colour direction fields reference the
    # EXISTING PEP brand (Didot, Montserrat, Brittany Signature, green/cream palette).
    # Injecting them anchors the model to the old identity — exactly what we don't want.
    # Suppress them in invention mode and rely on the competitor anchoring table instead.
    if from_design:
        typography_line = f"- Typography direction: {visual.get('typography', '')}"
        mood_line = f"- Mood: {visual.get('mood', '')}"
    else:
        typography_line = (
            "- Typography direction: **IGNORE any fonts referenced in the strategy — "
            "those are the existing PEP brand fonts. Use the direction-to-competitor "
            "anchoring table in the system prompt to choose a genuinely different typeface.**"
        )
        mood_line = (
            f"- Mood (use for occasion/personality only — NOT for colour or font): "
            f"{visual.get('mood', '')}"
        )

    return f"""Create a complete visual identity system for PEP ({positioning.get('activeName', '')} direction).

## Brand strategy summary
- Direction: {positioning.get('activeName', '')} (id {positioning.get('activeId', '')})
- Direction slug: {positioning.get('activeSlug', '')}
- One-liner: {positioning.get('oneLiner', '')}
{mood_line}
- Design concept: {visual.get('designConcept', '')}
{typography_line}
- Reject looks: {', '.join(visual.get('rejectLooks', []))}

## Product facts
```json
{json.dumps(product, indent=2)}
```
{design_block}
{_competitor_block(positioning)}

## Your task
Produce:
1. A colour palette (primary, secondary, text, background swatches with hex + role + competitor inspiration).
2. A complete typography system (display, body, script, badge — with pairing rationale).
3. 4–6 mockup briefs covering: can label, social post, venue card, brand hero, product lifestyle, story ad.
4. identityMarkdown — a clean human-readable identity guide for Lou & Shannon.
5. A logoBrief with the logo concept, a precise mark description, and 3 image generation prompts.
"""


def _resolve_positioning(positioning_arg: str | None) -> tuple[dict, Path]:
    if not positioning_arg:
        choice = _read_json(paths.CHOICE)
        positioning_arg = choice.get("positioningSlug", "")
        if not positioning_arg:
            raise SystemExit("Pass --positioning or set company/choice.json positioningSlug")

    aliases = {
        "1": "functional-protein", "functional": "functional-protein", "functional-protein": "functional-protein",
        "2": "lifestyle", "lifestyle": "lifestyle", "wellness": "lifestyle",
        "3": "social", "social": "social",
    }
    slug = aliases.get(positioning_arg.strip().lower(), positioning_arg.strip().lower())
    p = paths.direction_strategy(slug) / "positioning.json"
    if not p.is_file():
        raise SystemExit(f"No positioning.json found at {p}. Run brand_run first.")
    return _read_json(p), p


def run_identity(
    *,
    positioning_arg: str | None = None,
    model: str | None = None,
    provider: str = "openai",
    from_design: bool = False,
) -> Path:
    load_project_env()
    client, vision_json = _llm_backend(provider)

    positioning, pos_path = _resolve_positioning(positioning_arg)
    slug = positioning.get("activeSlug", "")
    if not slug:
        raise SystemExit("positioning.json missing activeSlug")

    model = model or PROVIDER_DEFAULTS[provider]["model"]
    system = _read_text(PROMPT_PATH)

    image_paths = [p for p in DESIGN_IMAGE_CANDIDATES if p.is_file()] if from_design else []

    mode = "from-design (extraction)" if from_design else "from-direction (invention)"
    print(f"Building identity for [{positioning.get('activeId')}] {positioning.get('activeName')} [{provider}/{model}] — {mode}")
    if image_paths:
        print(f"  Vision inputs: {[p.name for p in image_paths]}")

    bundle = vision_json(
        client,
        model=model,
        system=system,
        user=_user_message(positioning, from_design=from_design),
        image_paths=image_paths,
        schema_name="pep_brand_identity",
        schema=BRAND_IDENTITY_SCHEMA,
    )

    identity_dir = paths.direction_identity(slug)
    identity_dir.mkdir(parents=True, exist_ok=True)

    _write_outputs(bundle, identity_dir)

    meta = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "provider": provider,
        "selectedPositioning": slug,
        "mode": "from-design" if from_design else "from-direction",
        "visionImages": [p.name for p in image_paths],
    }
    (identity_dir / "identity-meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    return identity_dir


def _write_outputs(bundle: dict, out_dir: Path) -> None:
    (out_dir / "color-palette.json").write_text(
        json.dumps(bundle["colorPalette"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "typography.json").write_text(
        json.dumps(bundle["typographySystem"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "mockup-briefs.json").write_text(
        json.dumps(bundle["mockupBriefs"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "identity-guidelines.md").write_text(
        bundle["identityMarkdown"].strip() + "\n", encoding="utf-8"
    )
    if "logoBrief" in bundle:
        (out_dir / "logo-brief.json").write_text(
            json.dumps(bundle["logoBrief"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if "boardBrief" in bundle:
        (out_dir / "board-brief.json").write_text(
            json.dumps(bundle["boardBrief"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="PEP brand_identity — colour palette, typography, mockup briefs")
    parser.add_argument(
        "--positioning",
        default=None,
        help="1, 2, 3 or slug (default: company/choice.json positioningSlug)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model override (default per provider)",
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("BRAND_PROVIDER", "openai"),
        choices=["openai", "anthropic"],
    )
    parser.add_argument(
        "--from-design",
        action="store_true",
        help="Feed existing pep-original design images to the model (extraction mode). Default: invention from strategy only.",
    )
    args = parser.parse_args()

    out = run_identity(
        positioning_arg=args.positioning,
        model=args.model,
        provider=args.provider,
        from_design=args.from_design,
    )
    print(f"\nIdentity written to: {out}")
    print("  identity/color-palette.json")
    print("  identity/typography.json")
    print("  identity/mockup-briefs.json")
    print("  identity/identity-guidelines.md")
    print("  identity/logo-brief.json")
    print("  identity/board-brief.json")
    print("\nNext: npm run brand:images  (or  npm run brand:package)")


if __name__ == "__main__":
    main()
