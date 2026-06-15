"""
Export brand guidelines as styled HTML, PDF, and PNG images.

Usage:
  python scripts/export_brand_guidelines.py
  python scripts/export_brand_guidelines.py --html-only

Outputs (brand/exports/):
  PEP-brand-guidelines.html          — open in browser; Print → PDF if needed
  PEP-brand-guidelines.pdf           — print-quality PDF (requires playwright)
  PEP-brand-guidelines-<slug>.png    — one full-page image per direction
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paths  # noqa: E402

DIRS = paths.DIRECTIONS
OUT_DIR = paths.EXPORTS

SECTIONS = [
    ("functional-protein", "Functional protein drink", "1"),
    ("lifestyle", "Lifestyle upgrade", "2"),
    ("social", "Better social drink", "3"),
]

ACCENTS = {
    "functional-protein": "#1f4d3a",
    "lifestyle": "#c47b5a",
    "social": "#e86a1a",
}


def _load_brand() -> dict:
    if paths.PRODUCT_PROFILE.is_file():
        return json.loads(paths.PRODUCT_PROFILE.read_text(encoding="utf-8"))
    return {"colors": {"green": "#1f4d3a", "cream": "#faf6f0", "orange": "#e86a1a"}}


def _read_md(slug: str) -> str:
    path = DIRS / slug / "brand-guidelines.md"
    if not path.is_file():
        return f"*(Missing: {path})*\n"
    return path.read_text(encoding="utf-8")


def _md_to_html(text: str) -> str:
    import markdown

    return markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "nl2br"],
    )


def _build_html(sections_html: list[tuple[str, str, str, str]]) -> str:
    brand = _load_brand()
    colors = brand.get("colors", {})
    cream = colors.get("cream", "#faf6f0")
    green = colors.get("green", "#1f4d3a")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    nav_items = "".join(
        f'<a href="#direction-{slug}">{num}. {title}</a>'
        for slug, title, num in SECTIONS
    )

    body = []
    for slug, title, num, content_html in sections_html:
        accent = ACCENTS.get(slug, green)
        body.append(
            f"""
<article id="direction-{slug}" class="direction direction-{slug}" style="--accent: {accent};">
  <header class="direction-header">
    <p class="direction-num">Direction {num}</p>
    <h2 class="direction-title">{title}</h2>
  </header>
  <div class="direction-body prose">
    {content_html}
  </div>
</article>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PEP Brand Guidelines</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=GFS+Didot&family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --cream: {cream};
      --green: {green};
      --text: #1a1a1a;
      --muted: #5c5c5c;
      --border: #e8e2d8;
      --max: 42rem;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: Montserrat, system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.65;
      color: var(--text);
      background: var(--cream);
    }}
    .cover {{
      background: linear-gradient(160deg, var(--green) 0%, #163a2c 55%, #0f2a20 100%);
      color: #fff;
      padding: 3.5rem 1.5rem 4rem;
      text-align: center;
    }}
    .cover h1 {{
      font-family: "GFS Didot", Didot, Georgia, serif;
      font-size: clamp(2rem, 6vw, 2.75rem);
      font-weight: 400;
      margin: 0 0 0.5rem;
      letter-spacing: 0.02em;
    }}
    .cover .tagline {{
      font-size: 1rem;
      opacity: 0.9;
      margin: 0 0 1.5rem;
    }}
    .cover .meta {{
      font-size: 0.8rem;
      opacity: 0.65;
    }}
    nav.toc {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.5rem 1.25rem;
      padding: 1.25rem 1.5rem;
      background: #fff;
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 10;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    nav.toc a {{
      color: var(--green);
      text-decoration: none;
      font-weight: 600;
      font-size: 0.85rem;
    }}
    nav.toc a:hover {{ text-decoration: underline; }}
    main {{
      max-width: calc(var(--max) + 4rem);
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}
    .direction {{
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 24px rgba(31, 77, 58, 0.08);
      margin-bottom: 2.5rem;
      overflow: hidden;
      border: 1px solid var(--border);
    }}
    .direction-header {{
      padding: 1.75rem 2rem 1.25rem;
      border-bottom: 3px solid var(--accent);
      background: linear-gradient(180deg, #fff 0%, #fdfbf8 100%);
    }}
    .direction-num {{
      margin: 0 0 0.25rem;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    .direction-title {{
      margin: 0;
      font-family: "GFS Didot", Didot, Georgia, serif;
      font-size: 1.65rem;
      font-weight: 400;
      color: var(--text);
    }}
    .direction-body {{
      padding: 1.5rem 2rem 2rem;
    }}
    .prose h1 {{
      font-family: "GFS Didot", Didot, Georgia, serif;
      font-size: 1.5rem;
      font-weight: 400;
      color: var(--accent);
      margin: 0 0 1rem;
      line-height: 1.3;
    }}
    .prose h2 {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text);
      margin: 1.75rem 0 0.65rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid var(--border);
    }}
    .prose h3 {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--muted);
      margin: 1.25rem 0 0.5rem;
    }}
    .prose p {{ margin: 0 0 0.85rem; }}
    .prose ul, .prose ol {{
      margin: 0 0 1rem;
      padding-left: 1.35rem;
    }}
    .prose li {{ margin-bottom: 0.35rem; }}
    .prose li::marker {{ color: var(--accent); }}
    .prose strong {{ font-weight: 700; color: var(--text); }}
    .prose hr {{
      border: none;
      border-top: 1px solid var(--border);
      margin: 1.5rem 0;
    }}
    .prose em {{ color: var(--muted); }}
    @media print {{
      nav.toc {{ display: none; }}
      body {{ background: #fff; }}
      main {{ max-width: none; padding: 0; }}
      .direction {{
        box-shadow: none;
        border-radius: 0;
        border: none;
        page-break-before: always;
        margin-bottom: 0;
      }}
      .cover {{ page-break-after: always; }}
    }}
  </style>
</head>
<body>
  <header class="cover">
    <h1>PEP Brand Guidelines</h1>
    <p class="tagline">Three product directions — Lou &amp; Shannon</p>
    <p class="meta">Generated {generated}</p>
  </header>
  <nav class="toc">{nav_items}</nav>
  <main>
    {"".join(body)}
  </main>
</body>
</html>
"""


def _write_html(html: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "PEP-brand-guidelines.html"
    out.write_text(html, encoding="utf-8")
    return out


def _export_pdf_png(html_path: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print(
            "Playwright not installed — HTML only.\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            f"  ({exc})",
            file=sys.stderr,
        )
        return

    file_url = html_path.resolve().as_uri()
    pdf_path = OUT_DIR / "PEP-brand-guidelines.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 1200})
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(500)

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
        )
        print(f"Wrote {pdf_path.relative_to(ROOT)}")

        for slug, title, _num in SECTIONS:
            loc = page.locator(f"#direction-{slug}")
            png_path = OUT_DIR / f"PEP-brand-guidelines-{slug}.png"
            loc.screenshot(path=str(png_path), type="png")
            print(f"Wrote {png_path.relative_to(ROOT)}")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Skip PDF/PNG (no Playwright)",
    )
    args = parser.parse_args()

    sections_html = []
    for slug, title, num in SECTIONS:
        md = _read_md(slug)
        sections_html.append((slug, title, num, _md_to_html(md)))

    html = _build_html(sections_html)
    html_path = _write_html(html)
    print(f"Wrote {html_path.relative_to(ROOT)}")
    print(f"  Open in browser: {html_path.resolve()}")

    if not args.html_only:
        _export_pdf_png(html_path)


if __name__ == "__main__":
    main()
