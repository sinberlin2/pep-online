# Staging folder

Drop new brand images here (any filenames). Then run from project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\organize-brand-assets.ps1
```

Or ask Cursor to organize them — files will be moved into `identity/`, `product/`, or `marketing/` with standard names.

**Do not** commit huge PSDs here; use PNG/SVG/JPG/WebP only.
