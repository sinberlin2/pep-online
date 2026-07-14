"""
Extract brands from competition table PDF (colored cells → positioning 1/2/3).

Uses GPT-4o vision on rendered PDF pages.

Place PDF at:
  brand/inputs/competition/sources/drink-competition.pdf

Usage:
  python scripts/extract_competition_pdf.py
  python scripts/extract_competition_pdf.py --pdf path/to/file.pdf
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paths  # noqa: E402

OUT_JSON = paths.COMPETITION_EXTRACTED
OUT_CSV = paths.CHARACTERISTICS_CSV
OPTIONS_JSON = paths.POSITIONING_OPTIONS

EXTRACT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "legendNotes": {"type": "string"},
        "brands": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "brand_name": {"type": "string"},
                    "category": {"type": "string"},
                    "positioning_id": {"type": "integer"},
                    "positioning_name": {"type": "string"},
                    "background_color": {"type": "string"},
                    "adjectives": {"type": "array", "items": {"type": "string"}},
                    "visual_design_notes": {"type": "string"},
                    "product_traits": {"type": "string"},
                    "why_positioning_fit": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": [
                    "brand_name",
                    "category",
                    "positioning_id",
                    "positioning_name",
                    "background_color",
                    "adjectives",
                    "visual_design_notes",
                    "product_traits",
                    "why_positioning_fit",
                    "url",
                ],
            },
        },
    },
    "required": ["legendNotes", "brands"],
}

CSV_FIELDS = [
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


def _find_pdf(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise SystemExit(f"PDF not found: {p}")
        return p
    for pattern in ("drink-competition.pdf", "competition*.pdf", "*.pdf"):
        hits = list(paths.COMPETITION_SOURCES.glob(pattern)) if paths.COMPETITION_SOURCES.is_dir() else []
        if not hits:
            hits = list(paths.COMPETITION.glob(pattern))
        if hits:
            return sorted(hits, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    raise SystemExit(
        f"Put competition PDF in {paths.COMPETITION}/sources/drink-competition.pdf"
    )


def _render_pdf_pages(
    pdf_path: Path,
    max_pages: int = 8,
    *,
    tile_rows: int = 1,
    tile_cols: int = 1,
) -> list[dict[str, object]]:
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise SystemExit(
            "Install pymupdf: pip install pymupdf\n" + str(exc)
        ) from exc

    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    scale = 2.0
    if size_mb > 15:
        scale = 1.5
        max_pages = min(max_pages, 12)
        print(
            f"Large PDF ({size_mb:.0f} MB) — using up to {max_pages} page(s) at {scale}x scale."
        )

    doc = fitz.open(pdf_path)
    images: list[dict[str, object]] = []
    try:
        page_count = min(len(doc), max_pages)
        for i in range(page_count):
            page = doc[i]
            rect = page.rect
            for r in range(tile_rows):
                for c in range(tile_cols):
                    clip = fitz.Rect(
                        rect.x0 + (rect.width * c / tile_cols),
                        rect.y0 + (rect.height * r / tile_rows),
                        rect.x0 + (rect.width * (c + 1) / tile_cols),
                        rect.y0 + (rect.height * (r + 1) / tile_rows),
                    )
                    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip)
                    label = f"page-{i+1}-tile-r{r+1}c{c+1}"
                    images.append({"label": label, "png": pix.tobytes("png")})
            print(f"  Rendered page {i + 1}/{page_count} into {tile_rows * tile_cols} tile(s)")
    finally:
        doc.close()
    return images


def _load_positioning_context() -> str:
    if OPTIONS_JSON.is_file():
        return OPTIONS_JSON.read_text(encoding="utf-8")
    return (
        "Positioning 1 = Functional protein drink. "
        "Positioning 2 = Lifestyle upgrade (wellness). "
        "Positioning 3 = Better social drink."
    )


def _vision_extract_batch(
    *,
    client,
    model: str,
    pdf_path: Path,
    positioning_ctx: str,
    images: list[dict[str, object]],
    batch_idx: int,
    batch_count: int,
) -> dict:
    sys.path.insert(0, str(ROOT))
    user_text = f"""Extract every brand from this competition table PDF.

## Three PEP product directions (background color on brand cell indicates match)
```json
{positioning_ctx}
```

## Rules
- Read the table: drink **categories** (rows or sections) and **brand names** in cells.
- **positioning_id** must be 1, 2, or 3 based on the **background color** of that brand's cell.
- Describe the background color in `background_color` (e.g. "light green", "pastel peach", "bright coral").
- Return only brands visible in these image tiles.
- `url`: leave empty string if unknown; do not guess fake URLs.
- `adjectives` and `visual_design_notes`: infer from category + typical brand look if not visible.
- `why_positioning_fit`: one sentence linking brand to that positioning.
- `legendNotes`: explain how you mapped colors → 1/2/3.

PDF filename: {pdf_path.name}
Batch: {batch_idx}/{batch_count}
"""

    content: list[dict] = [{"type": "text", "text": user_text}]
    for tile in images:
        png = tile["png"]
        label = tile["label"]
        b64 = base64.standard_b64encode(png).decode("ascii")
        content.append({"type": "text", "text": f"Tile: {label}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
            }
        )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You extract structured data from brand competition tables. Be thorough.",
            },
            {"role": "user", "content": content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "competition_extract",
                "strict": True,
                "schema": EXTRACT_SCHEMA,
            },
        },
    )
    raw = completion.choices[0].message.content
    if not raw:
        raise RuntimeError("Empty vision response")
    return json.loads(raw)


def _vision_extract(pdf_path: Path, images: list[dict[str, object]], batch_size: int = 6) -> dict:
    sys.path.insert(0, str(ROOT))
    from agents.llm.env import get_openai_api_key, load_project_env
    from agents.llm.openai_client import make_client

    load_project_env()
    get_openai_api_key()
    client = make_client()
    model = os.environ.get("REVIEW_AGENT_MODEL", "gpt-4o")
    positioning_ctx = _load_positioning_context()

    all_brands: dict[str, dict] = {}
    legend_notes: list[str] = []
    batch_count = max(1, math.ceil(len(images) / batch_size))
    for i in range(0, len(images), batch_size):
        batch_idx = (i // batch_size) + 1
        batch = images[i : i + batch_size]
        print(f"  Vision batch {batch_idx}/{batch_count} ({len(batch)} tile(s))...")
        result = _vision_extract_batch(
            client=client,
            model=model,
            pdf_path=pdf_path,
            positioning_ctx=positioning_ctx,
            images=batch,
            batch_idx=batch_idx,
            batch_count=batch_count,
        )
        notes = result.get("legendNotes", "").strip()
        if notes:
            legend_notes.append(notes)
        for b in result.get("brands", []):
            key = f"{(b.get('brand_name') or '').strip().lower()}|{(b.get('category') or '').strip().lower()}"
            if not key.strip("|"):
                continue
            all_brands[key] = b

    return {
        "legendNotes": " | ".join(dict.fromkeys(legend_notes)) if legend_notes else "",
        "brands": sorted(
            all_brands.values(),
            key=lambda x: (x.get("positioning_id", 0), (x.get("brand_name") or "").lower()),
        ),
    }


def _to_csv_rows(data: dict) -> list[dict[str, str]]:
    rows = []
    for b in data.get("brands", []):
        adj = b.get("adjectives") or []
        pid = str(b.get("positioning_id", ""))
        rows.append(
            {
                "brand_name": b.get("brand_name", ""),
                "url": b.get("url", ""),
                "category": b.get("category", ""),
                "positioning_id": pid,
                "positioning_name": b.get("positioning_name", ""),
                "in_line": "pending",
                "use_cases": "",
                "adjectives": ", ".join(adj) if isinstance(adj, list) else str(adj),
                "visual_design_notes": b.get("visual_design_notes", "")
                + (
                    f" | cell color: {b.get('background_color', '')}"
                    if b.get("background_color")
                    else ""
                ),
                "product_traits": b.get("product_traits", ""),
                "why_in_or_out": b.get("why_positioning_fit", ""),
                "lane": b.get("category", ""),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", help="Path to competition PDF")
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--tile-rows", type=int, default=1)
    parser.add_argument("--tile-cols", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=6)
    args = parser.parse_args()

    pdf_path = _find_pdf(args.pdf)
    print(f"Rendering {pdf_path.name}...")
    tile_rows = max(1, args.tile_rows)
    tile_cols = max(1, args.tile_cols)
    if tile_rows == 1 and tile_cols == 1 and pdf_path.stat().st_size > 15 * 1024 * 1024:
        # Better OCR coverage for large single-page tables
        tile_rows, tile_cols = 2, 2
    images = _render_pdf_pages(
        pdf_path,
        max_pages=max(1, args.max_pages),
        tile_rows=tile_rows,
        tile_cols=tile_cols,
    )
    print(f"Extracting with vision ({len(images)} rendered tile(s))...")
    data = _vision_extract(pdf_path, images, batch_size=max(1, args.batch_size))

    OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = _to_csv_rows(data)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_JSON.relative_to(ROOT)} ({len(data.get('brands', []))} brands)")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print("Next: python scripts/merge_brand_research.py")
    print("       python -m agents.brand_run --positioning 2")


if __name__ == "__main__":
    main()
