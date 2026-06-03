"""
Pass 0 — brand positioning for a chosen product direction (1/2/3).

Usage:
  python scripts/parse_positioning_options.py
  python scripts/extract_competition_pdf.py   # after PDF is in brand/research/
  python scripts/merge_brand_research.py
  python -m agents.brand_run --positioning 2
  python -m agents.brand_run --positioning lifestyle
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agents.brand_schemas import BRAND_BUNDLE_SCHEMA
from agents.llm.env import get_openai_api_key, load_project_env
from agents.llm.openai_client import chat_json, make_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESEARCH = PROJECT_ROOT / "brand" / "research"
ACTIVE_DIR = RESEARCH / "active"
DIRECTIONS_DIR = RESEARCH / "directions"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "brand_strategist.md"
OPTIONS_PATH = RESEARCH / "positioning-options.json"
BUNDLE_PATH = RESEARCH / "research-bundle.md"
CHARACTERISTICS_PATH = RESEARCH / "characteristics.csv"


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
    if not CHARACTERISTICS_PATH.is_file():
        return "_No characteristics.csv — run extract_competition_pdf.py first._"
    import csv

    lines = []
    with CHARACTERISTICS_PATH.open(encoding="utf-8-sig", newline="") as f:
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
    brand = _read_json(PROJECT_ROOT / "brand" / "brand.json")
    bundle = _read_text(BUNDLE_PATH)
    active_id = active["id"]

    return f"""Create brand positioning for **one** selected product direction only.

## Selected direction (ACTIVE — build the whole brand here)
- id: {active['id']}
- slug: {active['slug']}
- name: {active['name']}

### Dimensions from Mural
```json
{json.dumps(active.get('dimensions', {}), indent=2, ensure_ascii=False)}
```

## All three directions (for context only — do not blend)
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

## brand.json
```json
{json.dumps(brand, indent=2)}
```

Output brand guidelines for Lou & Shannon implementing **{active['name']}** only.
"""


def run_brand(*, positioning_arg: str, model: str, set_active: bool = True) -> Path:
    load_project_env()
    get_openai_api_key()
    if not OPTIONS_PATH.is_file():
        raise SystemExit("Run: python scripts/parse_positioning_options.py")

    options_doc = _read_json(OPTIONS_PATH)
    options = options_doc.get("options", [])
    active = resolve_positioning_arg(positioning_arg, options)

    client = make_client()
    system = _read_text(PROMPT_PATH)
    print(f"Building brand for [{active['id']}] {active['name']} ({active['slug']})...")

    bundle = chat_json(
        client,
        model=model,
        system=system,
        user=_user_message(active, options_doc),
        schema_name="pep_brand_bundle",
        schema=BRAND_BUNDLE_SCHEMA,
    )

    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    DIRECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    pos = bundle["positioning"]
    pos["domain"] = pos.get("domain") or "pep-drink.com"
    pos["brand"] = pos.get("brand") or "PEP"

    direction_dir = DIRECTIONS_DIR / active["slug"]
    direction_dir.mkdir(parents=True, exist_ok=True)
    (direction_dir / "positioning.json").write_text(
        json.dumps(pos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (direction_dir / "brand-guidelines.md").write_text(
        bundle["brandGuidelinesMarkdown"].strip() + "\n", encoding="utf-8"
    )
    meta = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "selectedPositioning": active["slug"],
        "selectedId": active["id"],
    }
    (direction_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if set_active:
        (ACTIVE_DIR / "positioning.json").write_text(
            json.dumps(pos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (ACTIVE_DIR / "brand-guidelines.md").write_text(
            bundle["brandGuidelinesMarkdown"].strip() + "\n", encoding="utf-8"
        )
        (ACTIVE_DIR / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # Archive copy per direction
    archive = RESEARCH / "runs" / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{active['slug']}"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "positioning.json").write_text(
        json.dumps(pos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (archive / "brand-guidelines.md").write_text(
        bundle["brandGuidelinesMarkdown"].strip() + "\n", encoding="utf-8"
    )

    return direction_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="PEP brand_run — one positioning direction")
    parser.add_argument(
        "--positioning",
        required=True,
        help="1, 2, 3, or slug: functional-protein | lifestyle | wellness | social",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CONCEPT_AGENT_MODEL", "gpt-4.1"),
    )
    parser.add_argument(
        "--no-set-active",
        action="store_true",
        help="Generate direction files only; keep current active selection unchanged.",
    )
    args = parser.parse_args()
    out = run_brand(
        positioning_arg=args.positioning,
        model=args.model,
        set_active=not args.no_set_active,
    )
    print(
        f"\nDirection brand written to:\n  {out / 'positioning.json'}\n  {out / 'brand-guidelines.md'}"
    )
    if not args.no_set_active:
        print(
            "\nAlso updated active brand:\n"
            f"  {ACTIVE_DIR / 'positioning.json'}\n"
            f"  {ACTIVE_DIR / 'brand-guidelines.md'}"
        )
    print("\nNext: python -m agents.concept_run")


if __name__ == "__main__":
    main()
