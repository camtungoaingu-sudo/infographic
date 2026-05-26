from __future__ import annotations

import numpy as np
from PIL import Image


def load_rgba(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGBA"))
