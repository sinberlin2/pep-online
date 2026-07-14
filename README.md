# PEP Online

Marketing site for **PEP** — a light, refreshing premium drink with a protein boost. Built from the café handout design, with room to grow into an AI tool for Instagram and other social content.

## Pages

| Page | URL | Content |
|------|-----|---------|
| Landing (the drink) | `site/index.html` | Hero, 7g protein / 49 calories, product details, “Perfect for” occasions |
| For venues | `site/for-venues.html` | Why venues love PEP, how to serve, pilot steps, **customer inquiry form** |

## Production domain

**https://pep-drink.com** — see [DEPLOY.md](DEPLOY.md) for DNS and hosting (Cloudflare Pages / Netlify + GitHub).

## Documentation

| Doc | What |
|-----|------|
| **[docs/WORKFLOW.md](docs/WORKFLOW.md)** | **Start here** — end-to-end workflow (website + brand pipeline), what each agent does |
| [docs/PIPELINE-CONCEPT.md](docs/PIPELINE-CONCEPT.md) | One-screen pipeline diagram |
| [docs/ASSETS.md](docs/ASSETS.md) | Repo layout (`site/` vs `brand/`), asset buckets, git policy |
| [brand/README.md](brand/README.md) | Branding module — per-step detail |
| [agents/README.md](agents/README.md) | The agents — setup + list |
| [DEVELOPMENT.md](DEVELOPMENT.md) · [DEPLOY.md](DEPLOY.md) | Website dev/release flow · DNS & hosting |
| [docs/BRANDING-PIPELINE.md](docs/BRANDING-PIPELINE.md) | Architecture & roadmap (incl. planned Flow B) |
| [docs/AGENT-LAYOUT-PROPOSAL.md](docs/AGENT-LAYOUT-PROPOSAL.md) · [docs/BRAND-OUTPUT-SCHEMA-TODO.md](docs/BRAND-OUTPUT-SCHEMA-TODO.md) | Historical concept-agent proposal · schema status |

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

## Sign-up forms

Two forms feed straight into **Netlify Forms** — no API key or endpoint to configure. Netlify captures every submission once the site is deployed on Netlify.

| Form | Where | Collects |
|------|-------|----------|
| **Subscribers** | Landing (`index.html`) — “Be first to try PEP” band | Email |
| **Venue pilot** | `for-venues.html` → Join the PEP pilot | Name (required), venue, email (required), interest, message |

Both are handled by `site/js/forms.js`: it validates, AJAX-posts to Netlify, and shows an inline confirmation (the visitor stays on the page).

### Where submissions go

1. Deploy on **Netlify** (see [DEPLOY.md](DEPLOY.md)). Netlify auto-detects the forms at build time.
2. In the Netlify dashboard → **Forms** you’ll see the **venue-pilot** and **subscribers** submissions.
3. Add an email notification (**Forms → Settings → Form notifications**) to forward new sign-ups to sjdoyle46@gmail.com.

> On `localhost` Netlify can’t capture submissions, so the forms confirm without sending — useful for testing the UI. Real capture happens only on the deployed Netlify site.

## Repo layout

The **website** lives in `site/` (the only thing Netlify deploys — `netlify.toml` →
`publish = "site"`) and reads only from `site/public/`. The **brand pipeline** (generator)
lives under `brand/`, `agents/`, `scripts/`. End-to-end workflow (website + brand pipeline):
**[docs/WORKFLOW.md](docs/WORKFLOW.md)**; repo layout & git policy: **[docs/ASSETS.md](docs/ASSETS.md)**.

## Brand assets

- **Site images** — `site/public/`: hero can lockup (`product/pep-can-lockup.{webp,png}`),
  founders (`people/founders-lou-shannon.jpg`). These are the only images the site serves.
- **Design sets to extract from** — `brand/inputs/external-designs/pep-original/`
  (identity, marketing, product, `extracted/`). See `brand/README.md`.
- Publish generated brand assets into the site with `npm run site:sync`.

Site colours and fonts: `site/css/styles.css`.

## Roadmap

- [x] Brand assets sorted from `brand/tmp/` into `identity/`, `product/`, `marketing/`
- [x] Netlify Forms backend for sign-ups (subscribers + venue pilot)
- [ ] AI Instagram post generator (future)

## Project structure

```
pep-online/
├── index.html          # Landing — the drink
├── for-venues.html     # Venues + pilot + inquiry form
├── css/styles.css
├── js/
│   ├── main.js         # Mobile nav
│   └── forms.js        # Netlify Forms handling (subscribers + venue pilot)
├── brand/              # Identity, product, marketing assets
│   ├── identity/
│   ├── product/
│   └── marketing/
└── README.md
```
