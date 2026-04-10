"""Tests for the lunar terrain generator modules."""

import tempfile
from pathlib import Path

import numpy as np
import yaml
from rasterio.transform import from_bounds

from lunar_terrain_exporter.raster_processors.normal_map_generator import NormalMapGenerator
from lunar_terrain_exporter.model_writers.sdf_model_writer import SDFModelWriter


def _make_elevations(size: int = 65) -> np.ndarray:
    """Create a simple test elevation array (float64, meters)."""
    rng = np.random.default_rng(42)
    return rng.random((size, size)) * 500.0 - 100.0  # range ~ [-100, 400]


def _make_dem_profile(size: int = 65) -> dict:
    """Create a minimal rasterio-compatible DEM profile for tests."""
    return {
        "crs": "EPSG:3031",
        "transform": from_bounds(-500, -500, 500, 500, size, size),
    }


# ---------------------------------------------------------------------------
# NormalMapGenerator
# ---------------------------------------------------------------------------

class TestNormalMap:
    def test_shape_rgb(self):
        nm = NormalMapGenerator.from_heightmap(_make_elevations(129))
        assert nm.shape == (129, 129, 3)

    def test_dtype_uint8(self):
        nm = NormalMapGenerator.from_heightmap(_make_elevations(129))
        assert nm.dtype == np.uint8

    def test_flat_surface_points_up(self):
        flat = np.full((65, 65), 0.5, dtype=np.float64)
        nm = NormalMapGenerator.from_heightmap(flat, strength=1.0)
        # Z channel (blue) should be high (~255), X/Y (red/green) near 128
        assert nm[:, :, 2].mean() > 200
        assert 120 < nm[:, :, 0].mean() < 136
        assert 120 < nm[:, :, 1].mean() < 136

    def test_strength_affects_output(self):
        nm_weak = NormalMapGenerator.from_heightmap(_make_elevations(65), strength=0.5)
        nm_strong = NormalMapGenerator.from_heightmap(_make_elevations(65), strength=5.0)
        assert nm_strong[:, :, 0].std() > nm_weak[:, :, 0].std()


# ---------------------------------------------------------------------------
# SDFModelWriter
# ---------------------------------------------------------------------------

class TestSDFModelWriter:
    def test_writes_all_files(self):
        elev = _make_elevations()
        nm = NormalMapGenerator.from_heightmap(elev)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = SDFModelWriter(Path(tmpdir) / "test_site")
            writer.write(
                site_id="test_site",
                display_name="Test Site",
                description="A test site",
                elevations=elev,
                dem_profile=_make_dem_profile(),
                normal_map=nm,
                size_x_m=5000,
                size_y_m=4000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="nasa_pgda_78",
            )
            out = Path(tmpdir) / "test_site"
            assert (out / "model.sdf").exists()
            assert (out / "model.config").exists()
            assert (out / "metadata.yaml").exists()
            assert (out / "materials" / "textures" / "heightmap.tif").exists()
            assert (out / "materials" / "textures" / "normal.png").exists()

    def test_sdf_contains_site_id_and_sizes(self):
        elev = _make_elevations()
        nm = NormalMapGenerator.from_heightmap(elev)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = SDFModelWriter(Path(tmpdir) / "my_site")
            writer.write(
                site_id="my_site",
                display_name="My Site",
                description="Desc",
                elevations=elev,
                dem_profile=_make_dem_profile(),
                normal_map=nm,
                size_x_m=3000,
                size_y_m=2000,
                elevation_min=-100.0,
                elevation_max=200.0,
                lat=-85.0,
                lon=10.0,
                source="nasa_pgda_78",
            )
            sdf = (Path(tmpdir) / "my_site" / "model.sdf").read_text()
            assert 'name="my_site"' in sdf
            assert "3000" in sdf
            assert "2000" in sdf

    def test_metadata_yaml_valid(self):
        elev = _make_elevations()
        nm = NormalMapGenerator.from_heightmap(elev)
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = SDFModelWriter(Path(tmpdir) / "meta_test")
            writer.write(
                site_id="meta_test",
                display_name="Meta Test",
                description="Testing metadata",
                elevations=elev,
                dem_profile=_make_dem_profile(),
                normal_map=nm,
                size_x_m=5000,
                size_y_m=4000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="nasa_pgda_78",
            )
            with open(Path(tmpdir) / "meta_test" / "metadata.yaml") as f:
                meta = yaml.safe_load(f)
            assert meta["site_id"] == "meta_test"
            assert meta["size_x_m"] == 5000
            assert meta["size_y_m"] == 4000
            assert meta["elevation_range_m"] == 500.0
            assert meta["coordinates"]["lat"] == -89.7
            assert meta["source"] == "nasa_pgda_78"
