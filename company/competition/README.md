# Competition research

Competitor landscape — **input for branding**, sorted by positioning and drink type.

| File | Role |
|------|------|
| `sources/drink-competition.pdf` | Original competition table export |
| `characteristics.csv` | Brands with `positioning_id`, `category`, visual notes |
| `manual-competitors.csv` | Names you add manually |
| `competition-extracted.json` | Raw PDF extraction |
| `competitor-enrichment-log.json` | Enrichment run log |

```bash
python scripts/extract_competition_pdf.py
python scripts/enrich_competitors.py
python scripts/merge_brand_research.py
```
