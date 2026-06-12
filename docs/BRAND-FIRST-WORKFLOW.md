# Brand first, then website

## Why branding comes first

`concept_run` searched for “protein RTD” and surfaced **Lean Body, Ryse, Huel, Vital Proteins** — useful for *layout tricks*, weak as *brand peers*. PEP is **social, light, out-of-home protein**, not gym shakes or meal replacement.

Until positioning is written down, any agent will keep picking the wrong comparables.

## Recommended pipeline

```text
YOUR RESEARCH (brand/research/USER-RESEARCH.md)
        ↓
brand_run (ChatGPT) → positioning.json + brand-guidelines.md
        ↓
concept_run (ChatGPT) → site-concept.json (must follow positioning)
        ↓
You + Cursor implement on dev
        ↓
review_run (later) → harmony check on screenshots
```

## ChatGPT or Claude?

| | ChatGPT (OpenAI) | Claude (Anthropic) |
|--|------------------|---------------------|
| **You today** | API key in `.env` ✓ | Optional later |
| **Brand strategy** | Strong with your research doc as input | Also strong; use for second opinion |
| **Structured JSON** | Already used in `concept_run` | Same pattern possible |
| **Verdict** | **Use ChatGPT first** | Add Claude only if you want a separate “brand critic” pass |

Same two-pass idea as the site: **generator** (positioning) then optional **critic** (“does this feel like Lou & Shannon’s PEP?”).

## What `brand_run` will produce (when built)

- **`brand/research/positioning.json`** — audience, occasions, personality, allowed comparables, anti-references, one-liner
- **`brand/research/brand-guidelines.md`** — voice, visual principles, photography, web do/don’t
- Updates or sidecar to **`brand.json`** only where colors/fonts are confirmed (no hallucinated hex)

## What you do now

1. Export spreadsheet → **`brand/research/characteristics.csv`** (see `characteristics.template.csv`).
2. Export Mural → **`brand/research/mural/board.png`** (and optional `notes.md`).
3. Run **`npm run brand:merge`** → `research-bundle.md`.
4. Implement **`brand_run`** (ChatGPT) → `positioning.json` + `brand-guidelines.md`.
5. Re-run **`concept_run`** only after positioning exists.

## Fixing the last concept run

Keep `experiments/concepts/20260603-.../` as a draft. Do not treat `discovered-references.json` as brand direction — treat it as “what generic search returned.”
