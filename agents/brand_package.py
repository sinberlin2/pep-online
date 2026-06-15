"""
Assemble **brand package(s)** — outputs of the branding module.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import paths  # noqa: E402

FLOW_A_DIRECTIONS = ["functional-protein", "lifestyle", "social"]
DIRECTION_LABELS = {
    "functional-protein": "Functional protein",
    "lifestyle": "Lifestyle / wellness",
    "social": "Social",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def design_concept_slugs() -> list[str]:
    if not paths.PROVIDED.is_dir():
        return []
    return sorted(
        p.name
        for p in paths.PROVIDED.iterdir()
        if p.is_dir() and (p / "meta.json").is_file()
    )


def build_design_system_from_direction(positioning: dict[str, Any]) -> dict[str, Any]:
    visual = positioning.get("visual", {})
    return {
        "version": 1,
        "source": "from positioning.visual (Flow A — invented look)",
        "colors": {},
        "typography": {},
        "mood": visual.get("mood", ""),
        "photography": visual.get("photography", ""),
        "typographyDirection": visual.get("typography", ""),
        "rejectLooks": visual.get("rejectLooks", []),
    }


def build_design_system_from_extracted(extracted: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": extracted.get("version", 1),
        "source": extracted.get("source", "extracted from design concept (Flow B)"),
        "extractedFrom": extracted.get("extractedFrom"),
        "colors": extracted.get("colors", {}),
        "typography": extracted.get("typography", {}),
        "mood": extracted.get("mood", ""),
        "photography": extracted.get("photography", ""),
        "typographyDirection": extracted.get("typographyDirection", ""),
        "rejectLooks": extracted.get("rejectLooks", []),
    }


def build_manifest(
    *,
    slug: str,
    label: str,
    kind: str,
    source: str | None,
    product: dict[str, Any],
    positioning: dict[str, Any],
    design_system: dict[str, Any],
    positioning_path: Path | None,
    design_system_path: Path,
    guidelines_path: Path | None,
) -> dict[str, Any]:
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    has_strategy = bool(positioning)
    return {
        "slug": slug,
        "label": label,
        "kind": kind,
        "source": source,
        "brand": positioning.get("brand", product.get("name", "")),
        "domain": positioning.get("domain", ""),
        "version": 1,
        "assembledAt": datetime.now(timezone.utc).isoformat(),
        "strategyStatus": "ready" if has_strategy else "pending (Flow B extraction)",
        "summary": {
            "name": positioning.get("brand", product.get("name", "")),
            "tagline": positioning.get("voice", {}).get("tagline", product.get("tagline", "")),
            "oneLiner": positioning.get("oneLiner", ""),
            "positioningStatement": positioning.get("positioningStatement", ""),
            "primaryColors": [
                v for k, v in colors.items() if k in ("green", "orange", "cream")
            ],
            "fonts": {
                "logo": typography.get("logo", {}).get("family", ""),
                "body": typography.get("labels", {}).get("family", ""),
                "script": typography.get("script", {}).get("family", ""),
            },
        },
        "parts": {
            "positioning": _rel(positioning_path) if positioning_path and positioning_path.is_file() else None,
            "designSystem": _rel(design_system_path),
            "guidelines": _rel(guidelines_path) if guidelines_path and guidelines_path.is_file() else None,
        },
    }


def assemble_direction(
    *,
    slug: str,
    label: str,
    out_dir: Path,
    positioning_path: Path,
    guidelines_path: Path | None,
) -> dict[str, Any]:
    product = _read_json(paths.PRODUCT_PROFILE)
    positioning = _read_json(positioning_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    design_system = build_design_system_from_direction(positioning)
    ds_path = out_dir / "design-system.json"
    ds_path.write_text(
        json.dumps(design_system, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    manifest = build_manifest(
        slug=slug,
        label=label,
        kind="from-direction",
        source=_rel(paths.DIRECTIONS / slug),
        product=product,
        positioning=positioning,
        design_system=design_system,
        positioning_path=positioning_path,
        design_system_path=ds_path,
        guidelines_path=guidelines_path,
    )
    (out_dir / "brand-package.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def assemble_from_design(design_slug: str) -> dict[str, Any]:
    concept_dir = paths.PROVIDED / design_slug
    meta = _read_json(concept_dir / "meta.json")
    label = meta.get("label", design_slug)
    out_dir = paths.PROVIDED / design_slug / "extracted"
    concept_rel = _rel(concept_dir)
    product = _read_json(paths.PRODUCT_PROFILE)

    ds_path = out_dir / "design-system.json"
    extracted = _read_json(ds_path)
    if not extracted.get("colors"):
        extracted = {
            "version": 1,
            "source": "pending extraction from design concept (Flow B)",
            "extractedFrom": concept_rel,
            "colors": {},
            "typography": {},
        }
    design_system = build_design_system_from_extracted(extracted)

    key_images = [
        concept_dir / "marketing" / "originals" / "pep-flyer.png",
        concept_dir / "marketing" / "originals" / "design-reference-full.png",
        concept_dir / "product" / "bg_removed" / "pep-can-glass-lockup.png",
    ]
    sources = [_rel(p) for p in key_images if p.is_file()]

    source_md = [
        f"# From design — `{design_slug}`",
        "",
        f"**Input:** `{concept_rel}/`",
        f"**Output:** `{_rel(out_dir)}/`",
        "",
        "Generic company facts: `company/product-profile.json`.",
        "Logo/typography/colours are exploratory — part of this design concept.",
        "",
        "## Key design images",
        "",
    ]
    source_md += [f"- `{s}`" for s in sources] or ["- (none)"]
    source_md += [
        "",
        "## Folders",
        f"- `{concept_rel}/identity/`",
        f"- `{concept_rel}/marketing/`",
        f"- `{concept_rel}/product/`",
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    ds_path.write_text(
        json.dumps(design_system, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "source.md").write_text("\n".join(source_md) + "\n", encoding="utf-8")

    pos_path = out_dir / "positioning.json"
    positioning = _read_json(pos_path) if pos_path.is_file() else {}
    guidelines_path = out_dir / "brand-guidelines.md"

    manifest = build_manifest(
        slug=design_slug,
        label=label,
        kind="from-design",
        source=concept_rel,
        product=product,
        positioning=positioning,
        design_system=design_system,
        positioning_path=pos_path if pos_path.is_file() else None,
        design_system_path=ds_path,
        guidelines_path=guidelines_path if guidelines_path.is_file() else None,
    )
    (out_dir / "brand-package.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def active_slug() -> str:
    # No active folder anymore; company/choice.json is just an optional "selected
    # direction" pointer used for cosmetic flagging in the index.
    return _read_json(paths.CHOICE).get("positioningSlug", "")


def run(*, direction: str, design: str | None) -> None:
    active = active_slug()
    index: list[dict[str, Any]] = []

    if design:
        targets_design = [design]
        targets_direction = []
    elif direction == "all":
        targets_direction = FLOW_A_DIRECTIONS
        targets_design = design_concept_slugs()
    else:
        targets_direction = [direction] if direction in FLOW_A_DIRECTIONS else []
        targets_design = []

    for slug in targets_direction:
        pkg_dir = paths.direction_package(slug)
        manifest = assemble_direction(
            slug=slug,
            label=DIRECTION_LABELS[slug],
            out_dir=pkg_dir,
            positioning_path=paths.direction_strategy(slug) / "positioning.json",
            guidelines_path=paths.direction_strategy(slug) / "brand-guidelines.md",
        )
        flag = "  <== ACTIVE" if slug == active else ""
        print(f"  [from-direction] {slug}{flag}")
        index.append(
            {
                "slug": slug,
                "label": manifest["label"],
                "kind": manifest["kind"],
                "source": manifest["source"],
                "active": slug == active,
                "strategyStatus": manifest["strategyStatus"],
                "package": _rel(pkg_dir / "brand-package.json"),
            }
        )

    for design_slug in targets_design:
        manifest = assemble_from_design(design_slug)
        print(f"  [from-design   ] {design_slug}")
        index.append(
            {
                "slug": design_slug,
                "label": manifest["label"],
                "kind": manifest["kind"],
                "source": manifest["source"],
                "active": False,
                "strategyStatus": manifest["strategyStatus"],
                "package": _rel(paths.PROVIDED / design_slug / "extracted" / "brand-package.json"),
            }
        )

    if direction == "all" and not design:
        paths.BRANDINGS_INDEX.write_text(
            json.dumps(
                {
                    "activeSlug": active,
                    "assembledAt": datetime.now(timezone.utc).isoformat(),
                    "brandings": index,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"  index -> {_rel(paths.BRANDINGS_INDEX)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble brand package(s)")
    parser.add_argument("--direction", default="all", choices=["all", *FLOW_A_DIRECTIONS])
    parser.add_argument("--design", default=None)
    args = parser.parse_args()
    print("Assembling brand package(s):")
    run(direction=args.direction, design=args.design)


if __name__ == "__main__":
    main()
