"""
WEBSITE concept generator — NOT brand identity.

This is the *website redesign* pipeline. It produces a whole-site layout/content
concept for pep-drink.com, and it is the ONE place that reads the current live
`index.html` (the existing OLD design) as a reference to redesign from.

Distinct from the branding pipeline:
  - Branding  : agents.brand_run -> agents.brand_identity -> agents.brand_images
                (invents palette/typography/logo from a clean slate; never reads
                 the live site; competitors come from static research files).
  - This file : agents.concept_run
                (designs the actual website; reads index.html + competitors.md;
                 can do live web research for competitor sites).

Inputs : active positioning.json, experiments/references/competitors.md,
         current index.html, optional live web search (web_search_preview).
Output : experiments/website-concepts/<timestamp>-<slug>/  (kept separate from
         brand/ so website work never mixes with branding files).

Usage:
  python -m agents.concept_run --brief "Premium light, social protein, venue-led"
  python -m agents.concept_run --brief "..." --no-web-search   # skip live web research
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from agents.llm.env import env_bool, get_openai_api_key, load_project_env
from agents.llm.openai_client import chat_json, make_client, web_research
from agents.schemas import CONCEPT_BUNDLE_SCHEMA

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import paths  # noqa: E402
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "concept_director.md"
REFERENCES_PATH = PROJECT_ROOT / "experiments" / "references" / "competitors.md"
DIRECTIONS_ROOT = paths.DIRECTIONS
WEBSITE_CONCEPTS_DIR = PROJECT_ROOT / "experiments" / "website-concepts"
DEFAULT_BRIEF = (
    "Premium light protein drink for cafés, bars, and terraces. "
    "Whole-site concept: Revized-level clarity, PEP warmth and venue pilot. "
    "Flavour-forward but one SKU live today."
)


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path) or "{}")


def _current_site_summary() -> str:
    index = _read_text(PROJECT_ROOT / "index.html")
    if not index:
        return "(index.html not found)"
    # Keep prompt size reasonable
    return index[:12000] + ("\n...(truncated)" if len(index) > 12000 else "")


def _resolve_positioning_path(positioning_arg: str | None) -> Path:
    if not positioning_arg:
        positioning_arg = _read_json(paths.CHOICE).get("positioningSlug", "")
        if not positioning_arg:
            raise SystemExit("Pass --positioning or set company/choice.json positioningSlug")
    key = positioning_arg.strip().lower()
    aliases = {
        "1": "functional-protein",
        "functional": "functional-protein",
        "functional-protein": "functional-protein",
        "2": "lifestyle",
        "lifestyle": "lifestyle",
        "wellness": "lifestyle",
        "3": "social",
        "social": "social",
    }
    slug = aliases.get(key, key)
    return paths.direction_strategy(slug) / "positioning.json"


def _active_positioning_block(positioning_path: Path) -> str:
    if not positioning_path.is_file():
        return (
            "_No positioning file found. Run: python -m agents.brand_run --positioning 2 "
            "(or 1/3) first._"
        )
    pos = _read_json(positioning_path)
    peers = pos.get("inLineBrands", [])
    peer_lines = "\n".join(
        f"- {p.get('name', '?')}: {p.get('why', '')}" for p in peers[:12]
    )
    return f"""Active product direction: **{pos.get('activeName', '?')}** (id {pos.get('activeId', '?')})
One-liner: {pos.get('oneLiner', '')}
Statement: {pos.get('positioningStatement', '')}
Design concept: {pos.get('visual', {}).get('designConcept', '')}
In-line brands from research (search for sites like these, not gym RTD):
{peer_lines or '- (see positioning.json)'}
Anti-references: {', '.join(a.get('name', '') for a in pos.get('antiReferences', [])[:8])}
"""


def _research_instructions(brief: str, references: str, positioning: str) -> str:
    return f"""Research beverage brand **websites** for a redesign concept.

## PEP active brand direction (must follow)
{positioning}

## User brief
{brief}

## Anchored references
{references}

## Your task
1. Search for 5–8 sites similar to **in-line brands** and the active positioning — NOT generic gym protein RTD.
2. Use lanes from active positioning (occasions, competitors listed in positioning.json).
3. Prefer brands with URLs you can verify; include layout patterns to adapt.
4. Revized = layout-only reference; drinkpep.com = name collision (IA only).
5. List search queries used.

Plain-text research memo. No invented URLs."""


def _concept_user_message(brief: str, references: str, research: str, positioning: str, positioning_path: Path) -> str:
    product = _read_json(paths.PRODUCT_PROFILE)
    design_system = _read_json(paths.FROM_DESIGN / "pep-original" / "design-system.json")
    flavours = _read_json(paths.DESIGN_CONCEPTS / "pep-original" / "product" / "flavours" / "flavours.json")
    site_excerpt = _current_site_summary()
    # brand-guidelines.md lives next to the resolved positioning.json (the direction's strategy folder)
    guidelines = _read_text(positioning_path.parent / "brand-guidelines.md")

    return f"""Create a whole-site concept bundle for PEP (pep-drink.com).

## Active brand positioning (required)
{positioning}

## Brand guidelines excerpt
{guidelines[:8000] if guidelines else '_Run brand_run first._'}

## User brief
{brief}

## Reference notes (anchors + rules)
{references}

## Web research memo
{research or "(Web search disabled — use anchors and general category knowledge; mark discovered URLs only if confident.)"}

## product-profile.json (generic facts)
```json
{json.dumps(product, indent=2)}
```

## Active design tokens (from-design/pep-original — post-processed from proposed design)
```json
{json.dumps(design_system, indent=2)}
```

## flavours.json
```json
{json.dumps(flavours, indent=2)}
```

## Current index.html (excerpt)
```html
{site_excerpt}
```

## Requirements
- `siteConcept.pages.index` and `siteConcept.pages.forVenues` with section specs (hero, drinks, enjoy, about, cta, venues form, etc.)
- Include `anchoredReferences` for Revized and drinkpep.com (drinkpep: nameCollision true)
- `discoveredReferences.discovered`: 5–8 entries from research (or fewer if search was off — be honest)
- `conceptMarkdown`: full readable brief for Lou & Shannon
- siteConcept.id: slug like concept-YYYY-MM-short-name
"""


def run_concept(
    *,
    brief: str,
    use_web_search: bool,
    model: str,
    research_model: str,
    positioning_arg: str | None = None,
) -> Path:
    load_project_env()
    get_openai_api_key()
    client = make_client()

    references = _read_text(REFERENCES_PATH)
    system = _read_text(PROMPT_PATH)
    positioning_path = _resolve_positioning_path(positioning_arg)
    positioning = _active_positioning_block(positioning_path)

    research = ""
    web_ok = False
    if use_web_search:
        print("Searching the web for similar drink brand sites...")
        research, web_ok = web_research(
            client,
            model=research_model,
            instructions=_research_instructions(brief, references, positioning),
        )
        print("Web search:", "ok" if web_ok else "fallback")
    else:
        research = "(Web search disabled by --no-web-search.)"

    print(f"Generating site concept with {model}...")
    bundle = chat_json(
        client,
        model=model,
        system=system,
        user=_concept_user_message(brief, references, research, positioning, positioning_path),
        schema_name="pep_concept_bundle",
        schema=CONCEPT_BUNDLE_SCHEMA,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = bundle["siteConcept"].get("id", "concept").replace(" ", "-")[:48]
    out_dir = WEBSITE_CONCEPTS_DIR / f"{stamp}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "site-concept.json").write_text(
        json.dumps(bundle["siteConcept"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "discovered-references.json").write_text(
        json.dumps(bundle["discoveredReferences"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "concept.md").write_text(
        bundle["conceptMarkdown"].strip() + "\n", encoding="utf-8"
    )
    meta = {
        "brief": brief,
        "webSearch": use_web_search,
        "webSearchOk": web_ok,
        "conceptModel": model,
        "researchModel": research_model,
        "positioningSource": positioning_path.relative_to(PROJECT_ROOT).as_posix()
        if positioning_path.is_file()
        else None,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    if research and use_web_search:
        (out_dir / "research-memo.txt").write_text(research + "\n", encoding="utf-8")

    return out_dir


def main() -> None:
    load_project_env()
    parser = argparse.ArgumentParser(description="PEP Pass 1 — whole-site concept (OpenAI)")
    parser.add_argument("--brief", default=DEFAULT_BRIEF, help="Creative brief for this run")
    parser.add_argument(
        "--no-web-search",
        action="store_true",
        help="Skip web search (anchors + brand only)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CONCEPT_AGENT_MODEL", "gpt-4.1"),
        help="Model for structured concept JSON",
    )
    parser.add_argument(
        "--research-model",
        default=os.environ.get("REVIEW_AGENT_MODEL", "gpt-4o"),
        help="Model for web search step",
    )
    parser.add_argument(
        "--positioning",
        help="Optional positioning to use: 1,2,3 or functional-protein/lifestyle/social",
    )
    args = parser.parse_args()

    use_web = env_bool("CONCEPT_AGENT_WEB_SEARCH", True) and not args.no_web_search
    out_dir = run_concept(
        brief=args.brief.strip(),
        use_web_search=use_web,
        model=args.model,
        research_model=args.research_model,
        positioning_arg=args.positioning,
    )
    print(f"\nDone. Outputs in:\n  {out_dir}\n")
    print("  site-concept.json")
    print("  discovered-references.json")
    print("  concept.md")
    print("\nNext: read concept.md, implement on dev with Cursor, then review_run (when built).")


if __name__ == "__main__":
    main()
