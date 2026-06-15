# Website concepts

Each subfolder here is one run of `concept_run` and contains:

| File | What it is |
|------|-----------|
| `site-concept.json` | Structured spec: page sections, design tokens, typography, anchored references |
| `concept.md` | Human-readable brief for Lou & Shannon to hand to a developer |
| `discovered-references.json` | Sites found by web search (or marked as skipped) |
| `research-memo.txt` | Raw web search output (only present when search was on) |
| `meta.json` | Run metadata: model, brief, positioning source, timestamp |

## How to read a concept

Start with `concept.md`. It describes the full site vision in plain English.
Then open `site-concept.json` if you need the structured section specs to implement.

## Naming

Folders are stamped `YYYYMMDD-HHMMSS-{concept-id}` so runs sort chronologically.

## Running

```powershell
npm run concept
# or with a custom brief:
python -m agents.concept_run --brief "Your brief here" --positioning lifestyle
```

Requires `brand/active/positioning.json` and `brand/active/brand-guidelines.md` to exist (run `brand_run` first).
