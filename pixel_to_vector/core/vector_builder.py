from __future__ import annotations

import numpy as np
import svgwrite


def contour_to_path(contour: np.ndarray) -> str:
    if contour.shape[0] < 3:
        return ""
    cmds = [f"M {contour[0,1]:.3f} {contour[0,0]:.3f}"]
    for p in contour[1:]:
        cmds.append(f"L {p[1]:.3f} {p[0]:.3f}")
    cmds.append("Z")
    return " ".join(cmds)


def build_svg(label_map, palette_rgb, contours_by_label, out_path: str):
    h, w = label_map.shape
    dwg = svgwrite.Drawing(out_path, size=(w, h), profile="tiny")
    dwg.viewbox(0, 0, w, h)

    for idx, contours in contours_by_label.items():
        fill = f"rgb({palette_rgb[idx,0]},{palette_rgb[idx,1]},{palette_rgb[idx,2]})"
        group = dwg.g(id=f"layer_{idx}", fill=fill, stroke="none")
        for c in contours:
            path_d = contour_to_path(c)
            if path_d:
                group.add(dwg.path(d=path_d, fill_rule="evenodd"))
        dwg.add(group)

    dwg.save()
