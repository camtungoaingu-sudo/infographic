from __future__ import annotations

import numpy as np
from skimage import measure, morphology


def build_mask(label_map: np.ndarray, label: int, min_area: int = 4) -> np.ndarray:
    mask = label_map == label
    mask = morphology.remove_small_objects(mask, min_size=min_area)
    mask = morphology.remove_small_holes(mask, area_threshold=min_area)
    return mask


def extract_contours(mask: np.ndarray):
    # march along half-pixel boundaries
    return measure.find_contours(mask.astype(float), 0.5)
