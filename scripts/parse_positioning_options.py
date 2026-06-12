"""
Parse Mural positioning spreadsheet → positioning-options.json

Usage:
  python scripts/parse_positioning_options.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "brand" / "research"
OUT = RESEARCH / "positioning-options.json"

# Column order in your Mural export
OPTIONS = [
    {
        "id": 1,
        "slug": "functional-protein",
        "name": "Functional protein drink",
        "aliases": ["functional", "protein", "1"],
    },
    {
        "id": 2,
        "slug": "lifestyle",
        "name": "Lifestyle upgrade",
        "aliases": ["wellness", "lifestyle", "wellness/lifestyle", "2"],
    },
    {
        "id": 3,
        "slug": "social",
        "name": "Better social drink",
        "aliases": ["social", "3"],
    },
]


def _find_csv() -> Path:
    candidates = list(RESEARCH.glob("*positioning*.csv")) + list(RESEARCH.glob("*Positioning*.csv"))
    if not candidates:
        raise SystemExit(
            f"No positioning CSV in {RESEARCH}. "
            "Add your Mural export (e.g. 'Product positioning options - from Mural - Sheet1.csv')."
        )
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def main() -> None:
    csv_path = _find_csv()
    rows: list[list[str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if any(cell.strip() for cell in row):
                rows.append(row)

    if len(rows) < 2:
        raise SystemExit(f"CSV too short: {csv_path}")

    header = [c.strip() for c in rows[0]]
    if len(header) < 4:
        raise SystemExit(f"Expected Dimension + 3 positioning columns in {csv_path}")

    options_out = []
    for opt, col_idx in zip(OPTIONS, range(1, 4)):
        dimensions: dict[str, str] = {}
        for row in rows[1:]:
            if len(row) <= col_idx:
                continue
            key = (row[0] or "").strip()
            val = (row[col_idx] or "").strip()
            if key:
                dimensions[key] = val
        options_out.append({**opt, "dimensions": dimensions})

    payload = {
        "version": 1,
        "sourceCsv": csv_path.relative_to(ROOT).as_posix(),
        "options": options_out,
        "colorLegendHint": (
            "In the competition PDF, brand cell background color maps to positioning: "
            "match colors to the three columns above (functional / lifestyle pastel / social vibrant)."
        ),
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} from {csv_path.name}")
    for o in options_out:
        print(f"  [{o['id']}] {o['name']} ({o['slug']})")


if __name__ == "__main__":
    main()
