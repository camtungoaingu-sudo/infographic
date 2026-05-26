from __future__ import annotations

from pathlib import Path

from .color_quantizer import quantize_image
from .region_extractor import build_mask, extract_contours
from .vector_builder import build_svg


def export_svg_from_rgba(rgba, out_svg: str, k: int = 10):
    label_map, palette = quantize_image(rgba, k=k)
    contours = {}
    for label in range(palette.shape[0]):
        mask = build_mask(label_map, label)
        contours[label] = extract_contours(mask)
    Path(out_svg).parent.mkdir(parents=True, exist_ok=True)
    build_svg(label_map, palette, contours, out_svg)
    return out_svg
