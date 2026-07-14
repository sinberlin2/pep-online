"""
Pass 1.5 — competitor DESIGN THEMES (the only output).

Analyses the competitor images and writes `design-themes.json` — 2–4 recurring visual looks
per direction (base / colour / finish shiny-vs-matte / typography), each tagged with the
positioning it reads as. The brand board (brand_images) is generated later directly from the
strategy + a chosen theme, so this step no longer produces a palette, fonts, mockups, or a logo.

By default runs in direction mode (analyses competitors only — no existing design assets).
Pass --from-design [SLUG] to also attach an existing design set under
brand/inputs/external-designs/<slug> (default slug: pep-original). The reference images fed to the
model are listed in that folder's JSON manifest (brand/inputs/external-designs/<slug>/extraction-images.json),
not hardcoded — so you can extract from any provided design, and override the manifest
path with --design-manifest.

Usage:
  python -m agents.brand_identity
  python -m agents.brand_identity --positioning 2
  python -m agents.brand_identity --provider anthropic
  python -m agents.brand_identity --from-design                 # extract from pep-original
  python -m agents.brand_identity --from-design my-other-design # extract from brand/inputs/external-designs/my-other-design
  python -m agents.brand_identity --from-design --design-manifest path/to/list.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

# Max competitor images fed to the vision model for theme extraction. Downscaled
# already (see scripts/fetch_competitor_images.py) and sent at detail="low" to bound cost.
MAX_THEME_IMAGES = 28

def _design_image_paths(provided_slug: str, manifest: Path | None = None) -> list[Path]:
    """Curated reference images fed to the vision model in extraction mode.

    Data-driven: read from a JSON manifest (a list of paths relative to the provided
    design folder brand/inputs/external-designs/<slug>) rather than a hardcoded list. Works for any
    provided design set, not just pep-original. Only files that exist are returned, so
    a missing entry is silently skipped.
    """
    base = paths.external_design_dir(provided_slug)
    manifest = manifest or paths.external_design_manifest(provided_slug)
    if not manifest.is_file():
        return []
    try:
        entries = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return []
    resolved: list[Path] = []
    for entry in entries:
        p = base / str(entry)
        if p.is_file():
            resolved.append(p)
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path) or "{}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _priority_slugs(positioning: dict) -> set[str]:
    """Brands most relevant to the active direction — shown first, never dropped by the cap."""
    names: list[str] = []
    for b in positioning.get("inLineBrands", []):
        names.append(b.get("name", ""))
    for b in positioning.get("positioningFitTypeMismatch", []):
        names.append(b.get("name", ""))
    return {_norm(n) for n in names if n}


def _competitor_image_entries(positioning: dict) -> list[tuple[Path, str, object]]:
    """Ordered (path, brand, positioning_id) from the competitor image manifest.

    Whole competitor set (so cross-positioning looks are visible), active-direction
    peers first, capped at MAX_THEME_IMAGES.
    """
    manifest_path = paths.COMPETITION_IMAGES_MANIFEST
    if not manifest_path.is_file():
        return []
    try:
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    priority = _priority_slugs(positioning)
    resolved: list[tuple[Path, str, object, bool]] = []
    for e in entries:
        p = paths.COMPETITION / (e.get("file") or "")
        if not p.is_file():
            continue
        is_priority = _norm(e.get("brand", "")) in priority
        resolved.append((p, e.get("brand", ""), e.get("positioning_id", ""), is_priority))

    resolved.sort(key=lambda r: 0 if r[3] else 1)  # stable: priority first, else original order
    resolved = resolved[:MAX_THEME_IMAGES]
    return [(p, brand, pid) for (p, brand, pid, _) in resolved]


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


def _competitor_images_block(
    competitor_entries: list[tuple[Path, str, object]], from_design: bool
) -> str:
    if not competitor_entries:
        return (
            "## Competitor images\n"
            "_None available — run `npm run brand:competitor-images` first. "
            "Extract observedDesignThemes from the competitor tiers/notes below instead._"
        )
    lines = [
        "## Attached competitor images — analyse these for `observedDesignThemes`",
        "These are COMPETITOR packs/sites (NOT PEP). Read them to identify 2–4 recurring "
        "visual looks (base treatment, colour treatment, finish shiny-vs-matte, typography), "
        "tag each with the positioning it most reads as, then ground PEP's palette in the "
        "theme(s) that fit the active direction. Never copy a competitor's exact look.",
        "",
        "Image order:",
    ]
    for i, (_, brand, pid) in enumerate(competitor_entries, 1):
        lines.append(f"{i}. {brand} — competitor positioning {pid}")
    if from_design:
        lines.append(
            f"{len(competitor_entries) + 1}+. The remaining images are the existing "
            "design assets being extracted, NOT competitors."
        )
    return "\n".join(lines)


def _user_message(
    positioning: dict,
    competitor_entries: list[tuple[Path, str, object]] | None = None,
    from_design: bool = False,
    provided_slug: str = paths.DEFAULT_DESIGN_SLUG,
) -> str:
    product = _read_json(paths.PRODUCT_PROFILE)
    competitor_entries = competitor_entries or []

    design_block = ""
    if from_design:
        existing_ds = _read_json(paths.external_design_dir(provided_slug) / "extracted" / "design-system.json")
        design_block = f"""
## Existing extracted design tokens (from the '{provided_slug}' design)
These are the confirmed colours and fonts from the existing design.
Use these as your extraction foundation — refine and systematise what you observe.
```json
{json.dumps(existing_ds, indent=2)}
```

## Attached design images
The images show the existing '{provided_slug}' design concept. Extract and confirm colours, fonts, and layout patterns from them.
"""
    else:
        design_block = """
## Invention mode
You are inventing a fresh visual identity for this brand direction.
Do NOT reference or constrain yourself to any existing PEP design.
Invent colours, typography, and layout language that best express the strategy below.
"""

    competitor_images_block = _competitor_images_block(competitor_entries, from_design)

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

    return f"""Extract the recurring competitor design themes for PEP ({positioning.get('activeName', '')} direction).

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
{competitor_images_block}

{_competitor_block(positioning)}

## Your task
Produce **only** `observedDesignThemes` — from the attached competitor images, 2–4 recurring
looks (base treatment, colour treatment, finish shiny-vs-matte, typography feel, energy), each
with example brands (name the specific product line if the look is line-specific) and the
positioning it most reads as (1=functional, 2=lifestyle, 3=social), plus how each applies to
this direction. Do NOT invent a palette, fonts, mockups, or a logo — the brand board is
generated later directly from the strategy + a chosen theme.
"""


def _resolve_positioning(positioning_arg: str | None) -> tuple[dict, Path]:
    if not positioning_arg:
        choice = _read_json(paths.CHOICE)
        positioning_arg = choice.get("positioningSlug", "")
        if not positioning_arg:
            raise SystemExit("Pass --positioning or set brand/inputs/choice.json positioningSlug")

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
    provided_slug: str = paths.DEFAULT_DESIGN_SLUG,
    design_manifest: Path | None = None,
) -> Path:
    load_project_env()
    client, vision_json = _llm_backend(provider)

    positioning, pos_path = _resolve_positioning(positioning_arg)
    slug = positioning.get("activeSlug", "")
    if not slug:
        raise SystemExit("positioning.json missing activeSlug")

    if from_design and not paths.external_design_dir(provided_slug).is_dir():
        raise SystemExit(
            f"No provided design at {paths.external_design_dir(provided_slug)} — "
            f"expected brand/inputs/external-designs/{provided_slug}/ (with extraction-images.json)."
        )

    model = model or PROVIDER_DEFAULTS[provider]["model"]
    system = _read_text(PROMPT_PATH)

    # Competitor images (for observedDesignThemes) go first, in both modes; provided-design
    # images (for extraction) come from the manifest and are appended only in from-design mode.
    competitor_entries = _competitor_image_entries(positioning)
    competitor_paths = [e[0] for e in competitor_entries]
    pep_paths = _design_image_paths(provided_slug, design_manifest) if from_design else []
    image_paths = competitor_paths + pep_paths

    mode = f"from-design (extraction from '{provided_slug}')" if from_design else "from-direction (invention)"
    print(f"Building identity for [{positioning.get('activeId')}] {positioning.get('activeName')} [{provider}/{model}] — {mode}")
    print(f"  Competitor images: {len(competitor_paths)}" + (f" | design images: {[p.name for p in pep_paths]}" if pep_paths else ""))
    if not competitor_paths:
        print("  (no competitor images — run `npm run brand:competitor-images` for image-based themes)")
    if from_design and not pep_paths:
        manifest = design_manifest or paths.external_design_manifest(provided_slug)
        print(f"  (no extraction images — add reference paths to {manifest})")

    bundle = vision_json(
        client,
        model=model,
        system=system,
        user=_user_message(positioning, competitor_entries, from_design=from_design, provided_slug=provided_slug),
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
        "providedSource": provided_slug if from_design else None,
        "visionImages": [p.name for p in image_paths],
    }
    (identity_dir / "identity-meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    return identity_dir


def _write_outputs(bundle: dict, out_dir: Path) -> None:
    # Themes-only step: the design themes are the sole output. The brand board (brand_images)
    # is generated directly from positioning.json + a chosen theme — no palette/typography/
    # mockup/logo/board-brief JSON is produced here anymore.
    (out_dir / "design-themes.json").write_text(
        json.dumps(bundle.get("observedDesignThemes", []), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="PEP brand_identity — colour palette, typography, mockup briefs")
    parser.add_argument(
        "--positioning",
        default=None,
        help="1, 2, 3 or slug (default: brand/inputs/choice.json positioningSlug)",
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
        nargs="?",
        const=paths.DEFAULT_DESIGN_SLUG,
        default=None,
        metavar="PROVIDED_SLUG",
        help=(
            "Extraction mode: extract from an existing design under brand/inputs/external-designs/<slug> "
            f"(bare flag uses '{paths.DEFAULT_DESIGN_SLUG}'). Omit entirely for invention mode."
        ),
    )
    parser.add_argument(
        "--design-manifest",
        default=None,
        help="Override the extraction-mode image manifest (default: brand/inputs/external-designs/<slug>/extraction-images.json).",
    )
    args = parser.parse_args()

    out = run_identity(
        positioning_arg=args.positioning,
        model=args.model,
        provider=args.provider,
        from_design=args.from_design is not None,
        provided_slug=args.from_design or paths.DEFAULT_DESIGN_SLUG,
        design_manifest=Path(args.design_manifest) if args.design_manifest else None,
    )
    print(f"\nDesign themes written to: {out / 'design-themes.json'}")
    print("\nNext: npm run brand:images  (generate the brand board from a theme)")


if __name__ == "__main__":
    main()
