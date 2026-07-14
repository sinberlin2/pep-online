# Import your Mural + spreadsheet into PEP brand research

The brand agent needs **structured text** in this repo. Mural and Excel/Sheets are where you think; these exports are what ChatGPT reads.

---

## Quick path (recommended)

| Step | You do | Result in repo |
|------|--------|----------------|
| 1 | Export spreadsheet → CSV | `brand/research/characteristics.csv` |
| 2 | Export Mural board as **PNG** (full board or 2–3 frames) | `brand/research/mural/board.png` (+ optional `frame-*.png`) |
| 3 | Copy Mural board **link** (Share → view link) | `brand/research/mural/link.txt` one line |
| 4 | Optional: paste sticky-note text into one file | `brand/research/mural/notes.md` |
| 5 | Run merge script | `brand/research/research-bundle.md` (single file for agents) |
| 6 | Run brand agent (when built) | `positioning.json` + `brand-guidelines.md` |

```powershell
conda activate pep-online
cd c:\Users\doyle\projects\pep-online
python scripts/merge_brand_research.py
# later:
# python -m agents.brand_run
```

---

## Spreadsheet → `characteristics.csv`

1. In Excel or Google Sheets, use columns like the template (see `characteristics.template.csv`).
2. **File → Save As / Download → CSV (UTF-8)**.
3. Save as:

   `brand/research/characteristics.csv`

**Column guide:**

| Column | Meaning |
|--------|---------|
| `brand_name` | Brand or product name |
| `url` | Site URL if any |
| `in_line` | `yes` / `no` / `layout-only` — **critical** for filtering |
| `use_cases` | When people drink it (comma-separated) |
| `adjectives` | Words that describe look & feel (comma-separated) |
| `visual_design_notes` | Colours, typography vibe, photography style |
| `product_traits` | Protein? light? social? gym? |
| `why_in_or_out` | One sentence why PEP should or should not align |
| `lane` | e.g. seltzer, protein-rtd, café, energy (for your own sorting) |

`in_line=yes` → positioning peers.  
`in_line=no` → anti-references (agent must not treat as PEP).  
`in_line=layout-only` → Revized-style: structure only, not brand personality.

---

## Mural → images + notes

Mural has no simple “give the agent my board” button. Use **one or more** of these:

### A. PNG export (best for visual “looks”)

1. In Mural: select frames or zoom to full board.
2. **Export** → PNG (high resolution if offered).
3. Save to `brand/research/mural/`:
   - `board.png` — whole board or main frame
   - `use-cases.png`, `brand-map.png` — optional sections

The brand agent can send these to **GPT-4o vision** (same as site review) to read clusters, adjectives on stickies, and layout of your matrix.

### B. Board link

1. **Share** → copy link (viewer access for you is enough).
2. Paste into `brand/research/mural/link.txt` (one URL per line).

The automated agent **cannot** log into Mural. The link is for you and for notes in the prompt (“see board at …”). **PNG + CSV still required** for a full run.

### C. Text paste

If you have stickies as text:

1. Select content in Mural → copy, or export if your template allows.
2. Paste into `brand/research/mural/notes.md` with headings matching your frames (e.g. `## Use cases`, `## In-line brands`).

---

## What the agent produces (end state)

After `brand_run`, you should have a **single clear brand brain**:

| File | Contents |
|------|----------|
| **`positioning.json`** | Audience, occasions, approved adjectives, in-line brands, anti-brands, one-liner |
| **`brand-guidelines.md`** | Voice, colour/typography usage, photography, web UI do/don’t |
| **`brand-fit.json`** | Machine-readable: which looks/adjectives/design patterns **fit** vs **reject** |

`concept_run` will be updated to **require** `positioning.json` so site ideas stop drifting to gym protein sites.

---

## Privacy

- Do not put API keys in Mural or the spreadsheet.
- If the Mural board is private, **do not** commit a public share link unless you are comfortable; PNG + CSV export is enough for the agent.
