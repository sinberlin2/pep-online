# Brand output schema — status

**Mostly shipped.** The per-brand fit fields below are live in `agents/brand_schemas.py` and
populated by `brand_run` (see any `brand/directions/<slug>/strategy/positioning.json`).

## Per-brand fit fields (shipped)

| Field | Where | Meaning |
|-------|-------|---------|
| `drinkTypeFit` | all three brand lists | how well the drink category/type matches the direction |
| `positioningMismatch` | `positioningFitTypeMismatch`, `peerBrandsOtherPositionings` | why occasion/branding doesn't match the direction |
| `typeMismatch` | `positioningFitTypeMismatch` | drink-type mismatch (kept as-is; the brands are still used as *design* inspiration) |

## Brand lists (shipped)

- `inLineBrands` — strict fit: **positioning + drink type**
- `positioningFitTypeMismatch` — branding/occasion fit, drink type off (design-inspiration tier)
- `peerBrandsOtherPositionings` — mainly another positioning column

## Open (optional)

- Consider renaming `typeMismatch` → `drinkTypeMismatch` in a future `positioning.version` bump.
- Shareable guideline exports (`npm run brand:export`) → HTML / PDF / PNG.
