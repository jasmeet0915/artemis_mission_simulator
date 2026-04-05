"""Tests for heightmap generation with polar stereographic projection."""

import numpy as np
import pytest
from pathlib import Path

from lunar_terrain_exporter.map_generators.heightmap_generator import HeightmapGenerator


class TestPolarStereographicConversion:
    """Test the lat/lon to polar stereographic coordinate conversion."""

    def test_south_pole_maps_to_origin(self):
        """The south pole (-90, 0) should map to (0, 0) in polar stereo."""
        x, y = HeightmapGenerator.latlon_to_stereo(-90.0, 0.0)
        assert abs(x) < 1.0  # within 1 meter of origin
        assert abs(y) < 1.0

    def test_south_pole_any_longitude(self):
        """Any longitude at -90 lat should map near the origin."""
        x, y = HeightmapGenerator.latlon_to_stereo(-90.0, 45.0)
        assert abs(x) < 1.0
        assert abs(y) < 1.0

    def test_known_offset_from_pole(self):
        """A point at -85 lat, 0 lon should be ~150km from pole.

        At -85°, the colatitude is 5°. On the Moon (R=1737.4km):
        polar stereo distance = 2R * tan(colat/2) ≈ 2*1737400*tan(2.5°)
        ≈ 2*1737400*0.04366 ≈ 151,700 m
        The point should be along the +Y axis (lon=0).
        """
        x, y = HeightmapGenerator.latlon_to_stereo(-85.0, 0.0)
        distance = np.sqrt(x**2 + y**2)
        assert 140_000 < distance < 165_000  # ~151.7 km
        assert abs(x) < 1000  # mostly along Y axis

    def test_longitude_rotates_position(self):
        """Different longitudes at same latitude should give different x,y
        but same distance from origin."""
        x1, y1 = HeightmapGenerator.latlon_to_stereo(-85.0, 0.0)
        x2, y2 = HeightmapGenerator.latlon_to_stereo(-85.0, 90.0)
        d1 = np.sqrt(x1**2 + y1**2)
        d2 = np.sqrt(x2**2 + y2**2)
        assert abs(d1 - d2) < 100  # same distance
        assert abs(x1 - x2) > 10_000  # different positions


class TestInversePolarStereographic:
    """Test the polar stereographic (x, y) to lat/lon conversion."""

    def test_origin_maps_to_south_pole(self):
        """(0, 0) in stereo should map back to -90 lat."""
        lat, lon = HeightmapGenerator.stereo_to_latlon(0.0, 0.0)
        assert lat == pytest.approx(-90.0, abs=0.01)

    def test_roundtrip_known_point(self):
        """latlon_to_stereo then stereo_to_latlon should return the original coords."""
        orig_lat, orig_lon = -85.0, 45.0
        x, y = HeightmapGenerator.latlon_to_stereo(orig_lat, orig_lon)
        lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
        assert lat == pytest.approx(orig_lat, abs=0.01)
        assert lon == pytest.approx(orig_lon, abs=0.01)

    def test_roundtrip_near_pole(self):
        """Roundtrip for a point very near the south pole."""
        orig_lat, orig_lon = -89.5, -60.0
        x, y = HeightmapGenerator.latlon_to_stereo(orig_lat, orig_lon)
        lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
        assert lat == pytest.approx(orig_lat, abs=0.01)
        assert lon == pytest.approx(orig_lon, abs=0.1)

    def test_roundtrip_multiple_longitudes(self):
        """Roundtrip across different longitudes."""
        for orig_lon in [-180.0, -90.0, 0.0, 90.0, 130.0]:
            x, y = HeightmapGenerator.latlon_to_stereo(-87.0, orig_lon)
            lat, lon = HeightmapGenerator.stereo_to_latlon(x, y)
            assert lat == pytest.approx(-87.0, abs=0.01)
            # Normalize longitude comparison to [-180, 180]
            diff = (lon - orig_lon + 180) % 360 - 180
            assert abs(diff) < 0.1


class TestReadElevations:
    """Test metadata-driven elevation reading from rasterio datasets."""

    def test_float_data_no_scaling(self):
        """Float GeoTIFF data should be used as-is."""
        raw = np.array([[100.5, 200.3], [150.7, -9999.0]], dtype=np.float32)
        elevations = HeightmapGenerator._read_elevations(
            raw, nodata=-9999.0, scale=1.0, offset=0.0)
        assert elevations[0, 0] == pytest.approx(100.5, abs=0.1)
        assert elevations[1, 0] == pytest.approx(150.7, abs=0.1)
        assert np.isnan(elevations[1, 1])

    def test_int16_with_scale(self):
        """int16 data with scale=0.5."""
        raw = np.array([[100, 200], [300, -32768]], dtype=np.int16)
        elevations = HeightmapGenerator._read_elevations(
            raw, nodata=-32768, scale=0.5, offset=0.0)
        assert elevations[0, 0] == pytest.approx(50.0)
        assert elevations[0, 1] == pytest.approx(100.0)
        assert np.isnan(elevations[1, 1])

    def test_scale_and_offset(self):
        """Scale and offset should both be applied: elevation = raw * scale + offset."""
        raw = np.array([[10, 20]], dtype=np.int16)
        elevations = HeightmapGenerator._read_elevations(
            raw, nodata=None, scale=2.0, offset=100.0)
        assert elevations[0, 0] == pytest.approx(120.0)
        assert elevations[0, 1] == pytest.approx(140.0)

    def test_no_nodata(self):
        """When nodata is None, no pixels should become NaN."""
        raw = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        elevations = HeightmapGenerator._read_elevations(
            raw, nodata=None, scale=1.0, offset=0.0)
        assert not np.any(np.isnan(elevations))


class TestHeightmapNormalization:
    """Test normalization to 0-1 range and resize to 2^n+1."""

    def test_normalize_range(self):
        data = np.array([[100.0, 200.0], [150.0, 300.0]])
        normalized = HeightmapGenerator.normalize(data)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_normalize_flat_surface(self):
        data = np.full((10, 10), 42.0)
        normalized = HeightmapGenerator.normalize(data)
        assert np.all(normalized == 0.0)

    def test_nearest_gazebo_size(self):
        assert HeightmapGenerator.nearest_gazebo_size(500) == 513
        assert HeightmapGenerator.nearest_gazebo_size(513) == 513
        assert HeightmapGenerator.nearest_gazebo_size(514) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1000) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1025) == 1025
        assert HeightmapGenerator.nearest_gazebo_size(1026) == 2049


class TestFromDemFullROI:
    """Test reading a full DEM tile without lat/lon cropping."""

    def _make_test_geotiff(self, tmp_path: Path, size: int = 64) -> Path:
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

    def test_returns_heightmap_and_bounds(self, tmp_path):
        """from_dem_full_roi should return heightmap, elevation range, and geographic bounds."""
        dem_path = self._make_test_geotiff(tmp_path)
        heightmap, elev_min, elev_max, bounds = HeightmapGenerator.from_dem_full_roi(
            dem_path)

        assert heightmap.ndim == 2
        assert heightmap.shape[0] in [3, 5, 9, 17, 33, 65, 129]
        assert heightmap.shape[1] in [3, 5, 9, 17, 33, 65, 129]
        assert heightmap.min() == pytest.approx(0.0, abs=0.01)
        assert heightmap.max() == pytest.approx(1.0, abs=0.01)

        assert elev_min == pytest.approx(-100.0, abs=1.0)
        assert elev_max == pytest.approx(200.0, abs=1.0)

        assert "center_lat" in bounds
        assert "center_lon" in bounds
        assert "width_km" in bounds
        assert "height_km" in bounds
        assert bounds["width_km"] == pytest.approx(1.0, abs=0.1)
        assert bounds["height_km"] == pytest.approx(1.0, abs=0.1)
