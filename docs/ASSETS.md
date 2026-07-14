# Assets & repo layout

The repo has two decoupled areas. **`site/` is the website** (the only thing Netlify
deploys); **`brand/` + `agents/` + `scripts/` are the brand-generation pipeline**. The site
never reads from `brand/` — finished assets are copied across by an explicit sync step.

```
pep-online/
├─ site/                      # WEBSITE — Netlify publishes this (netlify.toml → publish = "site")
│  ├─ index.html  for-venues.html  css/  js/
│  └─ public/                # ONLY images the site serves (curated, committed)
│     ├─ product/  people/  flavours/
├─ brand/                    # BRAND PIPELINE (never deployed)
│  ├─ inputs/                # all pipeline INPUTS
│  │  ├─ external-designs/<slug>/   design sets to extract from (--from-design)
│  │  ├─ competition/               competitor CSV/JSON + image-overrides.json
│  │  │     images/                 fetched packshots (GITIGNORED — rebuildable)
│  │  ├─ product-profile.json  choice.json  positioning-options.json  research-bundle.md
│  │  └─ positioning/  schemas/
│  ├─ directions/<slug>/     # generated OUTPUTS: strategy/ + identity/ (JSON committed)
│  │     identity/images/    generated boards (GITIGNORED — rebuildable)
│  └─ brandings.json         # index; `activeSlug` = the chosen direction (no active/ folder)
├─ agents/  scripts/  paths.py   # pipeline code (paths.py is the single source of paths)
└─ docs/  package.json  netlify.toml
```

## The three buckets

| Bucket | Where | Git |
|--------|-------|-----|
| **Site assets** — what the page serves | `site/public/` | committed (curated, small) |
| **Pipeline inputs** — provided/external designs, competition data, product/positioning | `brand/inputs/` | committed (external-design *images* are large — see LFS below) |
| **Pipeline outputs** — generated strategy/identity | `brand/directions/` | JSON/MD committed; generated **images** gitignored |

## Git policy

**Committed:** all code; strategy/identity JSON+MD; `brand/inputs/competition/*.csv/json` +
`image-overrides.json`; `site/public/`.

**Gitignored (regenerable):**
- `brand/inputs/competition/images/` → rebuild with `npm run brand:competitor-images`
  (recipe = `brand/inputs/competition/image-overrides.json`, committed).
- `brand/directions/*/identity/images/` → rebuild with `npm run brand:images`
  (recipe = each direction's `identity/board-brief.json`, committed).

If these folders were tracked before, untrack them once (keeps the files on disk):
```
git rm -r --cached brand/inputs/competition/images "brand/directions/*/identity/images"
```

## Website ⇄ pipeline hand-off

The website depends only on `site/public/`. To publish generated brand assets into the site,
list them in `site-assets-map.json` and run:
```
npm run site:sync        # copies the activeSlug direction's approved images into site/public/
```
`{active}` in a `from` path expands to `brand/directions/<activeSlug>` (from `brandings.json`).
The default map is empty (see `_example`) — the site currently serves only its own static
images (`site/public/product/pep-can-lockup.*`, `site/public/people/founders-*`).

## Deferred (do when it's worth it)

- **External-design inputs are large** (~60 MB of PNGs). The proper long-term home is
  **Git LFS** or an external store, so they don't bloat the code pack:
  ```
  git lfs install
  git lfs track "brand/inputs/external-designs/**/*.png" "brand/inputs/external-designs/**/*.webp"
  git lfs migrate import --include="brand/inputs/external-designs/**"
  ```
  Netlify supports LFS.
- **Reclaim existing history** (the `.git` pack already carries old binary churn) with
  `git filter-repo` / BFG — disruptive (rewrites history); only after LFS.
