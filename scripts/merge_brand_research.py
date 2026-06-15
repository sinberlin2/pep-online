"""
Merge positioning + competition into one markdown bundle for brand_run.

Usage:
  python scripts/merge_brand_research.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paths  # noqa: E402


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def _load_csv_rows() -> list[dict[str, str]]:
    if not paths.CHARACTERISTICS_CSV.is_file():
        return []
    with paths.CHARACTERISTICS_CSV.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _section_csv(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "_No characteristics.csv yet — run extract + enrich._\n"

    lines = [
        "## Competition: brand characteristics\n",
        f"_{len(rows)} rows from company/competition/characteristics.csv_\n",
    ]
    for row in rows:
        name = row.get("brand_name", "").strip() or "(unnamed)"
        pid = row.get("positioning_id", "?")
        cat = row.get("category", "")
        lines.append(f"### {name} (positioning={pid}, type={cat})\n")
        for key in (
            "url", "positioning_name", "lane", "use_cases", "adjectives",
            "visual_design_notes", "product_traits", "why_in_or_out",
        ):
            val = (row.get(key) or "").strip()
            if val:
                lines.append(f"- **{key}:** {val}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = _load_csv_rows()
    board_notes = _read_optional(paths.POSITIONING / "notes.md")
    board_links = _read_optional(paths.POSITIONING / "link.txt")
    user_research = _read_optional(paths.COMPANY / "USER-RESEARCH.md")
    board_png = list(paths.POSITIONING.glob("*.png")) if paths.POSITIONING.is_dir() else []

    parts = [
        "# PEP research bundle (for brand agent)\n",
        "_Auto-generated. Re-run after updating company/ inputs._\n",
        "---\n",
        "## Positioning board (optional PNG/notes)\n",
    ]
    if board_links:
        parts.append("**Links:**\n")
        for line in board_links.splitlines():
            if line.strip():
                parts.append(f"- {line.strip()}")
        parts.append("")
    if board_png:
        for p in sorted(board_png):
            parts.append(f"- `{p.relative_to(ROOT).as_posix()}`")
        parts.append("")
    if board_notes:
        parts.append(board_notes + "\n")

    options = _read_optional(paths.POSITIONING_OPTIONS)
    parts.append("---\n## Positioning options (3 directions)\n")
    parts.append(
        f"_From company/positioning-options.json_\n\n```json\n{options}\n```\n"
        if options
        else "_Run parse_positioning_options.py._\n"
    )
    parts.append("---\n")
    parts.append(_section_csv(rows))
    parts.append("---\n## Manual notes (USER-RESEARCH.md)\n")
    parts.append(user_research or "_Empty._\n")

    paths.RESEARCH_BUNDLE.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {paths.RESEARCH_BUNDLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
