"""Slope-based diffuse texture generation from PGDA Product 78 slope GeoTIFFs.

Maps slope values (degrees) to grayscale: flat areas appear light gray
(accumulated regolith), steep areas appear dark gray (exposed rock).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_MAX_SLOPE_DEG = 45.0
_GRAY_FLAT = 190
_GRAY_STEEP = 60


class SlopeTextureGenerator:
    """Generates grayscale diffuse textures from PGDA-78 slope GeoTIFFs."""

    @staticmethod
    def slope_to_grayscale(slope_deg: np.ndarray) -> np.ndarray:
        """Map slope values (degrees) to grayscale RGB.

        Flat (0°) → 190, steep (≥45°) → 60.
        Returns uint8 RGB array (H, W, 3).
        """
        clamped = np.clip(slope_deg, 0.0, _MAX_SLOPE_DEG)
        normalized = clamped / _MAX_SLOPE_DEG
        gray = (_GRAY_FLAT - normalized * (_GRAY_FLAT - _GRAY_STEEP)).astype(np.uint8)
        return np.stack([gray, gray, gray], axis=-1)

    @staticmethod
    def from_slope_geotiff(
        slope_path: Path,
        target_height: int,
        target_width: int,
    ) -> np.ndarray:
        """Read full slope GeoTIFF and resample to target dimensions.

        Returns uint8 RGB array (target_height, target_width, 3).
        """
        import rasterio
        from rasterio.enums import Resampling

        with rasterio.open(slope_path) as src:
            slope = src.read(
                1,
                out_shape=(target_height, target_width),
                resampling=Resampling.bilinear,
            )
            nodata = src.nodata

        slope = slope.astype(np.float64)
        if nodata is not None:
            slope[np.isclose(slope, float(nodata))] = 0.0

        return SlopeTextureGenerator.slope_to_grayscale(slope)

    @staticmethod
    def from_slope_geotiff_cropped(
        slope_path: Path,
        lat: float,
        lon: float,
        width_km: float,
        height_km: float,
        target_height: int,
        target_width: int,
    ) -> np.ndarray:
        """Crop slope GeoTIFF to bounding box and resample.

        Uses the same polar stereographic projection as HeightmapGenerator.

        Returns uint8 RGB array (target_height, target_width, 3).
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling
        from .heightmap_generator import HeightmapGenerator

        x_center, y_center = HeightmapGenerator.latlon_to_stereo(lat, lon)
        half_w = width_km * 1000.0 / 2.0
        half_h = height_km * 1000.0 / 2.0

        with rasterio.open(slope_path) as src:
            window = from_bounds(
                x_center - half_w, y_center - half_h,
                x_center + half_w, y_center + half_h,
                src.transform,
            )
            slope = src.read(
                1,
                window=window,
                out_shape=(target_height, target_width),
                resampling=Resampling.bilinear,
            )
            nodata = src.nodata

        slope = slope.astype(np.float64)
        if nodata is not None:
            slope[np.isclose(slope, float(nodata))] = 0.0

        return SlopeTextureGenerator.slope_to_grayscale(slope)
