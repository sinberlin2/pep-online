# Brand output schema — planned extension

**Reminder:** Extend `agents/brand_schemas.py` and regenerate direction packs so every competitor entry includes explicit fit labels.

## Target fields (per brand object)

| Field | Meaning |
|-------|---------|
| `drinkTypeFit` | How well drink category/type matches active direction (e.g. strong / partial / weak) |
| `positioningMismatch` | Why occasion/branding does **not** match active direction (when drink type may still fit) |
| `typeMismatch` | Legacy alias kept in `positioningFitTypeMismatch` items — consider renaming to `drinkTypeMismatch` only in a future schema version |

## Lists to keep

- `inLineBrands` — strict fit: **positioning + drink type**
- `positioningFitTypeMismatch` — branding/occasion fit, drink type off
- `peerBrandsOtherPositionings` — mainly another Mural column (`positioning_id`)

## Also reflect in exports

- `brand-guidelines.md` — human-readable split (done manually in prose today)
- `positioning.json` — machine-readable (partially populated after next `brand_run`)

## Next implementation step

1. Update `agents/prompts/brand_strategist.md` to require `drinkTypeFit` + `positioningMismatch` on every brand entry.
2. Bump `positioning.version` in schema when fields are stable.
3. Re-run: `python -m agents.brand_all --set-active 2` (or per direction).

## PDF export

Brand guideline markups PDF: `brand/research/exports/PEP-brand-guidelines.pdf`  
Regenerate after guideline edits: `python scripts/generate_brand_guidelines_pdf.py`
