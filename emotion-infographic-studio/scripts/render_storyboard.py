#!/usr/bin/env python3
"""
render_storyboard.py
Nhận file HTML storyboard → xuất file PNG full-resolution.
Usage: python3 render_storyboard.py input.html output.png [--width 1400]
"""

import argparse
from playwright.sync_api import sync_playwright


def html_to_png(html_path: str, png_path: str, width: int = 1400):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})

        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        page.set_content(html_content, wait_until="networkidle")

        # Auto-detect full page height
        full_height = page.evaluate("document.body.scrollHeight")
        page.set_viewport_size({"width": width, "height": full_height})

        page.screenshot(path=png_path, full_page=True)
        browser.close()
        print(f"Saved: {png_path} ({width}x{full_height}px)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("html", help="Input HTML file")
    parser.add_argument("png", help="Output PNG file")
    parser.add_argument("--width", type=int, default=1400)
    args = parser.parse_args()
    html_to_png(args.html, args.png, args.width)
