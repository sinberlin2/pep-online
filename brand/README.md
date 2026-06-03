# PEP brand assets

## Typography & colours

- **`brand.json`** — fonts and colours for site + future tools
- **`identity/typography.md`** — flyer font table (Didot, Bebas Neue, Brittany Signature, Montserrat)
- **`identity/pep-fonts-reference.png`** — source screenshot

Each category uses the same layout:

```
brand/{identity,marketing,product}/
  originals/     ← source PNGs (do not overwrite)
  bg_removed/    ← rembg outputs (*-background-removed.png)
```

## Model workflow (rembg)

```powershell
conda activate pep-online
cd c:\Users\doyle\projects\pep-online
python scripts/bg_remove.py
```

Or: `npm run bg:remove` (uses `python` on PATH — activate conda first).

### What gets processed

| Category | Originals | Background removal |
|----------|-----------|-------------------|
| **product** | can, glass, cutouts | Yes |
| **identity** | logo, tagline, leaves | Yes |
| **marketing** | stats, garnishes, can-alt | Yes |
| **marketing** | `pep-flyer`, `hero-background`, `template-podium` | **Skipped** (full scenes — keep as-is) |

## Website usage

| Asset | Path |
|-------|------|
| Hero can | `product/bg_removed/pep-can-background-removed.png` |
| Header logo | `identity/logo-pep.png` → switch to `identity/bg_removed/logo-pep-background-removed.png` when ready |

## Staging uploads

Drop new files in **`tmp/`**, then sort into the right `originals/` folder and run `python scripts/bg_remove.py`.

### Flavour lineup → individual cans

- Source: `marketing/originals/flavours-lineup.png`
- Script: `python scripts/segment_flavors.py` (or `npm run segment:flavors`)
- Outputs: `product/flavours/bg_removed/`
- Optional: set `REMOVEBG_API_KEY` in `.env` for [remove.bg API](https://www.remove.bg/api) (often cleaner than local rembg alone)
- Model: `REMBG_MODEL=isnet-general-use` (default) — try `u2net` if edges look soft

Reference mockup: `marketing/originals/design-reference-full.png`
