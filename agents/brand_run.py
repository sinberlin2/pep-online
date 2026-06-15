"""
Pass 0 — brand positioning for a chosen product direction (1/2/3).

Usage:
  python scripts/parse_positioning_options.py
  python scripts/extract_competition_pdf.py   # PDF in company/competition/sources/
  python scripts/merge_brand_research.py
  python -m agents.brand_run --positioning 2
  python -m agents.brand_run --positioning lifestyle
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import paths  # noqa: E402

from agents.brand_schemas import BRAND_BUNDLE_SCHEMA
from agents.llm.env import get_anthropic_api_key, get_openai_api_key, load_project_env

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "brand_strategist.md"

PROVIDER_DEFAULTS = {
    "openai": "gpt-5.5",
    "anthropic": "claude-sonnet-4-6",
}


def _llm_backend(provider: str):
    if provider == "anthropic":
        from agents.llm.anthropic_client import chat_json, make_client

        get_anthropic_api_key()
        return make_client(), chat_json
    if provider == "openai":
        from agents.llm.openai_client import chat_json, make_client

        get_openai_api_key()
        return make_client(), chat_json
    raise SystemExit(f"Unknown provider {provider!r} (use openai or anthropic)")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path) or "{}")


def resolve_positioning_arg(arg: str, options: list[dict]) -> dict:
    key = arg.strip().lower()
    for opt in options:
        if key == str(opt["id"]):
            return opt
        if key == opt["slug"].lower():
            return opt
        if key == opt["name"].lower():
            return opt
        if key in [a.lower() for a in opt.get("aliases", [])]:
            return opt
    ids = ", ".join(f"{o['id']}={o['slug']}" for o in options)
    raise SystemExit(f"Unknown --positioning {arg!r}. Use one of: {ids}")


def _brands_for_prompt(active_id: int) -> str:
    if not paths.CHARACTERISTICS_CSV.is_file():
        return "_No characteristics.csv — run extract_competition_pdf.py first._"
    import csv

    lines = []
    with paths.CHARACTERISTICS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pid = (row.get("positioning_id") or "").strip()
            match = pid == str(active_id)
            tag = "PRIMARY PEER" if match else f"other positioning ({pid})"
            lines.append(
                f"- **{row.get('brand_name', '?')}** [{tag}] "
                f"category={row.get('category', '')} | "
                f"adjectives={row.get('adjectives', '')} | "
                f"visual={row.get('visual_design_notes', '')} | "
                f"why={row.get('why_in_or_out', '')}"
            )
    return "\n".join(lines) if lines else "_Empty CSV._"


def _user_message(active: dict, options_doc: dict) -> str:
    product = _read_json(paths.PRODUCT_PROFILE)
    bundle = _read_text(paths.RESEARCH_BUNDLE)
    active_id = active["id"]

    return f"""Create brand positioning for **one** selected product direction only.

## Selected direction (build the whole brand here)
- id: {active['id']}
- slug: {active['slug']}
- name: {active['name']}

### Dimensions from Mural
```json
{json.dumps(active.get('dimensions', {}), indent=2, ensure_ascii=False)}
```

## All three directions (context only)
Build the selected direction authentically from ITS OWN competitors and dimensions —
whatever vibe that genuinely implies. Do NOT force it to look different from the other
two directions; if their competitor sets overlap, some overlap in feel is fine. Just
don't merge all three into one generic blend.
```json
{json.dumps(options_doc.get('options', []), indent=2, ensure_ascii=False)}
```

## Competition table brands (from PDF extraction)
{_brands_for_prompt(active_id)}

Rules:
- **inLineBrands**: brands whose positioning_id matches {active_id}, plus any you strongly justify as peers for this direction only.
- **peerBrandsOtherPositionings**: brands from CSV with different positioning_id — explain why they are NOT PEP's direction.
- **antiReferences**: gym-bro protein, drinkpep.com name collision, anything that conflicts with this direction.
- **layoutOnlyReferences**: Revized if relevant for web structure only.
- **visual.designConcept**: use the "Design concept" dimension from the active column in positioning options.
- **domain**: pep-drink.com

## research-bundle.md
{bundle or '_Run merge_brand_research.py_'}

## product-profile.json (generic facts — name, tagline, protein/calories)
```json
{json.dumps(product, indent=2)}
```

Output brand guidelines for Lou & Shannon implementing **{active['name']}** only.
"""


def run_brand(
    *,
    positioning_arg: str,
    model: str | None = None,
    provider: str = "openai",
) -> Path:
    load_project_env()
    if not paths.POSITIONING_OPTIONS.is_file():
        raise SystemExit("Run: python scripts/parse_positioning_options.py")

    model = model or PROVIDER_DEFAULTS.get(provider) or PROVIDER_DEFAULTS["openai"]
    client, chat_json = _llm_backend(provider)

    options_doc = _read_json(paths.POSITIONING_OPTIONS)
    options = options_doc.get("options", [])
    active = resolve_positioning_arg(positioning_arg, options)

    system = _read_text(PROMPT_PATH)
    print(f"Building brand for [{active['id']}] {active['name']} ({active['slug']}) [{provider}/{model}]...")

    bundle = chat_json(
        client,
        model=model,
        system=system,
        user=_user_message(active, options_doc),
        schema_name="pep_brand_bundle",
        schema=BRAND_BUNDLE_SCHEMA,
    )

    paths.DIRECTIONS.mkdir(parents=True, exist_ok=True)
    pos = bundle["positioning"]
    pos["domain"] = pos.get("domain") or "pep-drink.com"
    pos["brand"] = pos.get("brand") or "PEP"

    direction_dir = paths.DIRECTIONS / active["slug"]
    direction_dir.mkdir(parents=True, exist_ok=True)
    strategy_dir = paths.direction_strategy(active["slug"])
    strategy_dir.mkdir(parents=True, exist_ok=True)
    (strategy_dir / "positioning.json").write_text(
        json.dumps(pos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (strategy_dir / "brand-guidelines.md").write_text(
        bundle["brandGuidelinesMarkdown"].strip() + "\n", encoding="utf-8"
    )
    meta = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "provider": provider,
        "selectedPositioning": active["slug"],
        "selectedId": active["id"],
    }
    (strategy_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # Archive copy per direction
    archive = paths.RUNS / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{active['slug']}"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "positioning.json").write_text(
        json.dumps(pos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (archive / "brand-guidelines.md").write_text(
        bundle["brandGuidelinesMarkdown"].strip() + "\n", encoding="utf-8"
    )

    return direction_dir


def _default_positioning_arg() -> str:
    choice = _read_json(paths.CHOICE)
    slug = choice.get("positioningSlug", "")
    if slug:
        return slug
    raise SystemExit("Pass --positioning or set company/choice.json positioningSlug")


def main() -> None:
    parser = argparse.ArgumentParser(description="PEP brand_run — one positioning direction")
    parser.add_argument(
        "--positioning",
        default=None,
        help="1, 2, 3, or slug (default: company/choice.json positioningSlug)",
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
    args = parser.parse_args()
    positioning = args.positioning or _default_positioning_arg()
    out = run_brand(
        positioning_arg=positioning,
        model=args.model,
        provider=args.provider,
    )
    print(
        f"\nDirection brand written to:\n  {out / 'strategy' / 'positioning.json'}\n  {out / 'strategy' / 'brand-guidelines.md'}"
    )
    print("\nNext: python -m agents.concept_run")


if __name__ == "__main__":
    main()
