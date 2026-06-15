"""
Generate brand outputs for all 3 product directions.

Usage:
  python -m agents.brand_all
"""
from __future__ import annotations

import argparse
import os

from agents.brand_run import run_brand


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate brand packs for 1/2/3 directions")
    parser.add_argument(
        "--model",
        default=None,
        help="Model override (default per provider)",
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("BRAND_PROVIDER", "openai"),
        choices=["openai", "anthropic"],
    )
    args = parser.parse_args()

    print(f"Provider: {args.provider}")
    print("Generating direction: 1 (functional-protein)")
    run_brand(positioning_arg="1", model=args.model, provider=args.provider)
    print("Generating direction: 2 (lifestyle)")
    run_brand(positioning_arg="2", model=args.model, provider=args.provider)
    print("Generating direction: 3 (social)")
    run_brand(positioning_arg="3", model=args.model, provider=args.provider)

    print("\nDone.")
    print("Direction outputs:")
    print("  brand/directions/functional-protein/")
    print("  brand/directions/lifestyle/")
    print("  brand/directions/social/")
    print("\nRun: npm run brand:package")


if __name__ == "__main__":
    main()

