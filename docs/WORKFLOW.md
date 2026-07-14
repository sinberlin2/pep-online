# PEP Online — workflow

The repo has two decoupled parts. This doc covers both; the sections are independent.

- **[Website](#website-site)** — developing and shipping the marketing site.
- **[Brand pipeline](#brand-pipeline-brand)** — generating the brand (strategy → identity → assets).

They meet at one boundary: `npm run site:sync` copies approved brand images into the website's
`site/public/`. The website never reads from `brand/` directly. Repo layout & git policy:
**[docs/ASSETS.md](ASSETS.md)**.

---

# Website (`site/`)

`site/` is the entire deployable website (`index.html`, `for-venues.html`, `css/`, `js/`,
`public/`). Netlify publishes **only** `site/` (`netlify.toml` → `publish = "site"`), and the
page serves images **only** from `site/public/`.

```powershell
npm start        # serve site/ at http://localhost:3000
```

Release flow (dev branch → main → pep-drink.com) and host settings are in
**[DEVELOPMENT.md](../DEVELOPMENT.md)**; DNS/hosting in **[DEPLOY.md](../DEPLOY.md)**.

To publish generated brand assets into the site, list them in `site-assets-map.json` (repo
root) and run `npm run site:sync` (see the hand-off step below).

---

# Brand pipeline (`brand/`)

Generates a complete brand for each of three positioning directions. Code lives in `agents/`
+ `scripts/`; inputs in `brand/inputs/`; outputs in `brand/directions/`. Deeper per-step
detail: **[brand/README.md](../brand/README.md)**.

```
inputs (brand/inputs/)                     outputs (brand/directions/<slug>/)
  product-profile · positioning-options        strategy/   ← brand_run (the strategist)
  competition (CSV/JSON + images)               identity/   ← brand_identity (themes) + brand_images (board)
  external-designs/<slug> (to extract from)     brand-package/ ← brand_package
        │                                              │
        └──────────► agents ──────────────────────────┘──► brandings.json (activeSlug)
                                                             │
                                                    npm run site:sync ──► site/public/
```

## Positioning directions

| ID | Slug | Name |
|----|------|------|
| **1** | `functional-protein` | Functional protein drink |
| **2** | `lifestyle` | Lifestyle upgrade (wellness) |
| **3** | `social` | Better social drink |

Run any step for one direction with `--positioning 1|2|3` (or the slug).

## Inputs prep

Everything below lives under `brand/inputs/`.

| Step | Command | Output (full path) |
|------|---------|--------------------|
| Parse directions | `npm run brand:parse` | `brand/inputs/positioning-options.json` |
| Extract competitors | `npm run brand:extract-pdf` | `brand/inputs/competition/characteristics.csv` + `brand/inputs/competition/competition-extracted.json` |
| Add + enrich competitors | `npm run brand:enrich` | reads `brand/inputs/competition/manual-competitors.csv`, updates `brand/inputs/competition/characteristics.csv` |
| Fetch competitor images | `npm run brand:competitor-images` | `brand/inputs/competition/images/` (+ `images-manifest.json`); pins in `brand/inputs/competition/image-overrides.json` |
| Merge research | `npm run brand:merge` | `brand/inputs/research-bundle.md` (context for the strategist) |

> **Idea (not implemented):** give each competitor **two** positioning tags — one for its
> **communicated value** (today's single `positioning_id`) and one for its **design/visual**
> read — since a brand can sit differently on each. E.g. **Bloom** reads value = 2 (lifestyle)
> but its design could read 3 (social). This would let the identity step borrow design
> inspiration by *design*-positioning independent of value-positioning. Partially anticipated
> today by `design-themes.json`'s per-theme `positioningLeaning` (identity stage) — this idea
> moves it to the competitor **input** level, e.g. a `design_positioning_id` column in
> `brand/inputs/competition/characteristics.csv`.

## Step 1 — Brand strategy = **the strategist** (`agents.brand_run`)

```powershell
npm run brand            # direction 2; or:  python -m agents.brand_run --positioning 3
```
**Reads:** `brand/inputs/product-profile.json`, `brand/inputs/positioning-options.json`,
`brand/inputs/competition/characteristics.csv`, `brand/inputs/research-bundle.md`, and the
prompt `agents/prompts/brand_strategist.md`.
**Writes** to `brand/directions/<slug>/strategy/`:
- `brand/directions/<slug>/strategy/positioning.json` — audience, occasions, voice, and the
  competitor split: `inLineBrands` (direct peers), `positioningFitTypeMismatch` (right vibe,
  different drink type — used as *design* inspiration), `peerBrandsOtherPositionings`,
  `antiReferences`, `brandFitRules`.
- `brand/directions/<slug>/strategy/brand-guidelines.md` — the human-readable strategy.

**Strategy only** — it never names colours or fonts (those are invented later).

## Step 2 — Design themes (`agents.brand_identity`)

```powershell
npm run brand:identity   # or:  python -m agents.brand_identity --positioning 3
```
**Reads:** `brand/directions/<slug>/strategy/positioning.json`, the competitor images via
`brand/inputs/competition/images/images-manifest.json`, and the prompt
`agents/prompts/brand_identity.md` (a vision model).
**Writes one file:** `brand/directions/<slug>/identity/design-themes.json` — 2–4 recurring
competitor looks (base / colour / **finish shiny-vs-matte** / typography / energy), each with
example brands and the positioning it most reads as. **Analysis only** — no palette, fonts,
mockups, or logo (the board is generated from a chosen theme in Step 3).

Optional `--from-design [slug]` also attaches an existing design under
`brand/inputs/external-designs/<slug>/` as context (still themes-only output).

## Step 3 — Brand board (`agents.brand_images`) — the main deliverable

```powershell
npm run brand:images                                              # first theme matching the direction
python -m agents.brand_images --positioning 3 --theme theme-02    # pick a specific theme
python -m agents.brand_images --positioning 3 --quality hd        # higher-quality render
```
Generates the brand board **directly** from `brand/directions/<slug>/strategy/positioning.json`
+ **one** design theme from `brand/directions/<slug>/identity/design-themes.json` (default: the
first theme whose `positioningLeaning` matches the direction; override with `--theme <id>`). The
image model **invents** a palette + type FROM the theme and shows them on the board (wordmark,
slim can, illustration elements, palette swatches, type specimen, badges, label layout). Output:
`brand/directions/<slug>/identity/images/brand-board.png` (**gitignored** — regenerable).

The board is the **end product** — you read colours/type off it by hand (it's an image, so
hex/fonts are approximate). No separate palette/typography/mockup/logo files are produced.
To compare directions, re-run with different `--theme` ids.

## Step 4 — Brand package (`agents.brand_package`)

```powershell
npm run brand:package
```
Pure assembly (no LLM): flattens each direction into
`brand/directions/<slug>/brand-package/design-system.json` + `.../brand-package/brand-package.json`,
and writes the index `brand/brandings.json`. The chosen direction is the `activeSlug` there —
there is no `active/` folder.

## Optional — website concept (`agents.concept_run`)

```powershell
npm run concept          # python -m agents.concept_run --positioning 3
```
Uses the positioning to propose a website concept (with web search). Output under
`experiments/` (e.g. `experiments/website-concepts/`).

## Hand-off — publish to the site (`npm run site:sync`)

Copies the `activeSlug` direction's approved images (from `brand/directions/<activeSlug>/…`)
into `site/public/`, per the map at `site-assets-map.json` (repo root). `activeSlug` is read
from `brand/brandings.json`. This is the only path from `brand/` into the website.

## Share (`npm run brand:export`)

Exports the guidelines as HTML / PDF / PNG packs.

---

**See also:** [brand/README.md](../brand/README.md) (per-step detail),
[docs/ASSETS.md](ASSETS.md) (layout + git policy),
[docs/BRANDING-PIPELINE.md](BRANDING-PIPELINE.md) (diagram + planned extensions).
