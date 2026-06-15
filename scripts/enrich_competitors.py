"""
Merge manual competitors and enrich URLs/notes via OpenAI web research.

Usage:
  python scripts/enrich_competitors.py
  python scripts/enrich_competitors.py --limit 50
  python scripts/enrich_competitors.py --overwrite-notes

Inputs:
  company/competition/characteristics.csv
  company/competition/manual-competitors.csv (optional)

Outputs:
  company/competition/characteristics.csv
  company/competition/competition-extracted.json
  company/competition/competitor-enrichment-log.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.llm.env import get_openai_api_key, load_project_env
from agents.llm.openai_client import chat_json, make_client, web_research

import paths  # noqa: E402

CHAR_PATH = paths.CHARACTERISTICS_CSV
MANUAL_PATH = paths.MANUAL_COMPETITORS
COMP_JSON_PATH = paths.COMPETITION_EXTRACTED
LOG_PATH = paths.ENRICHMENT_LOG
MANUAL_FIELDS = ["brand_name", "category", "positioning_id"]

FIELDS = [
    "brand_name",
    "url",
    "category",
    "positioning_id",
    "positioning_name",
    "in_line",
    "use_cases",
    "adjectives",
    "visual_design_notes",
    "product_traits",
    "why_in_or_out",
    "lane",
]

ENRICH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "official_name": {"type": "string"},
        "official_url": {"type": "string"},
        "category": {"type": "string"},
        "use_cases": {"type": "string"},
        "adjectives": {"type": "string"},
        "visual_design_notes": {"type": "string"},
        "product_traits": {"type": "string"},
        "why_in_or_out": {"type": "string"},
        "lane": {"type": "string"},
    },
    "required": [
        "official_name",
        "official_url",
        "category",
        "use_cases",
        "adjectives",
        "visual_design_notes",
        "product_traits",
        "why_in_or_out",
        "lane",
    ],
}


def _normalize_brand(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").strip().lower())


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({k: (row.get(k, "") or "").strip() for k in FIELDS})
        return rows


def _read_manual_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({k: (row.get(k, "") or "").strip() for k in MANUAL_FIELDS})
        return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def _write_manual_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANUAL_FIELDS)
        w.writeheader()
        w.writerows(rows)


def _merge_manual(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int, list[dict[str, str]]]:
    manual = _read_manual_csv(MANUAL_PATH)
    if not manual:
        return rows, 0, []

    existing = {_normalize_brand(r["brand_name"]) for r in rows if r.get("brand_name")}
    added = 0
    for m in manual:
        key = _normalize_brand(m.get("brand_name", ""))
        if not key or key in existing:
            continue
        base = {k: "" for k in FIELDS}
        base["brand_name"] = (m.get("brand_name") or "").strip()
        base["category"] = (m.get("category") or "").strip()
        base["positioning_id"] = (m.get("positioning_id") or "").strip()
        if base["positioning_id"] == "1":
            base["positioning_name"] = "Functional protein drink"
        elif base["positioning_id"] == "2":
            base["positioning_name"] = "Lifestyle upgrade"
        elif base["positioning_id"] == "3":
            base["positioning_name"] = "Better social drink"
        base["in_line"] = "pending"
        rows.append(base)
        existing.add(key)
        added += 1
    return rows, added, manual


def _needs_enrichment(row: dict[str, str], overwrite_notes: bool) -> bool:
    if not row.get("brand_name"):
        return False
    if not row.get("url"):
        return True
    if overwrite_notes:
        return True
    note_fields = ("use_cases", "adjectives", "visual_design_notes", "product_traits", "why_in_or_out")
    return any(not row.get(f) for f in note_fields)


def _enrich_row(client, row: dict[str, str], research_model: str, model: str) -> tuple[dict, str]:
    brand = row.get("brand_name", "")
    category = row.get("category", "")
    pos_name = row.get("positioning_name", "")
    pos_id = row.get("positioning_id", "")
    prompt = (
        f"Find the official website and concise brand notes for beverage brand '{brand}'. "
        f"Category hint: '{category}'. Positioning hint: {pos_id} '{pos_name}'. "
        "If multiple entities share name, choose beverage brand most relevant to this category and mention ambiguity."
    )
    memo, _ok = web_research(client, model=research_model, instructions=prompt)

    user = f"""Given this web research memo, return structured enrichment.

Brand in our sheet:
- brand_name: {brand}
- category: {category}
- positioning_name: {pos_name}

Rules:
- official_url should be the main brand/product website URL; if uncertain leave empty.
- use_cases/adjectives/visual/product_traits/why_in_or_out should be concise (1 sentence each, adjectives comma list).
- Keep output factual and short.

Memo:
{memo}
"""
    data = chat_json(
        client,
        model=model,
        system="You extract competitor metadata for beverage brand strategy spreadsheets.",
        user=user,
        schema_name="competitor_enrichment",
        schema=ENRICH_SCHEMA,
    )
    return data, memo


def _parse_pos_id(row: dict[str, str]) -> int:
    raw = (row.get("positioning_id") or "").strip()
    if raw in {"1", "2", "3"}:
        return int(raw)
    name = (row.get("positioning_name") or "").strip().lower()
    if "functional" in name:
        return 1
    if "lifestyle" in name or "wellness" in name:
        return 2
    if "social" in name:
        return 3
    return 2


def _pos_name(pos_id: int, fallback: str = "") -> str:
    if pos_id == 1:
        return "Functional protein drink"
    if pos_id == 2:
        return "Lifestyle upgrade"
    if pos_id == 3:
        return "Better social drink"
    return fallback or "Lifestyle upgrade"


def _split_adjectives(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def _sync_competition_json(
    rows: list[dict[str, str]],
    manual_rows: list[dict[str, str]],
    url_map: dict[str, str],
) -> tuple[int, int, set[str]]:
    if not COMP_JSON_PATH.is_file():
        return 0, 0, set()
    payload = json.loads(COMP_JSON_PATH.read_text(encoding="utf-8"))
    updated = 0
    added = 0
    existing = {}
    for brand in payload.get("brands", []):
        key = _normalize_brand(brand.get("brand_name", ""))
        if key:
            existing[key] = brand
        url = url_map.get(key, "")
        if url and not (brand.get("url") or "").strip():
            brand["url"] = url
            updated += 1

    rows_map = {_normalize_brand(r.get("brand_name", "")): r for r in rows}
    manual_names = {_normalize_brand(m.get("brand_name", "")) for m in manual_rows if m.get("brand_name")}
    for key in sorted(manual_names):
        if not key or key in existing:
            continue
        row = rows_map.get(key)
        if not row:
            continue
        pos_id = _parse_pos_id(row)
        obj = {
            "brand_name": row.get("brand_name", ""),
            "category": row.get("category", ""),
            "positioning_id": pos_id,
            "positioning_name": _pos_name(pos_id, row.get("positioning_name", "")),
            "background_color": "",
            "adjectives": _split_adjectives(row.get("adjectives", "")),
            "visual_design_notes": row.get("visual_design_notes", ""),
            "product_traits": row.get("product_traits", ""),
            "why_positioning_fit": row.get("why_in_or_out", ""),
            "url": row.get("url", ""),
        }
        payload.setdefault("brands", []).append(obj)
        existing[key] = obj
        added += 1

    COMP_JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return updated, added, set(existing.keys())


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich competitor URLs and notes")
    parser.add_argument("--limit", type=int, default=100, help="Max rows to enrich per run")
    parser.add_argument(
        "--overwrite-notes",
        action="store_true",
        help="Regenerate notes even if already present",
    )
    parser.add_argument(
        "--overwrite-url",
        action="store_true",
        help="Allow model to replace existing URL values.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="Structured extraction model",
    )
    parser.add_argument(
        "--research-model",
        default="gpt-4o",
        help="Web research model",
    )
    args = parser.parse_args()

    if not CHAR_PATH.is_file():
        raise SystemExit(f"Missing {CHAR_PATH}")

    load_project_env()
    get_openai_api_key()
    client = make_client()

    rows = _read_csv(CHAR_PATH)
    rows, manual_added, manual_rows = _merge_manual(rows)

    work_idx = [
        i for i, r in enumerate(rows) if _needs_enrichment(r, overwrite_notes=args.overwrite_notes)
    ][: max(0, args.limit)]

    log: dict[str, object] = {
        "manualAdded": manual_added,
        "attempted": 0,
        "updated": 0,
        "errors": [],
        "brands": [],
    }

    for i in work_idx:
        row = rows[i]
        brand = row.get("brand_name", "")
        try:
            log["attempted"] = int(log["attempted"]) + 1
            data, _memo = _enrich_row(
                client,
                row=row,
                research_model=args.research_model,
                model=args.model,
            )
            if data.get("official_url") and (args.overwrite_url or not row.get("url")):
                row["url"] = data["official_url"].strip()
            row["category"] = data.get("category", row.get("category", "")).strip() or row.get("category", "")
            for fld in ("use_cases", "adjectives", "visual_design_notes", "product_traits", "why_in_or_out", "lane"):
                new_val = data.get(fld, "").strip()
                if new_val and (args.overwrite_notes or not row.get(fld)):
                    row[fld] = new_val
            rows[i] = row
            log["updated"] = int(log["updated"]) + 1
            log["brands"].append({"brand": brand, "url": row.get("url", "")})
            print(f"Updated: {brand} -> {row.get('url', '')}")
        except Exception as exc:  # noqa: BLE001
            log["errors"].append({"brand": brand, "error": str(exc)})
            print(f"Error: {brand}: {exc}")

    _write_csv(CHAR_PATH, rows)
    url_map = {_normalize_brand(r["brand_name"]): r.get("url", "") for r in rows if r.get("brand_name")}
    json_updated, json_added, competition_names = _sync_competition_json(rows, manual_rows, url_map)
    log["competitionJsonUrlsUpdated"] = json_updated
    log["competitionJsonBrandsAddedFromManual"] = json_added

    if manual_rows:
        remaining = []
        removed = 0
        for m in manual_rows:
            key = _normalize_brand(m.get("brand_name", ""))
            if key and key in competition_names:
                removed += 1
            else:
                remaining.append(m)
        _write_manual_csv(MANUAL_PATH, remaining)
        log["manualRemovedAfterMerge"] = removed

    LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nDone. Wrote {CHAR_PATH.relative_to(ROOT)}")
    print(f"Log: {LOG_PATH.relative_to(ROOT)}")
    if COMP_JSON_PATH.is_file():
        print(f"Backfilled URLs in {COMP_JSON_PATH.relative_to(ROOT)}: {json_updated}")
        print(f"Added manual brands into {COMP_JSON_PATH.relative_to(ROOT)}: {json_added}")


if __name__ == "__main__":
    main()

