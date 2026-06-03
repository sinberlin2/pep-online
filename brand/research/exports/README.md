# Brand research exports

Shareable brand guideline packs (regenerate after editing markdown in `directions/*/brand-guidelines.md`):

```powershell
npm run brand:export
```

| File | Best for |
|------|----------|
| `PEP-brand-guidelines.html` | Email/link — open in any browser; looks correct without extra tools |
| `PEP-brand-guidelines.pdf` | Attachments, print (needs Playwright + Chromium) |
| `PEP-brand-guidelines-functional-protein.png` | Slack, WhatsApp, quick preview |
| `PEP-brand-guidelines-lifestyle.png` | Same |
| `PEP-brand-guidelines-social.png` | Same |

**HTML only** (no Chromium): `python scripts/export_brand_guidelines.py --html-only`

First-time PDF/PNG setup:

```powershell
pip install markdown playwright
playwright install chromium
```
