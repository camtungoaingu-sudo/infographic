#!/usr/bin/env python3
"""Render storyboard PNG from a JSON data file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_storyboard import generate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render storyboard data JSON to PNG.")
    parser.add_argument("data_json", help="Storyboard data JSON path")
    parser.add_argument("output_png", help="Output PNG path")
    parser.add_argument("--product-image", help="Override data.product_image")
    parser.add_argument("--hero-circle-image", help="Override data.hero_circle_image")
    parser.add_argument("--width", type=int, default=1400)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_json)
    output_path = Path(args.output_png)

    with data_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if args.product_image:
        data["product_image"] = str(Path(args.product_image).resolve())
        data.setdefault("hero_circle_image", data["product_image"])
    if args.hero_circle_image:
        data["hero_circle_image"] = str(Path(args.hero_circle_image).resolve())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate(data, str(output_path), width=args.width)


if __name__ == "__main__":
    main()
