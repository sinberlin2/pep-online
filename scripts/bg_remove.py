"""
Remove backgrounds from brand assets using rembg.

Reads PNGs from brand/{identity,marketing,product}/originals/
Writes to brand/{category}/bg_removed/{stem}-background-removed.png

Skips full-scene assets that should keep their background (flyers, backgrounds, templates).
"""

from pathlib import Path

from rembg import remove

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand"
CATEGORIES = ("identity", "marketing", "product")

# Basenames to skip (full posters, backgrounds, layout mockups)
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


def process_category(category: str) -> int:
    originals = BRAND / category / "originals"
    outputs = BRAND / category / "bg_removed"
    outputs.mkdir(parents=True, exist_ok=True)

    if not originals.is_dir():
        print(f"Skip {category}: no originals folder")
        return 0

    files = sorted(originals.glob("*.png"))
    count = 0

    for src in files:
        stem = src.stem.lower()
        if stem in SKIP_STEMS:
            print(f"  skip (full scene): {src.name}")
            continue

        dst = outputs / output_name(src.stem)
        print(f"  {category}: {src.name} -> {dst.name}")
        dst.write_bytes(remove(src.read_bytes()))
        count += 1

    return count


def main() -> None:
    total = 0
    for category in CATEGORIES:
        print(f"\n[{category}]")
        total += process_category(category)
    print(f"\nDone. Processed {total} image(s).")


if __name__ == "__main__":
    main()
