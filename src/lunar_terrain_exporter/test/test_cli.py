"""Tests for the CLI argument parsing and subcommands."""

import pytest

from lunar_terrain_exporter.cli import build_parser, _load_sites_from_yaml
from lunar_terrain_exporter.utils.types import BoundingBox, ROI, LunarSite


class TestSiteSubcommand:
    def test_site_full_roi(self):
        parser = build_parser()
        args = parser.parse_args([
            "site", "connecting_ridge",
            "--output-dir", "/tmp/out",
        ])
        assert args.command == "site"
        assert args.site_name == "connecting_ridge"
        assert args.output_dir == "/tmp/out"
        assert args.lat is None
        assert args.lon is None

    def test_site_with_code(self):
        """CLI should accept a site code as well as a name."""
        parser = build_parser()
        args = parser.parse_args(["site", "Site01"])
        assert args.site_name == "Site01"

    def test_site_with_crop(self):
        parser = build_parser()
        args = parser.parse_args([
            "site", "shackleton_rim",
            "--lat", "-86.5",
            "--lon", "-4.0",
            "--width", "5.0",
            "--height", "5.0",
            "--output-dir", "/tmp/out",
        ])
        assert args.site_name == "shackleton_rim"
        assert args.lat == -86.5
        assert args.width == 5.0

    def test_site_default_output_dir(self):
        parser = build_parser()
        args = parser.parse_args(["site", "connecting_ridge"])
        assert args.output_dir == "."

    def test_site_default_dimensions(self):
        parser = build_parser()
        args = parser.parse_args(["site", "connecting_ridge"])
        assert args.width == 10.0
        assert args.height == 10.0


class TestBatchSubcommand:
    def test_batch_mode(self):
        parser = build_parser()
        args = parser.parse_args([
            "batch",
            "--config", "sites.yaml",
            "--output-dir", "/tmp/out",
        ])
        assert args.command == "batch"
        assert args.config == "sites.yaml"
        assert args.output_dir == "/tmp/out"

    def test_batch_requires_config(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["batch", "--output-dir", "/tmp/out"])


class TestNoSubcommand:
    def test_no_command_gives_none(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestLunarSiteFromCatalog:
    def test_creates_config_full_roi(self):
        config = LunarSite.from_catalog("connecting_ridge")
        assert config.name == "connecting_ridge"
        assert config.site_code == "Site01"
        assert "Site01" in config.dem_url
        assert config.roi.use_full is True
        assert config.description != ""

    def test_creates_config_by_code(self):
        config = LunarSite.from_catalog("Site01")
        assert config.name == "connecting_ridge"
        assert config.site_code == "Site01"

    def test_creates_config_custom_roi(self):
        roi = ROI(
            use_full=False,
            bounding_box=BoundingBox(
                lat=-86.5, lon=-4.0, width_km=5.0, height_km=5.0),
        )
        config = LunarSite.from_catalog("shackleton_rim", roi=roi)
        assert config.roi.use_full is False
        assert config.roi.bounding_box.lat == -86.5

    def test_unknown_site_raises(self):
        with pytest.raises(KeyError, match="no_such_site"):
            LunarSite.from_catalog("no_such_site")
