"""
Hand-off: copy the ACTIVE brand's approved images into site/public/.

The website (site/) only ever reads from site/public/ — it never reaches into brand/.
This is the one-way boundary: pick the assets to publish in site-assets-map.json, run
`npm run site:sync`, and the chosen images are copied into site/public/.

`{active}` in a `from` path expands to brand/directions/<activeSlug>, where activeSlug
comes from brand/brandings.json.

Usage:
  python scripts/publish_site_assets.py
  python scripts/publish_site_assets.py --slug social   # override the active direction

Inputs:
  site-assets-map.json          list of {from, to}
  brand/brandings.json          activeSlug
Outputs:
  site/public/<to>              copied assets
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import paths  # noqa: E402

MAP_PATH = ROOT / "site-assets-map.json"
SITE_PUBLIC = ROOT / "site" / "public"


def _active_slug(override: str | None) -> str | None:
    if override:
        return override
    if paths.BRANDINGS_INDEX.is_file():
        try:
            return json.loads(paths.BRANDINGS_INDEX.read_text(encoding="utf-8")).get("activeSlug")
        except (json.JSONDecodeError, AttributeError):
            return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy active brand assets into site/public/")
    parser.add_argument("--slug", default=None, help="Override the active direction slug")
    args = parser.parse_args()

    if not MAP_PATH.is_file():
        raise SystemExit(f"Missing {MAP_PATH.name}")
    assets = json.loads(MAP_PATH.read_text(encoding="utf-8")).get("assets", [])
    slug = _active_slug(args.slug)
    active_dir = paths.DIRECTIONS / slug if slug else None

    copied = missing = 0
    for entry in assets:
        frm = entry.get("from", "")
        to = entry.get("to", "")
        if not frm or not to:
            continue
        if "{active}" in frm:
            if not active_dir:
                print(f"skip (no active slug): {frm}")
                missing += 1
                continue
            frm = frm.replace("{active}", str(active_dir.relative_to(ROOT)).replace("\\", "/"))
        src = ROOT / frm
        dst = SITE_PUBLIC / to
        if not src.is_file():
            print(f"missing: {frm}")
            missing += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        copied += 1
        print(f"synced: {frm} -> site/public/{to}")

    print(f"\nDone. active={slug or '(none)'}  copied={copied}  missing={missing}")


if __name__ == "__main__":
    main()
