"""
Fetch one representative image per competitor — a CLEARLY VISIBLE CAN/BOTTLE.

For each brand in competition-extracted.json we gather several candidate images from
the brand's site (og:image, twitter:image, and prominent <img> tags), then use a vision
model to pick the one that most clearly shows the product packaging (a can or bottle),
rejecting logos, lifestyle scenes, banners, and people-dominated shots. The chosen image
is downscaled and saved for the identity agent's design-theme analysis.

Usage:
  python scripts/fetch_competitor_images.py
  python scripts/fetch_competitor_images.py --overwrite   # refetch auto images
  python scripts/fetch_competitor_images.py --no-vision    # keep og:image, skip can-selection
  python scripts/fetch_competitor_images.py --limit 10

Manual override:
  Drop a file named <brand-slug>.png (or .jpg/.webp) into
  brand/inputs/competition/images/ and it will be kept — auto-fetch never overwrites a
  hand-dropped image.

Inputs:
  brand/inputs/competition/competition-extracted.json

Outputs:
  brand/inputs/competition/images/<brand-slug>.png
  brand/inputs/competition/images/images-manifest.json
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

import paths  # noqa: E402

MAX_EDGE = 768
MAX_CANDIDATES = 8
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
# URL hints that a candidate is (not) a product pack shot.
POSITIVE_HINTS = ("can", "bottle", "product", "pack", "drink", "/files/", "cdn/shop", "/products/")
NEGATIVE_HINTS = (
    "logo", "icon", "sprite", "favicon", "badge", "payment", "flag", "avatar",
    "banner", "press", "award", "placeholder", "loader", "spinner", "pixel",
)
SKIP_EXTS = (".svg", ".gif", ".ico")
# Homepage links worth following for cleaner pack shots (product/shop/collection pages).
PRODUCT_LINK_HINTS = ("product", "shop", "collection", "/drinks", "/range", "/store", "buy", "our-")

CAN_SELECT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "best_index": {
            "type": "integer",
            "description": "0-based index of the image that most clearly shows the product can/bottle, or -1 if none qualify.",
        },
        "has_can": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["best_index", "has_can", "reason"],
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")


def _largest_from_srcset(srcset: str) -> str:
    best_url, best_w = "", -1
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        url = bits[0]
        w = -1
        if len(bits) > 1 and bits[1].endswith("w"):
            try:
                w = int(bits[1][:-1])
            except ValueError:
                w = 0
        if w >= best_w:
            best_url, best_w = url, w
    return best_url


class _ImageHarvester(HTMLParser):
    """Collect og:image, twitter:image, link[image_src], and <img> candidates."""

    def __init__(self) -> None:
        super().__init__()
        self.og_image = ""
        self.twitter_image = ""
        self.link_image = ""
        self.imgs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("property", "").lower() or a.get("name", "").lower()
            content = a.get("content", "")
            if not content:
                return
            if key == "og:image" and not self.og_image:
                self.og_image = content
            elif key in ("twitter:image", "twitter:image:src") and not self.twitter_image:
                self.twitter_image = content
        elif tag == "link":
            if "image_src" in a.get("rel", "").lower() and a.get("href"):
                self.link_image = a["href"]
        elif tag == "img":
            url = (
                a.get("src")
                or a.get("data-src")
                or a.get("data-original")
                or a.get("data-lazy-src")
                or _largest_from_srcset(a.get("data-srcset") or a.get("srcset") or "")
            )
            if url and not url.startswith("data:"):
                self.imgs.append(url)


def _fetch(url: str, timeout: int) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _score(url: str) -> int:
    low = url.lower()
    return sum(3 for h in POSITIVE_HINTS if h in low) - sum(4 for h in NEGATIVE_HINTS if h in low)


def _root(url: str) -> str:
    pr = urlparse(url)
    return f"{pr.scheme}://{pr.netloc}"


def _shopify_products_images(page_url: str, timeout: int) -> list[str]:
    """Product image srcs from a Shopify storefront's products.json, if it has one."""
    root = _root(page_url)
    for path in ("/products.json?limit=30", "/collections/all/products.json?limit=30"):
        try:
            products = json.loads(_fetch(root + path, timeout)).get("products", [])
        except Exception:  # noqa: BLE001
            continue
        imgs = [im.get("src", "") for p in products for im in p.get("images", []) if im.get("src")]
        if imgs:
            return imgs
    return []


def _product_page_links(page_url: str, html: str) -> list[str]:
    """On-site product/shop/collection links worth crawling for pack shots."""
    root = _root(page_url)
    links: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r'href=["\']([^"\'#]+)["\']', html, re.I):
        href = m.group(1)
        if not any(k in href.lower() for k in PRODUCT_LINK_HINTS):
            continue
        absu = urljoin(page_url, href)
        if not absu.lower().startswith(("http://", "https://")) or _root(absu) != root:
            continue
        if absu in seen:
            continue
        seen.add(absu)
        links.append(absu)
    return links


def _candidate_urls(page_url: str, timeout: int) -> list[str]:
    raw: list[str] = []

    # 1) Shopify product feed — the cleanest pack shots when a store exposes it.
    raw += _shopify_products_images(page_url, timeout)

    # 2) Homepage meta + <img> candidates.
    try:
        html = _fetch(page_url, timeout).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        html = ""
    if html:
        h = _ImageHarvester()
        h.feed(html)
        raw += [u for u in (h.og_image, h.twitter_image, h.link_image) if u]
        raw += h.imgs
        # 3) Follow up to two product/shop pages for more pack shots (helps non-Shopify sites).
        for link in _product_page_links(page_url, html)[:2]:
            try:
                phtml = _fetch(link, timeout).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            ph = _ImageHarvester()
            ph.feed(phtml)
            raw += ph.imgs

    # Normalise, drop logos/badges (negative score) and vector/animated types, dedupe, rank.
    scored: list[str] = []
    seen: set[str] = set()
    for u in raw:
        absu = urljoin(page_url, u)
        if not absu.lower().startswith(("http://", "https://")):
            continue
        if absu.lower().split("?")[0].endswith(SKIP_EXTS):
            continue
        if _score(absu) < 0 or absu in seen:
            continue
        seen.add(absu)
        scored.append(absu)
    scored.sort(key=_score, reverse=True)
    return scored[:MAX_CANDIDATES]


def _download_downscaled(url: str, dest: Path, timeout: int) -> bool:
    try:
        data = _fetch(url, timeout)
        with Image.open(BytesIO(data)) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
            img.save(dest, format="PNG")
        return True
    except Exception:  # noqa: BLE001
        return False


def _pick_can(client, vision_json, model: str, name: str, category: str, files: list[Path]) -> dict:
    system = (
        "You select the single best PACKAGING photo for a beverage brand. You are shown "
        "candidate images in order (index 0..N-1). Choose the ONE that most clearly shows the "
        "brand's actual product packaging — a can, bottle, or sachet/pack — front-facing, "
        "unobstructed, and large in the frame. A clear BOTTLE (or sachet/pack) is just as good "
        "as a can; many brands do not sell cans, so NEVER reject an image only because it is a "
        "bottle rather than a can. Prefer a plain pack shot over a busy lifestyle scene, but a "
        "lifestyle photo is fine if the packaging is clearly visible and legible. Reject "
        "logos/wordmarks, award badges, banners, and shots where the product is tiny, absent, "
        "or obscured. Only if NO image shows the product packaging at all, return "
        "best_index = -1 and has_can = false."
    )
    user = (
        f"Brand: {name}. Category: {category}. {len(files)} candidate images attached, in order "
        "starting at index 0. Return the index of the clearest product packaging shot (can, "
        "bottle, or pack), or -1 if none show the packaging."
    )
    return vision_json(
        client,
        model=model,
        system=system,
        user=user,
        image_paths=files,
        schema_name="can_selection",
        schema=CAN_SELECT_SCHEMA,
        detail="low",
    )


def _existing_image(images_dir: Path, slug: str) -> Path | None:
    for ext in IMAGE_EXTS:
        p = images_dir / f"{slug}{ext}"
        if p.is_file():
            return p
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch competitor can/bottle images for theme analysis")
    parser.add_argument("--limit", type=int, default=200, help="Max brands to fetch per run")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Refetch auto images even if present (never touches manual overrides)",
    )
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout (seconds)")
    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Skip vision can-selection; just save the first candidate (og:image).",
    )
    parser.add_argument("--model", default="gpt-4o", help="Vision model for can-selection")
    args = parser.parse_args()

    if not paths.COMPETITION_EXTRACTED.is_file():
        raise SystemExit(f"Missing {paths.COMPETITION_EXTRACTED}")

    images_dir = paths.COMPETITION_IMAGES
    images_dir.mkdir(parents=True, exist_ok=True)

    client = vision_json = None
    if not args.no_vision:
        from agents.llm.openai_client import make_client, vision_json as _vision_json

        client = make_client()
        vision_json = _vision_json

    # Explicit per-brand image URLs (slug -> url). Authoritative: when a brand's site
    # scrape fails or picks a poor shot, pin the correct image here (e.g. a retailer or
    # Open Food Facts packshot). Overrides always win and are re-applied every run.
    overrides: dict[str, str] = {}
    if paths.COMPETITION_IMAGE_OVERRIDES.is_file():
        try:
            overrides = {
                _slug(k): v for k, v in json.loads(
                    paths.COMPETITION_IMAGE_OVERRIDES.read_text(encoding="utf-8")
                ).items() if v
            }
        except (json.JSONDecodeError, AttributeError):
            overrides = {}

    # Prior manifest tells us which slugs we fetched (auto) vs. hand-dropped (manual).
    prev_source: dict[str, str] = {}
    if paths.COMPETITION_IMAGES_MANIFEST.is_file():
        try:
            for e in json.loads(paths.COMPETITION_IMAGES_MANIFEST.read_text(encoding="utf-8")):
                prev_source[e.get("slug", "")] = e.get("source", "")
        except (json.JSONDecodeError, AttributeError):
            prev_source = {}

    payload = json.loads(paths.COMPETITION_EXTRACTED.read_text(encoding="utf-8"))
    brands = payload.get("brands", [])

    manifest: list[dict] = []
    fetched = skipped = no_can = errors = 0

    for brand in brands:
        name = (brand.get("brand_name") or "").strip()
        if not name:
            continue
        slug = _slug(name)
        pos_id = brand.get("positioning_id", "")
        category = (brand.get("category") or "").strip()
        existing = _existing_image(images_dir, slug)

        # Pinned override URL — authoritative, download it directly and skip scraping.
        if slug in overrides:
            dest = images_dir / f"{slug}.png"
            if _download_downscaled(overrides[slug], dest, args.timeout):
                manifest.append({
                    "brand": name, "slug": slug, "file": f"images/{dest.name}",
                    "positioning_id": pos_id, "source": "override",
                    "image_url": overrides[slug], "has_can": True, "reason": "pinned override",
                })
                fetched += 1
                print(f"override: {name} <- {overrides[slug]}")
            else:
                errors += 1
                print(f"error: {name}: override download failed ({overrides[slug]})")
            continue

        # A file we never recorded as auto is a manual override — keep it untouched.
        if existing is not None and prev_source.get(slug, "manual") == "manual":
            manifest.append({
                "brand": name, "slug": slug, "file": f"images/{existing.name}",
                "positioning_id": pos_id, "source": "manual", "image_url": "",
                "has_can": True, "reason": "manual override",
            })
            skipped += 1
            continue

        if existing is not None and not args.overwrite:
            manifest.append({
                "brand": name, "slug": slug, "file": f"images/{existing.name}",
                "positioning_id": pos_id, "source": prev_source.get(slug, "auto"),
                "image_url": "", "has_can": True, "reason": "kept (already fetched)",
            })
            skipped += 1
            continue

        if fetched >= args.limit:
            continue

        url = (brand.get("url") or "").strip()
        if not url:
            print(f"skip (no url): {name}")
            skipped += 1
            continue

        try:
            candidates = _candidate_urls(url, args.timeout)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"error: {name}: {exc}")
            continue

        if not candidates:
            no_can += 1
            print(f"no candidates: {name} ({url})")
            continue

        with tempfile.TemporaryDirectory() as td:
            tmp_dir = Path(td)
            tmp_files: list[Path] = []
            tmp_urls: list[str] = []
            for i, cu in enumerate(candidates):
                tf = tmp_dir / f"cand-{i}.png"
                if _download_downscaled(cu, tf, args.timeout):
                    tmp_files.append(tf)
                    tmp_urls.append(cu)
            if not tmp_files:
                errors += 1
                print(f"error: {name}: no candidate downloaded")
                continue

            if args.no_vision:
                idx, has_can, reason = 0, True, "no-vision: first candidate"
            else:
                try:
                    pick = _pick_can(client, vision_json, args.model, name, category, tmp_files)
                    idx = int(pick.get("best_index", -1))
                    has_can = bool(pick.get("has_can", False))
                    reason = pick.get("reason", "")
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    print(f"error: {name}: vision pick failed: {exc}")
                    continue

            if idx < 0 or idx >= len(tmp_files) or not has_can:
                no_can += 1
                print(f"no clear can: {name} — {reason}")
                continue

            dest = images_dir / f"{slug}.png"
            shutil.copyfile(tmp_files[idx], dest)
            manifest.append({
                "brand": name, "slug": slug, "file": f"images/{dest.name}",
                "positioning_id": pos_id, "source": "vision-can" if not args.no_vision else "og:image",
                "image_url": tmp_urls[idx], "has_can": True, "reason": reason,
            })
            fetched += 1
            print(f"fetched: {name} <- [{idx}] {tmp_urls[idx]}")

    paths.COMPETITION_IMAGES_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"\nDone. fetched={fetched} kept/skipped={skipped} no-can={no_can} errors={errors}"
        f"\nManifest: {paths.COMPETITION_IMAGES_MANIFEST.relative_to(ROOT)}"
        f"\nImages:   {images_dir.relative_to(ROOT)}"
        f"\nBrands with no clear can can be filled by hand-dropping <slug>.png into the images folder."
    )


if __name__ == "__main__":
    main()
