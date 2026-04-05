"""Tests for the PGDA-78 site catalog."""

import pytest

from lunar_terrain_exporter.utils.site_catalog import (
    CatalogSite, SITE_CATALOG, list_sites, get_site,
)

_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


class TestCatalogSite:
    def test_dem_url_generation(self):
        site = CatalogSite("Site01", "connecting_ridge",
                           "Connecting Ridge", "desc")
        assert site.dem_url == f"{_BASE_URL}/Site01/Site01_final_adj_5mpp_surf.tif"

    def test_slope_url_generation(self):
        site = CatalogSite("Site01", "connecting_ridge",
                           "Connecting Ridge", "desc")
        assert site.slope_url == f"{_BASE_URL}/Site01/Site01_final_adj_5mpp_slp.tif"

    def test_non_numeric_pgda_id(self):
        """Sites like Haworth, DM1, LM2 have non-SiteNN pgda_ids."""
        site = CatalogSite("Haworth", "haworth", "Haworth", "desc")
        assert site.dem_url == f"{_BASE_URL}/Haworth/Haworth_final_adj_5mpp_surf.tif"

    def test_frozen_dataclass(self):
        site = CatalogSite("Site01", "connecting_ridge",
                           "Connecting Ridge", "desc")
        with pytest.raises(AttributeError):
            site.name = "other"


class TestSiteCatalog:
    def test_catalog_has_27_sites(self):
        assert len(SITE_CATALOG) == 27

    def test_known_sites_present(self):
        for name in ["connecting_ridge", "shackleton_rim", "peak_near_shackleton",
                     "de_gerlache_rim", "haworth", "shoemaker", "amundsen_rim"]:
            assert name in SITE_CATALOG

    def test_all_names_are_snake_case(self):
        for name in SITE_CATALOG:
            assert name == name.lower()
            assert " " not in name

    def test_all_pgda_ids_unique(self):
        ids = [s.pgda_id for s in SITE_CATALOG.values()]
        assert len(ids) == len(set(ids))


class TestListSites:
    def test_returns_all_27(self):
        sites = list_sites()
        assert len(sites) == 27

    def test_returns_catalog_site_objects(self):
        sites = list_sites()
        assert all(isinstance(s, CatalogSite) for s in sites)


class TestGetSite:
    def test_known_site(self):
        site = get_site("connecting_ridge")
        assert site.pgda_id == "Site01"
        assert site.display_name == "Connecting Ridge"

    def test_unknown_site_raises(self):
        with pytest.raises(KeyError, match="no_such_site"):
            get_site("no_such_site")

    def test_error_lists_available(self):
        with pytest.raises(KeyError, match="connecting_ridge"):
            get_site("bad_name")
