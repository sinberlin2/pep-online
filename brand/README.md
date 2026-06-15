# Branding module

Outputs only. All inputs are under `company/`.

---

## Folder layout

```
brand/
  directions/
    <slug>/
      strategy/          ← brand_run output (positioning, guidelines)
        positioning.json
        brand-guidelines.md
        meta.json
      identity/          ← brand_identity output (colours, type, mockups)
        color-palette.json
        typography.json
        mockup-briefs.json
        identity-guidelines.md
        identity-meta.json
        preview.html       visual mockup of this direction
        image-prompts.md   Midjourney / DALL-E prompts for this direction
      brand-package/     ← brand_package output (assembled tokens)
        design-system.json
        brand-package.json
  provided/              ← existing PEP design assets (not generated)
    pep-original/
      identity/          original logo, typography reference
      marketing/         flyers, design reference, garnishes
      product/           can shots, glass shots
      extracted/         Flow B extraction output
        design-system.json
        brand-package.json
        source.md
      meta.json
  active/                mirror of the currently selected direction
    strategy/            positioning.json, brand-guidelines.md, meta.json
    identity/            color-palette.json, typography.json, mockup-briefs.json, identity-guidelines.md
  brandings.json         index of all brand packages
  preview.html           visual HTML preview of all three directions
  image-generation-prompts.md
```

---

## How to create a branding (Flow A — invent from strategy)

This is the standard flow. It runs three agents in sequence and has no dependency on any existing PEP design.

### Prerequisites

```
company/competition/characteristics.csv   # competitor data
company/competition/competition-extracted.json
company/positioning-options.json
company/product-profile.json
```

To build or refresh these, run the data prep scripts first (see `company/README.md`).

---

### Step 1 — Brand strategy (`brand_run`)

**What it does:** LLM agent reads the product profile, positioning options, and competitor table and writes a complete brand strategy for one direction.

**Input files:**
- `company/product-profile.json` — product facts (name, tagline, protein, calories)
- `company/positioning-options.json` — the three direction definitions from Mural
- `company/competition/characteristics.csv` — enriched competitor table
- `agents/prompts/brand_strategist.md` — system prompt

**Output files (written to `brand/directions/<slug>/strategy/`):**
- `positioning.json` — full brand strategy: audience, occasions, visual direction, competitor tiers
- `brand-guidelines.md` — human-readable strategy guide
- `meta.json` — run metadata

**Commands:**
```bash
npm run brand            # direction 2 (lifestyle) only
npm run brand:all        # all three directions
python -m agents.brand_run --positioning 1   # functional-protein
python -m agents.brand_run --positioning 2   # lifestyle
python -m agents.brand_run --positioning 3   # social
```

---

### Step 2 — Visual identity (`brand_identity`)

**What it does:** LLM agent reads the positioning and competitor data and **invents** a complete visual identity — colour palette, typography, mockup briefs, and a human-readable guidelines doc. It does **not** reference the existing PEP design in this mode.

**Input files:**
- `brand/directions/<slug>/strategy/positioning.json` — output of Step 1
- `agents/prompts/brand_identity.md` — system prompt (includes competitor anchoring table and existing-PEP colours to avoid)

**Output files (written to `brand/directions/<slug>/identity/`):**
- `color-palette.json` — primary, secondary, text, and background swatches with hex + role + rationale
- `typography.json` — display, body, script, badge fonts with pairing rationale
- `mockup-briefs.json` — 6 detailed briefs (can label, social post, venue card, hero, lifestyle, story ad), each with layout, colour usage, typography usage, and an image generation prompt
- `identity-guidelines.md` — human-readable identity guide for Lou & Shannon
- `identity-meta.json` — run metadata (model, provider, mode, timestamp)

If the active direction is set, all identity files are also mirrored to `brand/active/`.

**Commands:**
```bash
npm run brand:identity                          # active direction, OpenAI
npm run brand:identity:claude                   # active direction, Anthropic
python -m agents.brand_identity --positioning 1
python -m agents.brand_identity --positioning 2
python -m agents.brand_identity --positioning 3
python -m agents.brand_identity --from-design   # extraction mode (uses existing PEP design images)
```

---

### Step 3 — Brand package (`brand:package`)

**What it does:** Pure file assembly — no LLM. Reads all direction outputs and assembles them into a single brand pack index. Also builds `design-system.json` for each direction.

**Input files:**
- `brand/directions/*/strategy/positioning.json`
- `brand/directions/*/identity/color-palette.json`
- `brand/directions/*/identity/typography.json`
- `brand/directions/*/identity/mockup-briefs.json`

**Output files:**
- `brand/brandings.json` — index of all direction packs
- `brand/directions/<slug>/brand-package/design-system.json` — flattened design tokens per direction
- `brand/directions/<slug>/brand-package/brand-package.json` — assembled manifest per direction

**Command:**
```bash
npm run brand:package
```

---

## Invention mode vs extraction mode

| | Invention mode (default) | Extraction mode (`--from-design`) |
|---|---|---|
| **Trigger** | `npm run brand:identity` | `python -m agents.brand_identity --from-design` |
| **Colour source** | Invented from competitor anchoring table | Extracted from existing PEP design images |
| **Font source** | Invented — existing PEP fonts (Didot, Montserrat, Brittany Signature) are explicitly suppressed | Extracted from `provided/pep-original/extracted/design-system.json` |
| **Logo mark** | New mark per direction (no botanical leaf) | Based on observed existing logo |
| **Use when** | Exploring new brand directions | Systematising the current PEP design |

---

## Adding a competitor

1. Add a row to `company/competition/manual-competitors.csv`:
   ```
   brand_name,category,positioning_id
   Brand Name,category,2
   ```
   `positioning_id`: `1` = Functional, `2` = Lifestyle, `3` = Social

2. Run enrichment (requires OpenAI API key):
   ```bash
   npm run brand:enrich
   ```
   This web-researches the brand, fills visual notes, and merges it into `competition-extracted.json`.

3. Re-run `brand_identity` for the relevant direction — the new competitor will appear in the tier list.

---

## Generating real mockup images

`identity/mockup-briefs.json` contains `imagePrompt` fields for each surface. Pre-formatted prompts ready to paste into Midjourney or DALL-E 3 are in each direction's `identity/image-prompts.md`.
