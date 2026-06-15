# PEP Online

Marketing site for **PEP** — a light, refreshing premium drink with a protein boost. Built from the café handout design, with room to grow into an AI tool for Instagram and other social content.

## Pages

| Page | URL | Content |
|------|-----|---------|
| Landing (the drink) | `index.html` | Hero, 7g protein / 49 calories, product details, “Perfect for” occasions |
| For venues | `for-venues.html` | Why venues love PEP, how to serve, pilot steps, **customer inquiry form** |

## Production domain

**https://pep-drink.com** — see [DEPLOY.md](DEPLOY.md) for DNS and hosting (Cloudflare Pages / Netlify + GitHub).

## Develop locally (see changes instantly)

```bash
npm start
```

Open **http://localhost:3000** — save files and refresh; the live site does not change until you `git push`.

See **[DEVELOPMENT.md](DEVELOPMENT.md)** — **`dev`** for local WIP, **`main`** updates **pep-drink.com** when you merge and push.

## API keys (local only)

Copy `.env.example` to **`.env`** and add your keys there. **`.env` is gitignored** and must never be pushed to GitHub—only `.env.example` (placeholders, no secrets) is committed.

## AI site concept (Pass 1)

```powershell
pip install -r requirements-agents.txt
npm run concept
```

See **[agents/README.md](agents/README.md)** — OpenAI proposes a whole-site concept (Revized + drinkpep anchors, web search for more references). Outputs go to `experiments/concepts/`.

## Customer inquiry form

The form on **For venues → Join the PEP pilot** collects:

- Name (required)
- Venue name (optional)
- Email (required)
- Interest type
- Message

### Connect email (Formspree)

1. Create a free form at [formspree.io](https://formspree.io).
2. Edit `js/config.js` and set `FORM_ENDPOINT` to your form URL, e.g. `https://formspree.io/f/abcdefgh`.

Until then, submissions are stored in the browser’s `localStorage` under `pep_inquiries` (demo mode).

## Brand assets (`brand/`)

All logos, product shots, and marketing files live under **`brand/`** — see `brand/README.md`.

| Folder | Purpose |
|--------|---------|
| `brand/design-concepts/pep-original/identity/` | Logo, typography — from the **example design** (exploratory) |
| `brand/design-concepts/pep-original/product/` | Hero PNGs (can, glass) — **used on the landing page** |
| `brand/design-concepts/pep-original/marketing/` | Flyers, mockups, reference artwork |

**Landing hero** — assets live under `brand/directions/provided/assets/product/`:

- `pep-can.png`, `pep-glass.png`, `pep-mango.png` (optional)

PNG with alpha, trimmed tight; the site adds cream background and orange glow in CSS.

Site colours and fonts: `css/styles.css`.

## Roadmap

- [x] Brand assets sorted from `brand/tmp/` into `identity/`, `product/`, `marketing/`
- [ ] Formspree / backend for enquiries
- [ ] AI Instagram post generator (future)

## Project structure

```
pep-online/
├── index.html          # Landing — the drink
├── for-venues.html     # Venues + pilot + inquiry form
├── css/styles.css
├── js/
│   ├── main.js         # Mobile nav
│   ├── config.js       # Form endpoint
│   └── inquiry.js      # Form handling
├── brand/              # Identity, product, marketing assets
│   ├── identity/
│   ├── product/
│   └── marketing/
└── README.md
```
