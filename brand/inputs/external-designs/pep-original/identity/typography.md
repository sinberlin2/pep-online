# PEP typography (from flyer)

Reference image: `pep-fonts-reference.png`

| Element / text type | Font | Web weight | Used for |
|---------------------|------|------------|----------|
| **PEP logo** | Didot | Bold | Brand wordmark “PEP” |
| **NEW!** | Bebas Neue | Regular | Promo / “NEW!” badges |
| **Main script text** | Brittany Signature | — | Tagline, romantic script lines |
| **Numbers (7 / 49)** | Montserrat | ExtraBold (800) | Stat callout numbers |
| **Labels & badges** | Montserrat | Medium (500) | “protein”, “calories”, UI labels |
| **Bottom slogan** | Brittany Signature | — | “Feel good. Have fun.” |

## Website mapping (`css/styles.css`)

| CSS variable | Flyer font |
|--------------|------------|
| `--font-logo` | Didot |
| `--font-display` | Bebas Neue |
| `--font-script` | Brittany Signature |
| `--font-label` | Montserrat Medium |
| `--font-stat` | Montserrat ExtraBold |

## Web fonts

Loaded via Google Fonts in HTML:

- **GFS Didot** — stand-in for Didot
- **Bebas Neue**
- **Montserrat** (500, 800)

**Brittany Signature** is not on Google Fonts. The site uses `Segoe Script` as a temporary fallback until you add licensed files under `brand/research/design-concepts/pep-original/identity/fonts/`.

## Adding Brittany Signature (optional)

1. Place `BrittanySignature.woff2` in `brand/research/design-concepts/pep-original/identity/fonts/`
2. Add `@font-face` in `css/styles.css`
3. Set `--font-script: "Brittany Signature", ...`
