"""
Pass 1 — whole-site concept via OpenAI (optional web search).

Usage:
  python -m agents.concept_run --brief "Premium light, social protein, venue-led"
  python -m agents.concept_run --brief "..." --no-web-search
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from agents.llm.env import env_bool, get_openai_api_key, load_project_env
from agents.llm.openai_client import chat_json, make_client, web_research
from agents.schemas import CONCEPT_BUNDLE_SCHEMA

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "concept_director.md"
REFERENCES_PATH = PROJECT_ROOT / "experiments" / "references" / "competitors.md"
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


def _research_instructions(brief: str, references: str) -> str:
    return f"""Research similar beverage brand websites for a redesign concept.

## PEP (our client)
- Domain: pep-drink.com
- Product: premium protein drink, light and refreshing, social/out-of-home
- Founders: Lou & Shannon (NOT the Beasleys on drinkpep.com)

## User brief
{brief}

## Anchored references (visit / consider these)
{references}

## Your task
1. Search the web for 5–8 additional sites in these lanes:
   - premium RTD / clear protein drinks
   - light functional beverage DTC
   - flavour-forward drink brand websites
   - optional: out-of-home / café-friendly beverage brands
2. For each site found, note URL, brand, why it is relevant, layout patterns worth adapting, and what to avoid.
3. Summarize patterns from Revized (revized-seltzer.com) and drinkpep.com (name collision — IA only).
4. List the search queries you used.

Write a detailed research memo (plain text). Do not invent URLs — only include sites you actually found via search."""


def _concept_user_message(brief: str, references: str, research: str) -> str:
    brand = _read_json(PROJECT_ROOT / "brand" / "brand.json")
    flavours = _read_json(PROJECT_ROOT / "brand" / "product" / "flavours" / "flavours.json")
    site_excerpt = _current_site_summary()

    return f"""Create a whole-site concept bundle for PEP (pep-drink.com).

## User brief
{brief}

## Reference notes (anchors + rules)
{references}

## Web research memo
{research or "(Web search disabled — use anchors and general category knowledge; mark discovered URLs only if confident.)"}

## brand.json
```json
{json.dumps(brand, indent=2)}
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
) -> Path:
    load_project_env()
    get_openai_api_key()
    client = make_client()

    references = _read_text(REFERENCES_PATH)
    system = _read_text(PROMPT_PATH)

    research = ""
    web_ok = False
    if use_web_search:
        print("Searching the web for similar drink brand sites...")
        research, web_ok = web_research(
            client,
            model=research_model,
            instructions=_research_instructions(brief, references),
        )
        print("Web search:", "ok" if web_ok else "fallback")
    else:
        research = "(Web search disabled by --no-web-search.)"

    print(f"Generating site concept with {model}...")
    bundle = chat_json(
        client,
        model=model,
        system=system,
        user=_concept_user_message(brief, references, research),
        schema_name="pep_concept_bundle",
        schema=CONCEPT_BUNDLE_SCHEMA,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = bundle["siteConcept"].get("id", "concept").replace(" ", "-")[:48]
    out_dir = PROJECT_ROOT / "experiments" / "concepts" / f"{stamp}-{slug}"
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
    args = parser.parse_args()

    use_web = env_bool("CONCEPT_AGENT_WEB_SEARCH", True) and not args.no_web_search
    out_dir = run_concept(
        brief=args.brief.strip(),
        use_web_search=use_web,
        model=args.model,
        research_model=args.research_model,
    )
    print(f"\nDone. Outputs in:\n  {out_dir}\n")
    print("  site-concept.json")
    print("  discovered-references.json")
    print("  concept.md")
    print("\nNext: read concept.md, implement on dev with Cursor, then review_run (when built).")


if __name__ == "__main__":
    main()
