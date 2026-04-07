"""Tests for the PGDA-78 site catalog."""

import pytest

from lunar_terrain_exporter.utils.site_catalog import (
    CatalogEntry, list_sites, get_site,
)

_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


class TestCatalogEntry:
    def test_entry_has_required_keys(self):
        entry = get_site("connecting_ridge")
        assert "site_code" in entry
        assert "site_name" in entry
        assert "description" in entry

    def test_entry_values(self):
        entry = get_site("connecting_ridge")
        assert entry["site_code"] == "Site01"
        assert entry["site_name"] == "connecting_ridge"
        assert entry["description"] != ""


class TestSiteCatalog:
    def test_catalog_has_27_sites(self):
        assert len(list_sites()) == 27

    def test_known_sites_present(self):
        names = {e["site_name"] for e in list_sites()}
        for name in ["connecting_ridge", "shackleton_rim", "peak_near_shackleton",
                     "de_gerlache_rim", "haworth", "shoemaker", "amundsen_rim"]:
            assert name in names

    def test_all_names_are_snake_case(self):
        for entry in list_sites():
            name = entry["site_name"]
            assert name == name.lower()
            assert " " not in name

    def test_all_site_codes_unique(self):
        codes = [e["site_code"] for e in list_sites()]
        assert len(codes) == len(set(codes))


class TestListSites:
    def test_returns_all_27(self):
        sites = list_sites()
        assert len(sites) == 27

    def test_returns_catalog_entry_dicts(self):
        sites = list_sites()
        assert all(isinstance(s, dict) for s in sites)


class TestGetSite:
    def test_lookup_by_name(self):
        entry = get_site("connecting_ridge")
        assert entry["site_code"] == "Site01"

    def test_lookup_by_code(self):
        entry = get_site("Site01")
        assert entry["site_name"] == "connecting_ridge"

    def test_unknown_site_raises(self):
        with pytest.raises(KeyError, match="no_such_site"):
            get_site("no_such_site")

    def test_error_lists_available(self):
        with pytest.raises(KeyError, match="connecting_ridge"):
            get_site("bad_name")
