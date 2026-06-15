# Company

Everything about **what PEP is** and **what we know before branding** — not the brand outputs themselves.

| Path | What |
|------|------|
| `product-profile.json` | Generic facts: name, tagline, protein/calories |
| `choice.json` | **Your commit:** which positioning to brand (drink type optional later) |
| `positioning-options.json` | 3 directions (functional / lifestyle / social) — parsed from CSV |
| `positioning/` | Source CSV + optional board PNG/notes |
| `competition/` | Competitor table, enrichment, extracted JSON |
| `research-bundle.md` | Merged input for `brand_run` (auto-generated) |
| `schemas/` | `positioning.schema.json` etc. |
| `assets/` | Company photos (e.g. founders) — not design assets |

## Pipeline order

```text
1. product-profile.json     — what the product is
2. positioning-options.json — 3 positioning directions (from positioning CSV)
3. competition/             — competitors sorted by positioning + drink type
4. choice.json              — pick positioning (drink type TBD)
5. brand_run                — → brand package under brand/
```

## Scripts

```bash
python scripts/parse_positioning_options.py
python scripts/extract_competition_pdf.py
python scripts/enrich_competitors.py
python scripts/merge_brand_research.py
python -m agents.brand_run --positioning lifestyle   # or use choice.json default
```

See `IMPORT.md` for how to refresh the source CSV and competition PDF.
