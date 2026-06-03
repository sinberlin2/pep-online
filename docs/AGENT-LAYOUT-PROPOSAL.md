# Proposal: AI layout & brand-composition agent (PEP Online)

**Status:** Draft v2 — whole-site concept + review loop  
**Default provider:** **OpenAI (ChatGPT API)**  
**Goal:** Use ChatGPT in two distinct roles—first to **conceive the whole website** (informed by similar drink brands), then again to **review the built design** for harmony—before (or alongside) fine-tuning hero assets.

---

## 1. Problem you’re solving

Today the site grew section by section (hero, flavours, occasions, about, venues). Tweaking icon positions in CSS is not the same as having a **coherent site concept**: information architecture, narrative flow, visual rhythm, and how PEP compares to drinks people already know.

You want:

1. **Concept agent (ChatGPT)** — researches/adapts patterns from **similar drink brands**, outputs a **whole-site design concept** for PEP (not just hero layers).
2. **Build step** — turn that concept into HTML/CSS on `dev` (Cursor + you, or a second “implementer” API call with strict guardrails).
3. **Review agent (ChatGPT, second call)** — after the design exists, inspect screenshots + spec and judge **harmony** (typography, color, spacing, section balance, mobile, brand fit).
4. **Refine agent (optional, later)** — small JSON tweaks for product image composition once the macro design is approved.

All of this stays on **`dev`** until you merge to **`main`** → pep-drink.com.

---

## 2. Two ChatGPT agents (core workflow)

These are **two separate API runs** with different system prompts—not one chat that does everything at once.

```text
┌──────────────────────────────────────────────────────────────────┐
│  PASS 1 — CONCEPT DIRECTOR (gpt-4.1 or gpt-4o)                    │
│  Input:  brand.json, PEP story, competitor pack, your brief       │
│  Output: experiments/concepts/<id>/site-concept.json + concept.md   │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  BUILD — implement concept on dev (Cursor / implementer agent)    │
│  Output: updated index.html, for-venues.html, css/styles.css      │
│  Then: npm start + Playwright → desktop + mobile screenshots      │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  PASS 2 — DESIGN CRITIC (gpt-4o vision)                           │
│  Input:  site-concept.json, brand.json, screenshots, live HTML    │
│  Output: experiments/runs/<id>/review.json + review.md            │
│  Scores: harmony, hierarchy, brand fit, mobile — pass / revise    │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
         Revise on dev → re-screenshot → call Critic again until pass
                             ▼
         Optional PASS 3 — asset composition tweaks (hero JSON variants)
                             ▼
         You merge to main
```

**Why two passes:** The model that **invents** a layout is biased toward its own idea. A **critic** pass with fresh context (and screenshots of what was actually built) catches drift, clashing sections, and “template feel” that copy-paste from competitors would cause.

---

## 3. Pass 1 — Whole-site concept (not just icons)

### 3.1 References — two anchors + agent discovers the rest

You maintain **`experiments/references/competitors.md`** with only your fixed URLs:

| Site | Role |
|------|------|
| **[revized-seltzer.com](https://www.revized-seltzer.com/)** | Primary inspiration — flavour grid, ritual/serving, light DTC hero |
| **[drinkpep.com](https://drinkpep.com/)** | **Same name, different product** (US probiotic *energy* drink). Use for IA patterns only (benefits, testimonials, shop cards)—**not** your protein / founder story |

**Pass 1 (`concept_run`) also uses web search** (OpenAI browsing / search tool) to find 5–8 similar sites in lanes like: premium RTD protein, light functional beverages, flavour-forward DTC drinks. It writes `discovered-references.json` per run so you can see what it found and why.

You do **not** need to hand-pick Innocent, Huel, Celsius, etc.—unless you want to add more anchors to `competitors.md` later.

Local assets always included: `design-reference-full.png`, `flavours.json`, `brand.json`.

### 3.2 What the concept agent outputs

Structured **`site-concept.json`** — the blueprint for the entire site:

```json
{
  "id": "concept-2025-06-premium-light",
  "positioning": "Premium protein drink — light, refreshing, social",
  "inspiredBy": ["Revized", "Innocent flavour strip", "Huel clarity"],
  "differentiators": ["Out-of-home occasions", "Founder story", "Venue pilot"],
  "pages": {
    "index": {
      "narrativeArc": ["hook", "product proof", "occasions", "trust", "venue CTA"],
      "sections": [
        {
          "id": "hero",
          "purpose": "One message + product beauty",
          "layoutPattern": "split-editorial",
          "copyTone": "short headline, script subline",
          "imagery": ["can", "glass", "citrus-garnish"],
          "avoid": ["busy stat cards", "full flyer as background"]
        },
        {
          "id": "drinks",
          "purpose": "Flavour discovery + vote narrative",
          "layoutPattern": "horizontal-scroll-cards",
          "notes": "One available, five coming soon — colour from flavours.json"
        },
        { "id": "enjoy", "layoutPattern": "occasion-grid", "replaceEmojiWith": "optional photo icons later" },
        { "id": "about", "layoutPattern": "founders-split", "emphasis": "Lou UX + Shannon AI" },
        { "id": "cta-band", "layoutPattern": "full-bleed-green", "goal": "drive to for-venues" }
      ]
    },
    "for-venues": {
      "sections": ["hero", "why-pep", "serving", "form"],
      "visualLinkToIndex": "shared header, tokens, CTA style"
    }
  },
  "designTokens": {
    "colorsFromBrandJson": true,
    "spacingScale": "8px base",
    "heroDensity": "airy",
    "sectionRhythm": "alternating cream / white / green bands"
  },
  "typography": {
    "display": "Didot",
    "badges": "Bebas Neue",
    "script": "Brittany or fallback",
    "body": "Montserrat 500"
  },
  "harmonyPrinciples": [
    "Max one script line per viewport",
    "Product photography always on brand greens/creams",
    "Venues page feels like same family as home"
  ]
}
```

Plus human-readable **`concept.md`**: mood, section-by-section rationale, what **not** to do, and explicit **adaptations** (“like Innocent’s flavour row but calmer, more premium”).

### 3.3 CLI (Pass 1)

```powershell
python -m agents.concept_run --brief "Premium light, social protein, venue-led GTM" --provider openai
```

Writes to `experiments/concepts/<timestamp>/`:

- `site-concept.json` + `concept.md`
- `discovered-references.json` — URLs the agent found + patterns to adapt

---

## 4. Build step (between the two agents)

The concept is not the website. Implementation options:

| Approach | Who | When |
|----------|-----|------|
| **A — Cursor + you** | Human-led from `site-concept.json` | Safest v1 |
| **B — Implementer API call** | ChatGPT with “only edit these files” + schema | Faster; needs diff review |
| **C — Hybrid** | GPT drafts CSS token block + section order; you merge | Good balance |

**v1 recommendation:** **A or C** for full HTML/CSS changes; keep automated JSON for hero **composition** only after the critic passes.

Always branch: `dev` or `agent/concept-<id>`.

---

## 5. Pass 2 — Design critic (harmony review)

Run **only after** Playwright captures the built site:

```powershell
python -m agents.review_run --concept experiments/concepts/.../site-concept.json --screenshots experiments/runs/.../previews/
```

### 5.1 Critic rubric (structured `review.json`)

| Dimension | What ChatGPT checks (vision + HTML excerpt) |
|-----------|-----------------------------------------------|
| **Harmony** | Do sections feel like one brand? Consistent bands, radii, shadows |
| **Hierarchy** | Is the eye path hero → product → trust → CTA obvious? |
| **Typography** | Not too many voices; script used sparingly |
| **Color** | Stays within `brand.json`; no one-off hex surprises |
| **Imagery** | Product scale consistent; no floating awkward crops |
| **Competitive fit** | Feels premium-light, not gym shake or kids’ juice |
| **Mobile** | Scroll, tap targets, hero doesn’t crush copy |
| **Accessibility flags** | Contrast, heading order (advisory) |

Output:

```json
{
  "verdict": "revise",
  "overallScore": 72,
  "scores": { "harmony": 68, "hierarchy": 80, "brandFit": 75, "mobile": 70 },
  "strengths": ["..."],
  "issues": [
    { "severity": "high", "section": "hero", "finding": "...", "suggestion": "..." }
  ],
  "revisionBrief": "One paragraph you can feed back into Cursor or concept_run v2"
}
```

**`verdict: "pass"`** → you’re allowed to merge to `main` (your call). **`revise`** → fix on `dev`, re-screenshot, run `review_run` again (fresh thread, same concept id).

Use **gpt-4o** (vision) for Pass 2; **gpt-4.1** for Pass 1 text-heavy concept.

---

## 6. Pass 3 (optional) — Asset composition fine-tune

Once macro design passes the critic, use the smaller **variant JSON** system (original proposal) only for hero layer positions and carousel density—not for reinventing the whole site.

```powershell
python -m agents.layout_run --concept-id concept-2025-06-premium-light --count 5
```

This is **subordinate** to the site concept, not a replacement.

---

## 7. Recommended build order (phased)

### Phase 0 — Reference anchors (~done)

- `experiments/references/competitors.md` — Revized + drinkpep.com (with name-collision note)
- Agent discovers additional sites at concept time via web search

### Phase 1 — Concept agent + OpenAI (~3–5 days)

- `agents/concept_run.py` + `prompts/concept_director.md`
- Output `site-concept.json` + `concept.md`
- No production HTML changes yet

### Phase 2 — Build on `dev` (~3–7 days)

- Implement winning concept (Cursor/hybrid)
- Playwright screenshots → `experiments/runs/<id>/previews/`

### Phase 3 — Critic agent (~2–3 days)

- `agents/review_run.py` + `prompts/design_critic.md`
- Loop until `verdict: pass` or you override

### Phase 4 — Variant / composition tweaks (optional)

### Phase A — Variant system (foundation, for Pass 3 only)

**Don’t let the agent rewrite raw HTML freely at first.** Introduce a small **declarative config** the agent edits instead:

```json
// experiments/variants/hero-v3.json (example shape)
{
  "id": "hero-v3",
  "label": "Glass-forward, citrus subtle",
  "page": "index",
  "hero": {
    "layout": "split", 
    "assets": [
      { "src": "brand/product/bg_removed/pep-glass-background-removed.png", "role": "glass", "z": 2, "x": "58%", "y": "12%", "scale": 0.92 },
      { "src": "brand/product/bg_removed/pep-can-background-removed.png", "role": "can", "z": 3, "x": "42%", "y": "0%", "scale": 1 },
      { "src": "brand/marketing/bg_removed/garnishes-citrus-background-removed.png", "role": "garnish", "z": 1, "x": "70%", "y": "55%", "scale": 0.75, "opacity": 0.85 }
    ]
  },
  "sections": ["hero", "drinks", "enjoy", "about"],
  "notes": "Inspired by design-reference-full.png — glass leads visually"
}
```

- **One loader** (`js/variant-preview.js` or build-time merge) applies variant JSON → CSS variables / inline styles for `.hero-product` layers
- **Brand contract:** agent may only reference paths under `brand/` that exist in a generated **asset manifest** (from a small script scanning `originals/` + `bg_removed/`)
- **Guardrails:** validate against `brand/brand.json` (allowed colors, font families)

**Why:** Bounded search space = fewer broken pages, easier rollback, diffs you can actually review in Git.

---

### Phase B — Layout fine-tune CLI (after critic pass)

OpenAI returns structured **hero/carousel** variant JSON only; validator enforces asset paths. See Pass 3 above.

**Agent inputs (context pack):**

| Source | Use |
|--------|-----|
| `brand/brand.json` | Colors, typography — hard constraints |
| `brand/README.md`, `identity/typography.md` | Rules and usage |
| `brand/product/flavours/flavours.json` | Carousel colors/order |
| `marketing/originals/design-reference-full.png` | Visual target (multimodal) |
| Current `index.html` + `css/styles.css` | Baseline structure |
| Asset manifest | Allowed image paths only |

**Agent outputs:**

- `experiments/variants/*.json` — layout/composition specs
- `experiments/runs/<timestamp>/report.md` — what changed, why, risks
- Optional: patch to `css/styles.css` only for **section order** or **spacing tokens** if you add CSS variables for spacing

**Human-in-the-loop (required):**

- Agent never pushes to `main`
- Default branch for agent commits: `dev` or `agent/experiments-<date>`
- You approve via: localhost preview → merge to `main` → Netlify

---

### Phase C — Preview gallery (see many setups fast)

Two options (pick one or both):

1. **Local gallery page** — `experiments/gallery.html`  
   - Lists variants from `experiments/variants/`  
   - iframe or query param `?variant=hero-v3` loads the same homepage with different composition  
   - Run with `npm start` — no deploy needed

2. **Static screenshots (CI or local script)**  
   - Playwright: open each variant URL, capture desktop + mobile PNG  
   - Agent compares screenshots to reference mockup (vision model) and scores alignment  
   - Output: `experiments/runs/<id>/previews/` for side-by-side review in Finder

This is where “experiment with different setups” becomes tangible: **10 layouts in 10 minutes**, not 10 afternoons.

---

### Phase D — Image arrangement tools (beyond CSS nudge)

Pair the agent with **deterministic scripts** it can invoke (not hallucinate):

| Tool | Already have | Agent use |
|------|----------------|-----------|
| `scripts/bg_remove.py` | Yes | Re-run when new assets land in `tmp/` |
| `scripts/segment_flavors.py` | Yes | Refresh flavour carousel cutouts |
| New: `scripts/compose_hero.py` | Proposed | Given variant JSON, export a single marketing PNG (optional) for social |
| New: `scripts/asset_manifest.py` | Proposed | JSON list of safe paths + dimensions for agent |

Agent **chooses** arrangement parameters; scripts **execute** pixel work. Reduces “invented file path” errors.

---

## 8. OpenAI (ChatGPT API) — default setup

**Start with OpenAI only.** Claude stays available later via the same `provider.py` if you want A/B tests.

**Environment (`.env`):**

```bash
LAYOUT_AGENT_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Pass 1 — whole-site concept (text + optional reference images)
CONCEPT_AGENT_MODEL=gpt-4.1

# Pass 2 — harmony critic (screenshots required)
REVIEW_AGENT_MODEL=gpt-4o

# Pass 3 — hero composition tweaks (cheap bulk)
LAYOUT_AGENT_MODEL=gpt-4o-mini
```

| Pass | CLI | Model | Input |
|------|-----|-------|--------|
| **1 Concept** | `concept_run` | gpt-4.1 | competitors.md, brand.json, brief, mockup PNGs |
| **2 Critic** | `review_run` | gpt-4o | site-concept.json, Playwright PNGs, HTML excerpt |
| **3 Layout** | `layout_run` | gpt-4o-mini | approved concept + asset manifest |

Use the **API** ([platform.openai.com](https://platform.openai.com)), not the chat UI—so concepts and reviews are versioned under `experiments/`.

**Structured outputs:** JSON schema on every pass; validator retry on Pass 3 only.

**Cost (rough):** one concept + two review loops ≈ **$0.20–$1.00**; add vision screenshots each review.

**Cursor’s role:** implement `site-concept.json`, fix issues from `review.json`, build the CLIs—not replace Pass 1 or Pass 2.

---

## 9. Brand guardrails (all passes)

Encode these in validator + agent system prompt:

1. **Assets:** Only paths from `asset_manifest.json`; prefer `bg_removed/` for product shots on web
2. **Colors:** Only keys from `brand.json` → `colors` (or CSS variables mapped to them)
3. **Fonts:** Didot / Bebas / Montserrat on web; Brittany = fallback until WOFF2 licensed
4. **Copy:** Concept agent may propose headlines in `site-concept.json`; **founder facts and SKU truth stay fixed**; no auto-merge of copy to `main` without you
5. **Competitors:** Adapt **patterns**, never copy logos, names, or proprietary creative
6. **Performance:** Max 3–4 hero layers; `fetchpriority` on LCP image only
7. **Accessibility:** Critic flags issues; implementer must not remove alt text or heading order silently

---

## 10. What changes at each level

| Level | Concept agent | Critic agent | Layout agent (Pass 3) |
|-------|---------------|--------------|------------------------|
| **Site IA** | Section order, narrative arc, page goals | Flow feels coherent | — |
| **Visual system** | Tokens, bands, typography rules | Harmony score | — |
| **Hero** | Pattern (split, centered, product-led) | Balance vs copy | Asset x/y/scale |
| **Flavours** | Carousel vs grid, vote story placement | Readable on mobile | Card density |
| **Enjoy / About** | Grid vs editorial, emoji vs photo | Section weight | — |
| **Venues page** | Same family as index | Cross-page consistency | — |
| **Copy** | Proposals in concept only | Tone consistency | — |

**Fixed forever (unless you edit):** Lou/Shannon story facts, 1 live flavour + 5 soon, form endpoint, `brand.json` colors/fonts.

---

## 11. Integration with Mantique (optional later)

You already have **`mantique`** with `brand_memory.py` (chunked `brand.json`, embeddings). Later:

- Same `brand.json` syncs into Mantique’s vector store
- Layout agent retrieves “tone + visual rules” via RAG
- Winning web variants inform **social templates** (one brand brain, two surfaces)

Not required for Phase A–B; avoid blocking the web agent on Mantique.

---

## 12. Implementation stack

| Layer | Choice |
|-------|--------|
| **Pass 1** | `agents/concept_run.py` → OpenAI gpt-4.1 |
| **Build** | Cursor + you on `dev` |
| **Pass 2** | `agents/review_run.py` → OpenAI gpt-4o + Playwright PNGs |
| **Pass 3** | `agents/layout_run.py` → gpt-4o-mini (optional) |
| **Deploy** | You merge to `main` → Netlify |

**Dependencies:** `openai`, `pillow`, `playwright` (screenshots); `anthropic` optional later.

```json
"concept": "python -m agents.concept_run",
"review": "python -m agents.review_run",
"experiment": "python -m agents.layout_run"
```

---

## 13. Suggested file layout

```text
pep-online/
  agents/
    concept_run.py       # Pass 1 — whole-site concept
    review_run.py        # Pass 2 — harmony critic
    layout_run.py        # Pass 3 — composition tweaks
    llm/openai_client.py
    prompts/
      concept_director.md
      design_critic.md
      layout_system.md
    validate_variant.py
  experiments/
    references/
      competitors.md     # you maintain
    concepts/            # site-concept.json + concept.md
    variants/            # hero tweaks (Pass 3)
    runs/                # previews + review.json
  scripts/
    asset_manifest.py
    capture_screenshots.py
```

---

## 14. Architecture diagram (full pipeline)

```text
competitors.md + brief
        → concept_run (GPT-4.1) → site-concept.json
        → build on dev (Cursor)
        → capture_screenshots.py
        → review_run (GPT-4o vision) → review.json
        → revise loop → pass → optional layout_run → main
```

---

## 15. Success metrics

- **Concept:** 1 `site-concept.json` you’d actually build (not generic “modern website”)
- **Critic:** Review catches at least one real issue you agree with before `main`
- **Harmony:** `review.json` harmony ≥ 80 before merge (or you document override)
- **Whole site:** `index` + `for-venues` feel like one product, not two templates
- **Safety:** Competitor inspiration = patterns only; PEP brand colors/fonts enforced

---

## 16. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Agent breaks production HTML | Variants JSON only in v1; HTML changes human-approved |
| Off-brand colors/fonts | Validator + `brand.json` allowlist |
| Huge repo / slow deploy | Don’t commit screenshot blobs; keep experiments on `dev` |
| API cost (vision) | Batch screenshots; vision-rank finalists only; Haiku/mini for bulk |
| API key leak | `.env` only; never commit; rotate if exposed |
| Provider lock-in | `provider.py` abstraction; same JSON schema for Claude and GPT |
| Generic “AI slop” layout | Competitor pack + PEP mockups + critic pass |
| Copying competitor branding | Prompt: patterns only; critic checks brand fit |
| Worse than manual | Keep current site on `main`; all experiments on `dev` |

---

## 17. Recommended next steps

1. **OpenAI key** in `.env` only (not `.env.example`) — [platform.openai.com](https://platform.openai.com)
2. **Anchors** — Revized + drinkpep.com are in `experiments/references/competitors.md` ✓
3. **Build Pass 1** — `concept_run` with web search → `site-concept.json` + `discovered-references.json`
4. **You + Cursor implement** concept on `dev`
5. **Build Pass 2** — Playwright + `review_run` → fix from `revisionBrief`
6. **Merge to `main`** only after critic `pass` (or conscious override)
7. **Pass 3 later** — hero composition JSON if needed

---

## 18. Effort estimate

| Phase | Effort | Outcome |
|-------|--------|---------|
| 0 — Reference pack | 1 hour | Grounded competitor context |
| 1 — `concept_run` | 3–5 days | Whole-site blueprint |
| 2 — Build on dev | 3–7 days | Real HTML/CSS |
| 3 — `review_run` + screenshots | 2–4 days | Harmony loop |
| 4 — `layout_run` | Optional | Pixel-level hero tweaks |

**MVP:** Phases 0–3 with OpenAI only (~2 weeks part-time).

---

*Confirm before build:*  
1) **Build step** — Cursor-only v1, or also an “implementer” GPT call?  
2) **Review bar** — must critic say `pass`, or is a score + your judgment enough?
