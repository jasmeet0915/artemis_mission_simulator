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


"""Tests for DEMProcessor elevation extraction from GeoTIFF DEMs."""

from pathlib import Path

from lunar_terrain_exporter.raster_processors.dem_processor import DEMProcessor
from lunar_terrain_exporter.utils.types import BoundingBox, ROI
import numpy as np
import pytest


class TestDEMProcessor:
    """Test the public extract_from_raw() interface."""

    @staticmethod
    def _make_test_geotiff(tmp_path: Path, size: int = 64) -> Path:
        """Create a small GeoTIFF in south polar stereographic with known values."""
        import rasterio
        from rasterio.transform import from_bounds

        dem_path = tmp_path / 'test_dem.tif'
        # 1km x 1km tile centered at stereo origin (south pole)
        transform = from_bounds(-500, -500, 500, 500, size, size)
        data = np.linspace(-100.0, 200.0, size * size,
                           dtype=np.float32).reshape(size, size)

        with rasterio.open(
            dem_path, 'w', driver='GTiff', height=size, width=size,
            count=1, dtype='float32',
            crs='EPSG:3031',
            transform=transform, nodata=-9999.0,
        ) as dst:
            dst.write(data, 1)
        return dem_path

    def test_returns_with_full_roi(self, tmp_path):
        """
        Test extract_from_raw with use_full=True.

        Should return elevations, range, bounds, and profile.
        """
        dem_path = self._make_test_geotiff(tmp_path)
        roi = ROI(use_full=True)
        elevations, elev_min, elev_max, bounds, dem_profile = (
            DEMProcessor.extract_from_raw(dem_path, roi)
        )

        assert elevations.ndim == 2
        assert elev_min == pytest.approx(-100.0, abs=1.0)
        assert elev_max == pytest.approx(200.0, abs=1.0)
        assert elevations.min() == pytest.approx(elev_min, abs=1.0)
        assert elevations.max() == pytest.approx(elev_max, abs=1.0)

        assert 'center_lat' in bounds
        assert 'center_lon' in bounds
        assert 'width_km' in bounds
        assert 'height_km' in bounds
        assert bounds['width_km'] == pytest.approx(1.0, abs=0.1)
        assert bounds['height_km'] == pytest.approx(1.0, abs=0.1)

        assert 'crs' in dem_profile
        assert 'transform' in dem_profile

    def test_returns_with_bounding_box(self, tmp_path):
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
        assert elev_min <= elev_max
        assert elevations.min() == pytest.approx(elev_min, abs=1.0)
        assert elevations.max() == pytest.approx(elev_max, abs=1.0)
        assert bounds['width_km'] == pytest.approx(0.5, abs=0.01)
        assert bounds['height_km'] == pytest.approx(0.5, abs=0.01)
        assert 'crs' in dem_profile
        assert 'transform' in dem_profile
