"""Integration tests: LunarSite → LunarTerrainExporter → output files.

Uses mocked downloads and data processing to avoid network access.
Verifies the full pipeline from YAML config to output model directory structure.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from lunar_terrain_exporter.utils.types import (
    BoundingBox, ROI, LunarSite,
)
from lunar_terrain_exporter.cli import load_sites_from_yaml
from lunar_terrain_exporter.lunar_terrain_exporter import LunarTerrainExporter


class TestIntegrationConfigLoad:
    """Verify the preset Artemis sites config loads correctly."""

    def test_load_all_artemis_sites(self):
        config_path = Path(__file__).parent.parent / \
            "config" / "artemis_sites.yaml"
        sites = load_sites_from_yaml(str(config_path))
        assert len(sites) == 4
        names = [s.name for s in sites]
        assert "connecting_ridge" in names
        assert "de_gerlache_rim" in names

    def test_all_sites_use_full_roi(self):
        config_path = Path(__file__).parent.parent / \
            "config" / "artemis_sites.yaml"
        sites = load_sites_from_yaml(str(config_path))
        for site in sites:
            site.validate()
            assert site.roi.use_full is True
            assert site.dem_url.startswith("https://")

    def test_all_site_names_are_unique(self):
        config_path = Path(__file__).parent.parent / \
            "config" / "artemis_sites.yaml"
        sites = load_sites_from_yaml(str(config_path))
        names = [s.name for s in sites]
        assert len(names) == len(set(names))


class TestIntegrationPipeline:
    """End-to-end pipeline with mocked external dependencies."""

    def test_terrain_generator_creates_output_structure(self, tmp_path):
        """Verify LunarTerrainExporter produces model dir with expected files."""
        config = LunarSite(
            site_code="Site01",
            name="test_site",
            roi=ROI(
                use_full=False,
                bounding_box=BoundingBox(
                    lat=-86.5, lon=-4.0, width_km=2.0, height_km=2.0),
            ),
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        fake_bounds = {"center_lat": -86.5, "center_lon": -4.0,
                       "width_km": 2.0, "height_km": 2.0}
        fake_profile = {"crs": "EPSG:3031",
                        "transform": None}

        with patch("lunar_terrain_exporter.lunar_terrain_exporter.FileDownloader") as mock_dl_cls, \
                patch("lunar_terrain_exporter.lunar_terrain_exporter.DEMProcessor") as mock_hm:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.extract_from_raw.return_value = (
                fake_heightmap, -500.0, 2000.0, fake_bounds, fake_profile)

            generator = LunarTerrainExporter(output_dir=output_dir)
            result = generator.export_model(config)

        # Downloader called for DEM only
        assert mock_dl_instance.download.call_count == 1

        model_dir = output_dir / "test_site"
        assert model_dir.exists()
        assert result == model_dir

        assert (model_dir / "model.sdf").exists()
        assert (model_dir / "model.config").exists()

        textures_dir = model_dir / "materials" / "textures"
        assert textures_dir.exists()
        assert (textures_dir / "heightmap.tif").exists()
        assert (textures_dir / "normal.png").exists()

        sdf_content = (model_dir / "model.sdf").read_text()
        assert "test_site" in sdf_content


class TestIntegrationFullROIPipeline:
    """Pipeline test with use_full ROI."""

    def test_full_roi_pipeline(self, tmp_path):
        """Verify LunarTerrainExporter calls extract_from_raw with use_full ROI."""
        config = LunarSite(
            site_code="Site01",
            name="test_full_roi",
            roi=ROI(use_full=True),
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        size = 513
        fake_heightmap = np.random.rand(size, size).astype(np.float64)
        bounds = {"center_lat": -89.5, "center_lon": -
                  130.0, "width_km": 20.0, "height_km": 15.0}
        fake_profile = {"crs": "EPSG:3031",
                        "transform": None}

        with patch("lunar_terrain_exporter.lunar_terrain_exporter.FileDownloader") as mock_dl_cls, \
                patch("lunar_terrain_exporter.lunar_terrain_exporter.DEMProcessor") as mock_hm:

            mock_dl_instance = MagicMock()
            mock_dl_instance.download.return_value = tmp_path / "fake.tif"
            mock_dl_cls.return_value = mock_dl_instance

            mock_hm.extract_from_raw.return_value = (
                fake_heightmap, -500.0, 2000.0, bounds, fake_profile
            )

            generator = LunarTerrainExporter(output_dir=output_dir)
            result = generator.export_model(config)

        mock_hm.extract_from_raw.assert_called_once()

        assert mock_dl_instance.download.call_count == 1

        model_dir = output_dir / "test_full_roi"
        assert model_dir.exists()
        assert result == model_dir
