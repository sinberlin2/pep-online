# Brand + website workflow (3 positionings)

## Your inputs

| File | Content |
|------|---------|
| `Product positioning options - from Mural - Sheet1.csv` | 3 directions (functional / lifestyle / social) |
| `competition-table.pdf` | Categories × brands; **cell background color** → positioning 1/2/3 |

## Pipeline

```powershell
conda activate pep-online
cd c:\Users\doyle\projects\pep-online

# 1) Parse 3 product directions from Mural CSV
python scripts/parse_positioning_options.py

# 2) Extract brands from PDF → characteristics.csv (needs PDF in brand/research/)
#    Save PDF as: brand/research/competition-table.pdf
pip install pymupdf
python scripts/extract_competition_pdf.py --max-pages 12 --tile-rows 2 --tile-cols 2

# 3) (Optional) Add manual competitors by name
#    Edit brand/research/manual-competitors.csv
#    Then enrich URLs/notes for extracted + manual brands
python scripts/enrich_competitors.py --limit 50

# 4) Merge research for agents
python scripts/merge_brand_research.py

# 5) Build brand packs for all 3 directions (keeps active=2 by default)
python -m agents.brand_all --set-active 2

# Or build one direction only
python -m agents.brand_run --positioning 2

# 6) Site concept uses that brand + peers for web search
python -m agents.concept_run --positioning 2
```

## Positioning IDs

| ID | Slug | Name |
|----|------|------|
| **1** | `functional-protein` | Functional protein drink |
| **2** | `lifestyle` | Lifestyle upgrade (wellness) |
| **3** | `social` | Better social drink |

## Outputs

| Step | Output |
|------|--------|
| Parse | `positioning-options.json` |
| PDF extract | `characteristics.csv` + `competition-extracted.json` |
| URL + notes enrich | `characteristics.csv` + `competitor-enrichment-log.json` |
| brand_run | `directions/<slug>/positioning.json` + `brand-guidelines.md` |
| active selection | `active/positioning.json` + `active/brand-guidelines.md` |
| concept_run | `experiments/website-concepts/...` |

## Switching direction later

```powershell
python -m agents.brand_run --positioning 1
python -m agents.concept_run --positioning 1
```

`brand/research/directions/` keeps separate packs for all three directions.
`brand/research/active/` is just your current selection for website work.

## Competitor selection logic

How fitting brands are chosen for each direction:

1. Primary filter is **positioning fit** (`positioning_id` 1/2/3), not strict product format.
2. `inLineBrands` are the brands that match the active direction's mindset, use case, and design concept.
3. `peerBrandsOtherPositionings` capture brands that are valid competitors but belong more to another direction.
4. Product category (mocktail, kombucha, hydration, etc.) is secondary context, not the main decision rule.

Example: for direction **3 (social)**, a mocktail/non-alcoholic spirit brand can be a good fit because its
social ritual and occasion fit are strong, even if the drink format differs from PEP.

## Shareable exports (HTML, PDF, PNG)

```powershell
npm run brand:export
```

Outputs in `brand/research/exports/`:

- **HTML** — easiest to share (open in browser)
- **PDF** + **PNG per direction** — via Playwright (`playwright install chromium` once)

See `brand/research/exports/README.md`.

## Planned schema extension

See **`docs/BRAND-OUTPUT-SCHEMA-TODO.md`** — add per-brand fields `drinkTypeFit` and `positioningMismatch` in `agents/brand_schemas.py` (partially started in code; regenerate with `brand_run` when ready).
