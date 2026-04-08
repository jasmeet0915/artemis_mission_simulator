"""Raster / array utilities shared across map generators."""

from __future__ import annotations

import numpy as np


def normalize_array(data: np.ndarray) -> np.ndarray:
    """Min-max normalize an array to [0, 1]. NaN values become 0.

    Args:
        data: Input array (any shape). NaN pixels are replaced with
              the array minimum before normalisation so they map to 0.

    Returns:
        float64 array in [0, 1].  If the array is flat (max == min)
        the result is all zeros.
    """
    data = np.nan_to_num(
        data,
        nan=np.nanmin(data) if not np.all(np.isnan(data)) else 0.0,
    )
    vmin = float(np.min(data))
    vmax = float(np.max(data))
    if vmax > vmin:
        return (data - vmin) / (vmax - vmin)
    return np.zeros_like(data, dtype=np.float64)
