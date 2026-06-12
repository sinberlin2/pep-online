# PEP site design agents

## Setup (once)

```powershell
cd c:\Users\doyle\projects\pep-online
conda activate pep-online
pip install -r requirements-agents.txt
# .env with OPENAI_API_KEY only (never commit .env)
```

## Full workflow (3 positionings + PDF table)

See `brand/research/WORKFLOW.md`.

```powershell
npm run brand:parse
# Add brand/research/competition-table.pdf then:
npm run brand:extract-pdf -- --max-pages 12 --tile-rows 2 --tile-cols 2
npm run brand:merge
npm run brand:all

# Build website concept for selected direction
python -m agents.concept_run --positioning 2
```

| ID | Direction | CLI |
|----|-----------|-----|
| 1 | Functional protein | `--positioning 1` |
| 2 | Lifestyle / wellness | `--positioning 2` or `lifestyle` |
| 3 | Better social drink | `--positioning 3` |

All direction packs:
- `brand/research/directions/functional-protein/`
- `brand/research/directions/lifestyle/`
- `brand/research/directions/social/`

Current active selection:
- `brand/research/active/positioning.json`

## Pass 1 — Site concept

```powershell
python -m agents.concept_run --brief "..." --positioning 2
```

Outputs go to `experiments/website-concepts/` to keep website work separate from branding files.

Shareable brand exports: `npm run brand:export` → HTML, PDF, and PNGs in `brand/research/exports/`

**Schema reminder:** planned per-brand fields `drinkTypeFit` + `positioningMismatch` — see `docs/BRAND-OUTPUT-SCHEMA-TODO.md`.

## Pass 2 — Design critic

`review_run` — not built yet.
