# PEP brand research (source of truth)

**Do this before** (or instead of) another open-ended `concept_run`. Website layout agents need a tight **brand positioning** doc here; otherwise web search drifts toward gym protein and meal-replacement brands.

## Files

| File | Who fills it | Purpose |
|------|----------------|---------|
| **`characteristics.csv`** | Your spreadsheet export | Brands, adjectives, in_line yes/no, visual notes |
| **`manual-competitors.csv`** | You (names only is fine) | Add missing competitors manually; script enriches URL + notes |
| **`mural/board.png`** (+ optional notes) | Mural export | Visual map of use cases & brand fit |
| **`research-bundle.md`** | `merge_brand_research.py` | Single file agents read |
| **`USER-RESEARCH.md`** | You (optional) | Extra notes if not everything is in CSV/Mural |
| **`positioning.json`** | `brand_run` agent | Structured brand brain for all agents |
| **`brand-guidelines.md`** | `brand_run` agent | Voice, visuals, do/don’t — readable brief |

**Start here:** [`IMPORT.md`](IMPORT.md) — how to export Mural + spreadsheet.

`brand.json` stays the technical contract (hex colors, font names). **Positioning** decides *who PEP is* and *who to compare to*.

## Order of work

```text
1. Export spreadsheet → characteristics.csv
2. Export Mural → mural/board.png (+ optional notes.md)
3. (Optional) add missing names → manual-competitors.csv
4. python scripts/enrich_competitors.py   ← fills official URLs + notes
   (uses `manual-competitors.csv`; keeps existing URLs unless `--overwrite-url`)
5. python scripts/merge_brand_research.py
6. npm run brand:all    ← positioning.json + guidelines for 1/2/3
7. npm run concept      ← website concept for selected positioning
```

## ChatGPT vs Claude for branding

| Task | Recommendation |
|------|----------------|
| **Primary — positioning framework** | **ChatGPT** (you already have the API; use gpt-4.1) |
| **Optional — “does this sound like us?” critique** | **Claude** later, if you add `ANTHROPIC_API_KEY` |
| **Web search for comparables** | ChatGPT (gpt-4o) **only after** your filters in USER-RESEARCH |

You do **not** need both on day one. One strong positioning doc beats switching models.

## What “in line” means for PEP (default filters)

Use these to reject bad comparables (e.g. Lean Body, Ryse):

- **Occasion:** café, bar, terrace, brunch, social — not gym-first
- **Feel:** light, refreshing, premium — not meal replacement or energy shot
- **Message:** protein as *bonus*, not bodybuilding identity
- **Visual:** warm greens/creams, flavour joy — not neon seltzer or black/yellow gym

Revized = layout reference. **Positioning peers** might be closer to premium soft drinks, lifestyle functional beverages, or “social wellness” — not collagen press releases.
