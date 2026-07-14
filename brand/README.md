# Branding module

Outputs only. All inputs are under `brand/inputs/`.

---

## Folder layout

```
brand/
  inputs/                ← all pipeline INPUTS (see docs/ASSETS.md)
    external-designs/     existing/provided design sets to extract from (--from-design)
      pep-original/
        identity/         original logo, typography reference
        marketing/        flyers, design reference, garnishes
        product/          can shots, glass shots
        extracted/        Flow B extraction output (design-system.json, source.md)
        extraction-images.json   curated refs fed to the vision model
    competition/          competitor CSV/JSON + image-overrides.json (images/ gitignored)
    product-profile.json  choice.json  positioning-options.json  research-bundle.md
    positioning/  schemas/
  directions/            ← generated OUTPUTS per direction
    <slug>/
      strategy/           brand_run output — positioning.json, brand-guidelines.md, meta.json
      identity/           brand_identity output — color-palette.json, typography.json,
                          design-themes.json, mockup-briefs.json, logo-brief.json,
                          board-brief.json, identity-guidelines.md  (images/ gitignored)
      brand-package/      brand_package output — design-system.json, brand-package.json
  brandings.json         index of all directions; `activeSlug` = the chosen one (no active/ folder)
```

The website is separate under `site/` and reads only from `site/public/`; publish approved
assets to it with `npm run site:sync`. See `docs/ASSETS.md`.

---

## How to create a branding (Flow A — invent from strategy)

This is the standard flow. It runs three agents in sequence and has no dependency on any existing PEP design.

### Prerequisites

```
brand/inputs/competition/characteristics.csv   # competitor data
brand/inputs/competition/competition-extracted.json
brand/inputs/positioning-options.json
brand/inputs/product-profile.json
```

To build or refresh these, run the data prep scripts first (see `brand/inputs/README.md`).

---

### Step 1 — Brand strategy (`brand_run`)

**What it does:** LLM agent reads the product profile, positioning options, and competitor table and writes a complete brand strategy for one direction.

**Input files:**
- `brand/inputs/product-profile.json` — product facts (name, tagline, protein, calories)
- `brand/inputs/positioning-options.json` — the three direction definitions from Mural
- `brand/inputs/competition/characteristics.csv` — enriched competitor table
- `agents/prompts/brand_strategist.md` — system prompt

> **Potential change (TODO):** each direction in `positioning-options.json` carries a
> `Design concept` dimension that the strategist currently copies straight into
> `visual.designConcept` (see the "Use active column **Design concept**" rule in
> `brand_strategist.md`). Consider **removing `Design concept` from `positioning-options.json`**
> so the strategist *generates* the design concept from the positioning + competitors instead
> of echoing the Mural input. Would need dropping the copy rule in `brand_strategist.md` too.

> **TODO — PEP's use cases aren't well defined:** the research bundle lists an explicit
> `use_cases` field per *competitor* (from `characteristics.csv`), but PEP's own use
> cases/occasions have no equivalent field. They're only *implicit* in
> `positioning-options.json`, spread across `Typical moments`, `Consumption context`, and
> `Core problem`, and the bundle dumps that as raw JSON. Consider adding an explicit
> per-direction **use-cases/occasions** field to `positioning-options.json` (or have the
> strategist synthesise it into `positioning.json`) so occasions are stated, not inferred.

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

### Step 2 — Design themes (`brand_identity`)

**What it does:** a vision LLM analyses the competitor images and extracts the recurring **design themes** — the handful of visual looks that repeat across brands. That is its *only* output; it no longer invents a palette, fonts, mockups, or a logo (the brand board in Step 3 does the visual, directly from a chosen theme).

**Prerequisite (recommended):** run `npm run brand:competitor-images` once to fetch a
representative image per competitor into `brand/inputs/competition/images/`. The identity agent
reads these to extract `observedDesignThemes` — the recurring visual looks within each
positioning (e.g. social "white base + shiny accent" vs "solid colour + shiny"; wellness
"white/pastel + matte"). Without images it still runs, extracting themes from the text notes.
Weak/missing auto-fetches: drop a `<brand-slug>.png` into that folder by hand — it won't be overwritten.

**Input files:**
- `brand/directions/<slug>/strategy/positioning.json` — output of Step 1
- `brand/inputs/competition/images/` + `images-manifest.json` — competitor images for theme analysis
- `agents/prompts/brand_identity.md` — system prompt (competitor design-theme extraction)

**Output files (written to `brand/directions/<slug>/identity/`):**
- `design-themes.json` — 2–4 recurring competitor design themes (base/colour/finish/typography/energy axes, example brands, `positioningLeaning`, relevance to this direction)
- `identity-meta.json` — run metadata (model, provider, mode, timestamp)

The chosen direction is tracked by `activeSlug` in `brand/brandings.json` (no `active/` folder).

**Commands:**
```bash
npm run brand:identity                          # active direction, OpenAI
npm run brand:identity:claude                   # active direction, Anthropic
python -m agents.brand_identity --positioning 1
python -m agents.brand_identity --positioning 2
python -m agents.brand_identity --positioning 3
python -m agents.brand_identity --from-design   # extraction mode (uses existing PEP design images)
```

**Extraction mode** (`--from-design [SLUG]`) can extract from **any** existing design set
under `brand/inputs/external-designs/<slug>/`, not just `pep-original` (bare `--from-design` uses
`pep-original`). Each provided design folder carries its own `extraction-images.json` — a
JSON array of image paths relative to that folder — listing the reference images fed to the
model. Edit that file to change which assets are used (no code change); override the manifest
location with `--design-manifest`. To extract from a new design, create
`brand/inputs/external-designs/<slug>/` with the images + an `extraction-images.json`, then run
`python -m agents.brand_identity --from-design <slug>`.

---

### Step 3 — Brand board (`brand:images`)

**What it does:** generates the editorial **brand board** (`brand-board.png`) — the main visual deliverable — directly from `positioning.json` + **one** design theme. The image model invents a palette + type FROM the theme and renders them onto the board; you read colours/typography off it by hand. No palette/typography/mockup JSON is produced.

**Command:**
```bash
npm run brand:images                                            # first theme matching the direction
python -m agents.brand_images --positioning 3 --theme theme-02  # pick a specific theme
```

**Output:** `brand/directions/<slug>/identity/images/brand-board.png` (gitignored — regenerable).

---

### Step 4 — Brand package (`brand:package`)

**What it does:** Pure file assembly — no LLM. Assembles the direction outputs into a single brand pack index.

**Input files:**
- `brand/directions/*/strategy/positioning.json`

**Output files:**
- `brand/brandings.json` — index of all direction packs
- `brand/directions/<slug>/brand-package/design-system.json` — flattened design tokens per direction
- `brand/directions/<slug>/brand-package/brand-package.json` — assembled manifest per direction

**Command:**
```bash
npm run brand:package
```

---

## Invention vs extraction mode

`brand_identity` always outputs **design themes only** — the mode just changes which images it sees:

- **Invention (default):** analyses the competitor images only.
- **Extraction (`--from-design [slug]`):** also attaches an existing design set under
  `brand/inputs/external-designs/<slug>/` (default `pep-original`) as extra context — still
  themes-only output. Use it when you want the themes to account for an existing design too.

---

## Adding a competitor

1. Add a row to `brand/inputs/competition/manual-competitors.csv`:
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

3. Fetch its image so it feeds the design-theme analysis:
   ```bash
   npm run brand:competitor-images
   ```
   (Only new brands are fetched. If the auto `og:image` is weak, drop a
   `brand/inputs/competition/images/<brand-slug>.png` in by hand — it won't be overwritten.)

4. Re-run `brand_identity` for the relevant direction — the new competitor will appear in the tier list and in `observedDesignThemes`, then re-run `brand:images` to refresh the board.
