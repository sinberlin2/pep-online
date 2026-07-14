# PEP agents

LLM agents that generate the brand and the website concept. Full end-to-end workflow:
**[docs/WORKFLOW.md](../docs/WORKFLOW.md)**. Pipeline diagram: **[docs/PIPELINE-CONCEPT.md](../docs/PIPELINE-CONCEPT.md)**.

## Setup (once)

```powershell
pip install -r requirements-agents.txt
# .env with OPENAI_API_KEY (and optional ANTHROPIC_API_KEY); never commit .env
```

## Agents

| Module | npm | Role |
|--------|-----|------|
| `agents.brand_run` | `brand` | **Strategist** — positioning, voice, competitor split → `directions/<slug>/strategy/` |
| `agents.brand_identity` | `brand:identity` | **Design themes** — extracts recurring competitor looks → `directions/<slug>/identity/design-themes.json` (themes only) |
| `agents.brand_images` | `brand:images` | Renders the **brand board** directly from the strategy + a chosen design theme (`--theme <id>`) — the main visual deliverable |
| `agents.brand_package` | `brand:package` | Assembles design-system + `brandings.json` (no LLM) |
| `agents.concept_run` | `concept` | Proposes a whole-site **concept** (web search) → `experiments/` |

Run any per direction with `--positioning 1|2|3` (or the slug). Most default to OpenAI; add
`--provider anthropic` where supported.

```powershell
python -m agents.brand_run --positioning 3
python -m agents.brand_identity --positioning 3
python -m agents.concept_run --positioning 3
```

Not built yet: a `review_run` design-critic pass (see `docs/AGENT-LAYOUT-PROPOSAL.md`).
