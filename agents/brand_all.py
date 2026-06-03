"""
Generate brand outputs for all 3 product directions.

Usage:
  python -m agents.brand_all
  python -m agents.brand_all --set-active 2
"""
from __future__ import annotations

import argparse
import os

from agents.brand_run import run_brand


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate brand packs for 1/2/3 directions")
    parser.add_argument(
        "--model",
        default=os.environ.get("CONCEPT_AGENT_MODEL", "gpt-4.1"),
        help="Model for brand generation",
    )
    parser.add_argument(
        "--set-active",
        choices=["1", "2", "3"],
        help="After generating all directions, set active brand to this id.",
    )
    args = parser.parse_args()

    print("Generating direction: 1 (functional-protein)")
    run_brand(positioning_arg="1", model=args.model, set_active=False)
    print("Generating direction: 2 (lifestyle)")
    run_brand(positioning_arg="2", model=args.model, set_active=False)
    print("Generating direction: 3 (social)")
    run_brand(positioning_arg="3", model=args.model, set_active=False)

    if args.set_active:
        print(f"Setting active to: {args.set_active}")
        run_brand(positioning_arg=args.set_active, model=args.model, set_active=True)

    print("\nDone.")
    print("Direction outputs:")
    print("  brand/research/directions/functional-protein/")
    print("  brand/research/directions/lifestyle/")
    print("  brand/research/directions/social/")


if __name__ == "__main__":
    main()

