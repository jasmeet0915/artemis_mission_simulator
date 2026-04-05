"""Tests for slope-based diffuse texture generation."""

import numpy as np
import pytest
from pathlib import Path

from generate_lunar_sdf.map_generators.slope_texture_generator import SlopeTextureGenerator


class TestSlopeToGrayscale:
    def test_flat_surface_is_light(self):
        """Flat areas (0° slope) should map to light gray (~190)."""
        slope = np.zeros((64, 64), dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8
        assert result[0, 0, 0] == 190

    def test_steep_surface_is_dark(self):
        """Steep areas (>=45° slope) should map to dark gray (~60)."""
        slope = np.full((64, 64), 45.0, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result[0, 0, 0] == 60

    def test_clamps_above_max(self):
        """Slopes above 45° should clamp to the same dark gray as 45°."""
        slope = np.full((64, 64), 90.0, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        assert result[0, 0, 0] == 60

    def test_intermediate_slope(self):
        """Mid-range slope should produce mid-range gray."""
        slope = np.full((64, 64), 22.5, dtype=np.float64)
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        gray = result[0, 0, 0]
        assert 100 < gray < 160

    def test_rgb_channels_equal(self):
        """All 3 RGB channels should be identical (grayscale)."""
        slope = np.random.uniform(0, 30, (64, 64))
        result = SlopeTextureGenerator.slope_to_grayscale(slope)
        np.testing.assert_array_equal(result[:, :, 0], result[:, :, 1])
        np.testing.assert_array_equal(result[:, :, 0], result[:, :, 2])

    def test_monotonic_darker_with_slope(self):
        """Higher slope values should produce darker (lower) gray values."""
        slopes = [0, 10, 20, 30, 45]
        grays = []
        for s in slopes:
            arr = np.full((4, 4), float(s))
            result = SlopeTextureGenerator.slope_to_grayscale(arr)
            grays.append(int(result[0, 0, 0]))
        for i in range(len(grays) - 1):
            assert grays[i] >= grays[i + 1]


class TestFromSlopeGeotiff:
    def _make_test_slope_geotiff(self, tmp_path: Path, size: int = 64) -> Path:
        """Create a small slope GeoTIFF in south polar stereographic."""
        import rasterio
        from rasterio.transform import from_bounds

        slope_path = tmp_path / "test_slope.tif"
        transform = from_bounds(-500, -500, 500, 500, size, size)
        data = np.linspace(0.0, 30.0, size * size, dtype=np.float32).reshape(size, size)

        with rasterio.open(
            slope_path, "w", driver="GTiff", height=size, width=size,
            count=1, dtype="float32",
            crs="EPSG:3031",
            transform=transform, nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        return slope_path

    def test_full_roi_shape_and_dtype(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path)
        result = SlopeTextureGenerator.from_slope_geotiff(slope_path, 33, 33)
        assert result.shape == (33, 33, 3)
        assert result.dtype == np.uint8

    def test_full_roi_grayscale_range(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path)
        result = SlopeTextureGenerator.from_slope_geotiff(slope_path, 33, 33)
        assert result.min() >= 60
        assert result.max() <= 190

    def test_cropped_shape_and_dtype(self, tmp_path):
        slope_path = self._make_test_slope_geotiff(tmp_path, size=128)
        result = SlopeTextureGenerator.from_slope_geotiff_cropped(
            slope_path, -90.0, 0.0, 0.5, 0.5, 17, 17
        )
        assert result.shape == (17, 17, 3)
        assert result.dtype == np.uint8
