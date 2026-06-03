# PEP site design agents

## Setup (once)

```powershell
cd c:\Users\doyle\projects\pep-online
conda activate pep-online
pip install -r requirements-agents.txt
copy .env.example .env
# Edit .env — put OPENAI_API_KEY there only (never in .env.example)
```

## Pass 1 — Whole-site concept

```powershell
python -m agents.concept_run --brief "Premium light protein, venue pilot, flavour-forward"
```

Uses:

- Anchors: `experiments/references/competitors.md` (Revized + drinkpep.com)
- Web search (default on) to find 5–8 similar drink sites
- `brand.json`, `flavours.json`, current `index.html`

Outputs under `experiments/concepts/<timestamp>-<id>/`:

| File | Content |
|------|---------|
| `site-concept.json` | Full IA + sections + tokens |
| `discovered-references.json` | URLs the agent found |
| `concept.md` | Readable brief |
| `research-memo.txt` | Raw web research (if search ran) |

Skip web search:

```powershell
python -m agents.concept_run --brief "..." --no-web-search
```

## Pass 2 — Design critic

`review_run` — not built yet. Run after you implement the concept on `dev` and capture screenshots.

## npm

```bash
npm run concept
```
