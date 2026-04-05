"""Integration tests: SiteConfig → GenerateLunarSDF → output files.

Uses mocked downloads and data processing to avoid network access.
Verifies the full pipeline from YAML config to output model directory structure.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from generate_lunar_sdf.utils.site_config_parser import (
    BoundingBox, ROI, SiteConfig, load_sites,
)
from generate_lunar_sdf.generate_lunar_sdf import GenerateLunarSDF


class TestIntegrationConfigLoad:
    """Verify the preset Artemis sites config loads correctly."""

    def test_load_all_artemis_sites(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        assert len(sites) == 4
        names = [s.name for s in sites]
        assert "connecting_ridge" in names
        assert "de_gerlache_rim" in names

    def test_all_sites_use_full_roi(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        for site in sites:
            site.validate()
            assert site.roi.use_full is True
            assert site.dem_url.startswith("https://")

    def test_all_site_names_are_unique(self):
        config_path = Path(__file__).parent.parent / "config" / "artemis_sites.yaml"
        sites = load_sites(str(config_path))
        names = [s.name for s in sites]
        assert len(names) == len(set(names))


class TestIntegrationPipeline:
    """End-to-end pipeline with mocked external dependencies."""

    def test_terrain_generator_creates_output_structure(self, tmp_path):
        """Verify GenerateLunarSDF produces model dir with expected files."""
        config = SiteConfig(
            name="test_site",
            dem_url="https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
            roi=ROI(
                use_full=False,
                bounding_box=BoundingBox(lat=-86.5, lon=-4.0, width_km=2.0, height_km=2.0),
            ),
        )

        output_dir = tmp_path / "output"
        cache_dir = tmp_path / "cache"
        output_dir.mkdir()
        cache_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_diffuse = np.random.randint(60, 190, (size, size, 3), dtype=np.uint8)

        with patch("generate_lunar_sdf.generate_lunar_sdf.FileDownloader") as mock_dl_cls, \
             patch("generate_lunar_sdf.generate_lunar_sdf.HeightmapGenerator") as mock_hm, \
             patch("generate_lunar_sdf.generate_lunar_sdf.SlopeTextureGenerator") as mock_slope:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.from_dem.return_value = (fake_heightmap, -500.0, 2000.0)
            mock_slope.from_slope_geotiff_cropped.return_value = fake_diffuse

            generator = GenerateLunarSDF(output_dir=output_dir, cache_dir=cache_dir)
            result = generator.generate(config)

        # Downloader called for both DEM and slope
        assert mock_dl_instance.download.call_count == 2

        model_dir = output_dir / "test_site"
        assert model_dir.exists()
        assert result == model_dir

        assert (model_dir / "model.sdf").exists()
        assert (model_dir / "model.config").exists()

        textures_dir = model_dir / "materials" / "textures"
        assert textures_dir.exists()
        assert (textures_dir / "heightmap.png").exists()
        assert (textures_dir / "diffuse.png").exists()
        assert (textures_dir / "normal.png").exists()

        sdf_content = (model_dir / "model.sdf").read_text()
        assert "test_site" in sdf_content
        assert "diffuse.png" in sdf_content


class TestIntegrationFullROIPipeline:
    """Pipeline test with use_full ROI."""

    def test_full_roi_pipeline(self, tmp_path):
        """Verify GenerateLunarSDF uses from_dem_full_roi when roi.use_full=True."""
        config = SiteConfig(
            name="test_full_roi",
            dem_url="https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/Site01_final_adj_5mpp_surf.tif",
            roi=ROI(use_full=True),
        )

        output_dir = tmp_path / "output"
        cache_dir = tmp_path / "cache"
        output_dir.mkdir()
        cache_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_diffuse = np.random.randint(60, 190, (size, size, 3), dtype=np.uint8)
        bounds = {"center_lat": -89.5, "center_lon": -130.0, "width_km": 20.0, "height_km": 15.0}

        with patch("generate_lunar_sdf.generate_lunar_sdf.FileDownloader") as mock_dl_cls, \
             patch("generate_lunar_sdf.generate_lunar_sdf.HeightmapGenerator") as mock_hm, \
             patch("generate_lunar_sdf.generate_lunar_sdf.SlopeTextureGenerator") as mock_slope:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.from_dem_full_roi.return_value = (
                fake_heightmap, -500.0, 2000.0, bounds
            )
            mock_slope.from_slope_geotiff.return_value = fake_diffuse

            generator = GenerateLunarSDF(output_dir=output_dir, cache_dir=cache_dir)
            result = generator.generate(config)

        mock_hm.from_dem_full_roi.assert_called_once()
        mock_hm.from_dem.assert_not_called()
        mock_slope.from_slope_geotiff.assert_called_once()

        assert mock_dl_instance.download.call_count == 2

        model_dir = output_dir / "test_full_roi"
        assert model_dir.exists()
        assert result == model_dir
