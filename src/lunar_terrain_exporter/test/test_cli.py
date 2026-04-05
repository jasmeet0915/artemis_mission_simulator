"""Tests for the CLI argument parsing and interactive mode."""

import pytest
from unittest.mock import patch

from lunar_terrain_exporter.lunar_terrain_exporter import LunarTerrainExporter


class TestCLISiteMode:
    def test_site_mode_full_roi(self):
        parser = LunarTerrainExporter._build_parser()
        args = parser.parse_args([
            "--site", "connecting_ridge",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "connecting_ridge"
        assert args.output_dir == "/tmp/out"
        assert args.lat is None
        assert args.lon is None

    def test_site_mode_with_crop(self):
        parser = LunarTerrainExporter._build_parser()
        args = parser.parse_args([
            "--site", "shackleton_rim",
            "--lat", "-86.5",
            "--lon", "-4.0",
            "--width", "5.0",
            "--height", "5.0",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "shackleton_rim"
        assert args.lat == -86.5
        assert args.width == 5.0

    def test_site_mode_explicit_full_roi(self):
        parser = LunarTerrainExporter._build_parser()
        args = parser.parse_args([
            "--site", "peak_near_shackleton",
            "--use-full-roi",
            "--output-dir", "/tmp/out",
        ])
        assert args.site == "peak_near_shackleton"
        assert args.use_full_roi is True


class TestCLIConfigMode:
    def test_config_mode(self):
        parser = LunarTerrainExporter._build_parser()
        args = parser.parse_args([
            "--config", "sites.yaml",
            "--output-dir", "/tmp/out",
        ])
        assert args.config == "sites.yaml"
        assert args.output_dir == "/tmp/out"


class TestCLIMutualExclusion:
    def test_config_and_site_together_fails(self):
        parser = LunarTerrainExporter._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([
                "--config", "sites.yaml",
                "--site", "bad",
                "--output-dir", "/tmp/out",
            ])


class TestCLIInteractiveMode:
    def test_no_mode_gives_interactive(self):
        """When neither --site nor --config given, args.site and args.config are both None."""
        parser = LunarTerrainExporter._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/out"])
        assert args.site is None
        assert args.config is None

    def test_interactive_list_sites(self):
        """_interactive_select should list all 27 sites and return a SiteConfig."""
        inputs = iter(["1", "1"])
        with patch("builtins.input", side_effect=inputs):
            config = LunarTerrainExporter._interactive_select()
        assert config.name == "connecting_ridge"
        assert config.roi.use_full is True

    def test_interactive_select_by_name(self):
        inputs = iter(["shackleton_rim", "1"])
        with patch("builtins.input", side_effect=inputs):
            config = LunarTerrainExporter._interactive_select()
        assert config.name == "shackleton_rim"

    def test_interactive_custom_bbox(self):
        inputs = iter(["1", "2", "-86.5", "-4.0", "5.0", "5.0"])
        with patch("builtins.input", side_effect=inputs):
            config = LunarTerrainExporter._interactive_select()
        assert config.roi.use_full is False
        assert config.roi.bounding_box.lat == -86.5
        assert config.roi.bounding_box.width_km == 5.0
