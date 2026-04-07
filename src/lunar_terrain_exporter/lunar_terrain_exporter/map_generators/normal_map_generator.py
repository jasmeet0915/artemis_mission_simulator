"""Normal map generation from heightmap data using Sobel gradients."""

import numpy as np
from scipy.ndimage import sobel


class NormalMapGenerator:
    """Derives RGB normal maps from heightmap arrays."""

    @staticmethod
    def from_heightmap(
        heightmap: np.ndarray, strength: float = 2.0
    ) -> np.ndarray:
        """
        Derive an RGB normal map from a heightmap using Sobel gradients.

        Args:
            heightmap: float64 array in [0, 1], shape (H, W).
            strength: exaggeration factor for surface detail.

        Returns:
            uint8 RGB array of shape (H, W, 3) encoding surface normals.
            Convention: R=X, G=Y, B=Z mapped from [-1,1] to [0,255].
        """
        dx = sobel(heightmap, axis=1) * strength
        dy = sobel(heightmap, axis=0) * strength

        normals = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
        norms = np.linalg.norm(normals, axis=-1, keepdims=True)
        normals /= np.where(norms > 0, norms, 1.0)

        normal_map = ((normals + 1.0) * 0.5 *
                      255.0).clip(0, 255).astype(np.uint8)
        return normal_map
