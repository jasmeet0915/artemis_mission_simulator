"""Normal map generation from heightmap data using Sobel gradients."""

import numpy as np
from scipy.ndimage import sobel

from ..utils.raster_utils import normalize_array


class NormalMapGenerator:
    """Derives RGB normal maps from heightmap arrays."""

    @staticmethod
    def from_heightmap(
        heightmap: np.ndarray, strength: float = 2.0
    ) -> np.ndarray:
        """
        Derive an RGB normal map from a heightmap using Sobel gradients.

        The input is automatically normalized to [0, 1] before gradient
        computation, so callers can pass raw elevation data directly.

        Args:
            heightmap: float64 elevation array, shape (H, W).
                       Does not need to be pre-normalized.
            strength: exaggeration factor for surface detail.

        Returns:
            uint8 RGB array of shape (H, W, 3) encoding surface normals.
            Convention: R=X, G=Y, B=Z mapped from [-1,1] to [0,255].
        """
        normalized = normalize_array(heightmap)

        dx = sobel(normalized, axis=1) * strength
        dy = sobel(normalized, axis=0) * strength

        normals = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
        norms = np.linalg.norm(normals, axis=-1, keepdims=True)
        normals /= np.where(norms > 0, norms, 1.0)

        normal_map = ((normals + 1.0) * 0.5 *
                      255.0).clip(0, 255).astype(np.uint8)
        return normal_map
