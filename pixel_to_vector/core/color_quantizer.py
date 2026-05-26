from __future__ import annotations

import numpy as np
from skimage import color
from sklearn.cluster import KMeans


def rgba_to_rgb_white(rgba: np.ndarray) -> np.ndarray:
    if rgba.shape[-1] == 3:
        return rgba.astype(np.uint8)
    rgb = rgba[..., :3].astype(np.float32)
    alpha = (rgba[..., 3:4].astype(np.float32) / 255.0)
    white = np.full_like(rgb, 255.0)
    comp = rgb * alpha + white * (1.0 - alpha)
    return np.clip(comp, 0, 255).astype(np.uint8)


def quantize_image(rgba: np.ndarray, k: int = 10, random_state: int = 42):
    rgb = rgba_to_rgb_white(rgba)
    rgb_norm = rgb.astype(np.float32) / 255.0
    lab = color.rgb2lab(rgb_norm)
    h, w, _ = lab.shape
    pixels = lab.reshape(-1, 3)

    km = KMeans(n_clusters=max(2, int(k)), n_init=10, random_state=random_state)
    labels = km.fit_predict(pixels)
    centers_lab = km.cluster_centers_

    centers_rgb = color.lab2rgb(centers_lab[np.newaxis, :, :])[0]
    centers_rgb = np.clip(centers_rgb * 255.0, 0, 255).astype(np.uint8)
    label_map = labels.reshape(h, w)
    return label_map, centers_rgb
