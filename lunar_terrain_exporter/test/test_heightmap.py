# Copyright 2026 Jasmeet Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Tests for heightmap generation from GeoTIFF DEMs."""

import numpy as np
import pytest
from pathlib import Path

from lunar_terrain_exporter.raster_processors.dem_processor import DEMProcessor
from lunar_terrain_exporter.utils.raster_utils import normalize_array
from lunar_terrain_exporter.utils.types import BoundingBox, ROI


class TestReadElevations:
    """Test metadata-driven elevation reading from rasterio datasets."""

    def test_float_data_no_scaling(self):
        """Float GeoTIFF data should be used as-is."""
        raw = np.array([[100.5, 200.3], [150.7, -9999.0]], dtype=np.float32)
        elevations = DEMProcessor._read_elevations(
            raw, nodata=-9999.0, scale=1.0, offset=0.0)
        assert elevations[0, 0] == pytest.approx(100.5, abs=0.1)
        assert elevations[1, 0] == pytest.approx(150.7, abs=0.1)
        assert np.isnan(elevations[1, 1])

    def test_int16_with_scale(self):
        """int16 data with scale=0.5."""
        raw = np.array([[100, 200], [300, -32768]], dtype=np.int16)
        elevations = DEMProcessor._read_elevations(
            raw, nodata=-32768, scale=0.5, offset=0.0)
        assert elevations[0, 0] == pytest.approx(50.0)
        assert elevations[0, 1] == pytest.approx(100.0)
        assert np.isnan(elevations[1, 1])

    def test_scale_and_offset(self):
        """Scale and offset should both be applied: elevation = raw * scale + offset."""
        raw = np.array([[10, 20]], dtype=np.int16)
        elevations = DEMProcessor._read_elevations(
            raw, nodata=None, scale=2.0, offset=100.0)
        assert elevations[0, 0] == pytest.approx(120.0)
        assert elevations[0, 1] == pytest.approx(140.0)

    def test_no_nodata(self):
        """When nodata is None, no pixels should become NaN."""
        raw = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        elevations = DEMProcessor._read_elevations(
            raw, nodata=None, scale=1.0, offset=0.0)
        assert not np.any(np.isnan(elevations))


class TestNormalizeArray:
    """Test normalization to 0-1 range."""

    def test_normalize_range(self):
        data = np.array([[100.0, 200.0], [150.0, 300.0]])
        normalized = normalize_array(data)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_normalize_flat_surface(self):
        data = np.full((10, 10), 42.0)
        normalized = normalize_array(data)
        assert np.all(normalized == 0.0)


class TestFromDem:
    """Test reading a DEM tile via the unified extract_from_raw() interface."""

    @staticmethod
    def _make_test_geotiff(tmp_path: Path, size: int = 64) -> Path:
        """Create a small GeoTIFF in south polar stereographic with known values."""
        import rasterio
        from rasterio.transform import from_bounds

        dem_path = tmp_path / "test_dem.tif"
        # 1km x 1km tile centered at stereo origin (south pole)
        transform = from_bounds(-500, -500, 500, 500, size, size)
        data = np.linspace(-100.0, 200.0, size * size,
                           dtype=np.float32).reshape(size, size)

        with rasterio.open(
            dem_path, "w", driver="GTiff", height=size, width=size,
            count=1, dtype="float32",
            crs="EPSG:3031",
            transform=transform, nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        return dem_path

    def test_full_roi_returns_elevations_and_bounds(self, tmp_path):
        """extract_from_raw with use_full=True should return elevations, range, bounds, and profile."""
        dem_path = self._make_test_geotiff(tmp_path)
        roi = ROI(use_full=True)
        elevations, elev_min, elev_max, bounds, dem_profile = (
            DEMProcessor.extract_from_raw(dem_path, roi)
        )

        assert elevations.ndim == 2
        # Raw elevations are NOT normalized — values should span the input range
        assert elev_min == pytest.approx(-100.0, abs=1.0)
        assert elev_max == pytest.approx(200.0, abs=1.0)
        assert elevations.min() == pytest.approx(elev_min, abs=1.0)
        assert elevations.max() == pytest.approx(elev_max, abs=1.0)

        assert "center_lat" in bounds
        assert "center_lon" in bounds
        assert "width_km" in bounds
        assert "height_km" in bounds
        assert bounds["width_km"] == pytest.approx(1.0, abs=0.1)
        assert bounds["height_km"] == pytest.approx(1.0, abs=0.1)

        assert "crs" in dem_profile
        assert "transform" in dem_profile

    def test_bounding_box_roi_returns_elevations(self, tmp_path):
        """extract_from_raw with a bounding box ROI should crop and return elevations."""
        dem_path = self._make_test_geotiff(tmp_path, size=128)
        roi = ROI(
            use_full=False,
            bounding_box=BoundingBox(lat=-90.0, lon=0.0,
                                     width_km=0.5, height_km=0.5),
        )
        elevations, elev_min, elev_max, bounds, dem_profile = (
            DEMProcessor.extract_from_raw(dem_path, roi)
        )

        assert elevations.ndim == 2
        assert bounds["width_km"] == pytest.approx(0.5, abs=0.01)
        assert bounds["height_km"] == pytest.approx(0.5, abs=0.01)
        assert "crs" in dem_profile
        assert "transform" in dem_profile
