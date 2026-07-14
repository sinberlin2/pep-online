"""
Remove backgrounds from brand assets using rembg.

Processes external-design folders:
  brand/inputs/external-designs/<slug>/{identity,marketing,product}/originals/

Skips full-scene assets that should keep their background (flyers, backgrounds, templates).
"""

from pathlib import Path

from rembg import remove

ROOT = Path(__file__).resolve().parents[1]
DESIGN_CONCEPTS = ROOT / "brand" / "inputs" / "external-designs"

SKIP_STEMS = frozenset(
    {
        "hero-background",
        "pep-flyer",
        "template-podium",
        "flavours-lineup",
        "design-reference-full",
    }
)


def output_name(stem: str) -> str:
    if stem.endswith("-background-removed"):
        return f"{stem}.png"
    if stem.endswith("-transparent"):
        return f"{stem.replace('-transparent', '')}-background-removed.png"
    return f"{stem}-background-removed.png"


def process_folder(originals: Path, outputs: Path, label: str) -> int:
    outputs.mkdir(parents=True, exist_ok=True)
    if not originals.is_dir():
        print(f"Skip {label}: no originals folder")
        return 0

    count = 0
    for src in sorted(originals.glob("*.png")):
        stem = src.stem.lower()
        if stem in SKIP_STEMS:
            print(f"  skip (full scene): {src.name}")
            continue
        dst = outputs / output_name(src.stem)
        print(f"  {label}: {src.name} -> {dst.name}")
        dst.write_bytes(remove(src.read_bytes()))
        count += 1
    return count


def main() -> None:
    total = 0
    if not DESIGN_CONCEPTS.is_dir():
        print("No external-designs folder")
        return

    for concept in sorted(DESIGN_CONCEPTS.iterdir()):
        if not concept.is_dir() or not (concept / "meta.json").is_file():
            continue
        for category in ("identity", "marketing", "product"):
            originals = concept / category / "originals"
            if not originals.is_dir():
                continue
            print(f"\n[{concept.name}/{category}]")
            total += process_folder(
                originals,
                concept / category / "bg_removed",
                f"{concept.name}/{category}",
            )

    print(f"\nDone. Processed {total} image(s).")


if __name__ == "__main__":
    main()
