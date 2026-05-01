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


"""Tests for site configuration dataclasses and YAML loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from lunar_terrain_exporter.utils.types import (
    BoundingBox, ROI, LunarSite,
)
from lunar_terrain_exporter.cli import load_sites_from_yaml


class TestBoundingBox:
    def test_create_with_defaults(self):
        bb = BoundingBox(lat=-86.5, lon=-4.0)
        assert bb.width_km == 10.0
        assert bb.height_km == 10.0

    def test_create_with_explicit_dims(self):
        bb = BoundingBox(lat=-86.5, lon=-4.0, width_km=8.0, height_km=12.0)
        assert bb.width_km == 8.0
        assert bb.height_km == 12.0

    def test_validate_rejects_lat_above_minus_80(self):
        with pytest.raises(ValueError, match="lat"):
            BoundingBox(lat=-70.0, lon=0.0).validate()

    def test_validate_rejects_non_positive_width(self):
        with pytest.raises(ValueError, match="width_km"):
            BoundingBox(lat=-85.0, lon=0.0, width_km=0).validate()

    def test_validate_rejects_non_positive_height(self):
        with pytest.raises(ValueError, match="height_km"):
            BoundingBox(lat=-85.0, lon=0.0, height_km=-1).validate()

    def test_validate_accepts_valid(self):
        BoundingBox(lat=-86.5, lon=-4.0, width_km=10.0,
                    height_km=8.0).validate()


class TestROI:
    def test_use_full_no_bbox(self):
        ext = ROI(use_full=True)
        ext.validate()

    def test_use_full_with_bbox_still_valid(self):
        ext = ROI(use_full=True, bounding_box=BoundingBox(lat=-85.0, lon=0.0))
        ext.validate()

    def test_crop_requires_bbox(self):
        with pytest.raises(ValueError, match="bounding_box"):
            ROI(use_full=False).validate()

    def test_crop_with_bbox_valid(self):
        ext = ROI(
            use_full=False,
            bounding_box=BoundingBox(
                lat=-86.5, lon=-4.0, width_km=10.0, height_km=8.0),
        )
        ext.validate()

    def test_crop_propagates_bbox_validation(self):
        with pytest.raises(ValueError, match="lat"):
            ROI(
                use_full=False,
                bounding_box=BoundingBox(lat=-70.0, lon=0.0),
            ).validate()


class TestLunarSite:
    def test_create_with_bbox(self):
        config = LunarSite(
            site_code="Site01",
            name="test_site",
            roi=ROI(
                use_full=False,
                bounding_box=BoundingBox(lat=-86.5, lon=-4.0),
            ),
        )
        assert config.name == "test_site"
        assert config.site_code == "Site01"
        assert config.roi.bounding_box.lat == -86.5
        assert config.roi.bounding_box.lon == -4.0
        assert config.roi.bounding_box.width_km == 10.0
        assert config.roi.bounding_box.height_km == 10.0
        assert config.description == ""

    def test_create_with_full_roi(self):
        config = LunarSite(
            site_code="Site01",
            name="test_site",
            roi=ROI(use_full=True),
        )
        assert config.roi.use_full is True
        assert config.roi.bounding_box is None

    def test_dem_url_generated_from_site_code(self):
        config = LunarSite(
            site_code="Site01",
            name="test_site",
            roi=ROI(use_full=True),
        )
        assert config.dem_url == (
            "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/Site01/"
            "Site01_final_adj_5mpp_surf.tif"
        )

    def test_validate_rejects_empty_name(self):
        with pytest.raises(ValueError, match="name"):
            LunarSite(
                site_code="Site01",
                name="",
                roi=ROI(use_full=True),
            ).validate()

    def test_validate_rejects_invalid_name_chars(self):
        with pytest.raises(ValueError, match="name"):
            LunarSite(
                site_code="Site01",
                name="bad name/here",
                roi=ROI(use_full=True),
            ).validate()

    def test_validate_rejects_empty_site_code(self):
        with pytest.raises(ValueError, match="site_code"):
            LunarSite(
                site_code="",
                name="test",
                roi=ROI(use_full=True),
            ).validate()

    def test_validate_propagates_roi_validation(self):
        with pytest.raises(ValueError, match="bounding_box"):
            LunarSite(
                site_code="Site01",
                name="test",
                roi=ROI(use_full=False),
            ).validate()

    def test_validate_accepts_full_roi(self):
        config = LunarSite(
            site_code="Site01",
            name="test_site",
            roi=ROI(use_full=True),
        )
        config.validate()

    def test_validate_accepts_valid_bbox(self):
        config = LunarSite(
            site_code="Haworth",
            name="haworth",
            roi=ROI(
                use_full=False,
                bounding_box=BoundingBox(lat=-86.5, lon=-4.0),
            ),
        )
        config.validate()

    def test_default_roi_requires_bbox(self):
        with pytest.raises(ValueError, match="bounding_box"):
            LunarSite(
                site_code="Site01",
                name="test_site",
            ).validate()


class TestLoadSites:
    def _write_yaml(self, data: dict, path: Path) -> Path:
        config_file = path / "sites.yaml"
        with open(config_file, "w") as f:
            yaml.dump(data, f)
        return config_file

    def test_load_single_site(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "connecting_ridge",
                    "roi": {
                        "use_full": False,
                        "bounding_box": {"lat": -86.5, "lon": -4.0},
                    },
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 1
            assert sites[0].name == "connecting_ridge"
            assert sites[0].site_code == "Site01"
            assert sites[0].roi.bounding_box.width_km == 10.0

    def test_load_multiple_sites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {
                        "site": "connecting_ridge",
                        "roi": {
                            "use_full": False,
                            "bounding_box": {"lat": -86.0, "lon": 0.0},
                        },
                    },
                    {
                        "site": "shackleton_rim",
                        "roi": {
                            "use_full": False,
                            "bounding_box": {
                                "lat": -87.0, "lon": 10.0,
                                "width_km": 5.0, "height_km": 5.0,
                            },
                        },
                    },
                ]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 2
            assert sites[1].roi.bounding_box.width_km == 5.0

    def test_missing_required_field_raises(self):
        """An entry without a 'site' key is skipped (warning printed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{"name": "bad"}]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 0

    def test_load_full_roi_site(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "connecting_ridge",
                    "roi": {"use_full": True},
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 1
            assert sites[0].roi.use_full is True
            assert sites[0].roi.bounding_box is None


class TestFromCatalog:
    def test_creates_config_from_catalog_name(self):
        config = LunarSite.from_catalog("connecting_ridge")
        assert config.name == "connecting_ridge"
        assert "Site01" in config.dem_url
        assert config.roi.use_full is True
        assert config.description != ""

    def test_custom_roi(self):
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


class TestLoadSitesCatalogShorthand:
    def _write_yaml(self, data: dict, path: Path) -> Path:
        config_file = path / "sites.yaml"
        with open(config_file, "w") as f:
            yaml.dump(data, f)
        return config_file

    def test_catalog_shorthand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "connecting_ridge",
                    "roi": {"use_full": True},
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 1
            assert sites[0].name == "connecting_ridge"
            assert "Site01" in sites[0].dem_url

    def test_catalog_shorthand_with_bbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [{
                    "site": "shackleton_rim",
                    "roi": {
                        "use_full": False,
                        "bounding_box": {"lat": -86.5, "lon": -4.0, "width_km": 5.0},
                    },
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert sites[0].roi.bounding_box.width_km == 5.0
            assert "Site04" in sites[0].dem_url

    def test_mixed_catalog_and_explicit(self):
        """Two catalog entries in a batch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                "sites": [
                    {
                        "site": "connecting_ridge",
                        "roi": {"use_full": True},
                    },
                    {
                        "site": "shackleton_rim",
                        "roi": {"use_full": True},
                    },
                ]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 2
            assert sites[0].name == "connecting_ridge"
            assert sites[1].name == "shackleton_rim"
