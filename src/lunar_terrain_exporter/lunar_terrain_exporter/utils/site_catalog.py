"""PGDA Product 78 site catalog — all 27 south pole landing sites.

URL patterns are deterministic from the PGDA ID:
  DEM:   https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{id}/{id}_final_adj_5mpp_surf.tif
  Slope: https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/{id}/{id}_final_adj_5mpp_slp.tif
"""

from __future__ import annotations

from dataclasses import dataclass

_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


@dataclass(frozen=True)
class CatalogSite:
    """Metadata for a single PGDA-78 south pole site."""

    pgda_id: str
    name: str
    display_name: str
    description: str

    @property
    def dem_url(self) -> str:
        """DEM (surface elevation) GeoTIFF URL."""
        return f"{_BASE_URL}/{self.pgda_id}/{self.pgda_id}_final_adj_5mpp_surf.tif"

    @property
    def slope_url(self) -> str:
        """Slope map GeoTIFF URL."""
        return f"{_BASE_URL}/{self.pgda_id}/{self.pgda_id}_final_adj_5mpp_slp.tif"


SITE_CATALOG: dict[str, CatalogSite] = {s.name: s for s in [
    CatalogSite("Site01", "connecting_ridge", "Connecting Ridge",
                "Site 01 – Connecting ridge between Shackleton and de Gerlache craters"),
    CatalogSite("Site04", "shackleton_rim", "Shackleton Rim",
                "Site 04 – Rim of Shackleton crater"),
    CatalogSite("Site06", "nobile_rim_1", "Nobile Rim 1",
                "Site 06 – Nobile rim 1"),
    CatalogSite("Site07", "peak_near_shackleton", "Peak Near Shackleton",
                "Site 07 – Isolated peak near Shackleton crater"),
    CatalogSite("Site11", "de_gerlache_rim", "de Gerlache Rim",
                "Site 11 – Rim of de Gerlache crater"),
    CatalogSite("Site20", "leibnitz_beta", "Leibnitz Beta Plateau",
                "Site 20 – Leibnitz beta plateau"),
    CatalogSite("Site20v2", "leibnitz_beta_v2", "Leibnitz Beta Plateau (Extended)",
                "Site 20v2 – Leibnitz beta plateau, extended boundaries"),
    CatalogSite("Site23", "malapert_massif", "Malapert Massif",
                "Site 23 – Malapert massif"),
    CatalogSite("Site42", "de_gerlache_kocher", "de Gerlache-Kocher Massif",
                "Site 42 – de Gerlache-Kocher massif"),
    CatalogSite("Haworth", "haworth", "Haworth",
                "Haworth crater"),
    CatalogSite("Shoemaker", "shoemaker", "Shoemaker",
                "Shoemaker crater"),
    CatalogSite("DM1", "amundsen_rim", "Amundsen Rim",
                "DM1 – Amundsen rim"),
    CatalogSite("DM2", "nobile_rim_2", "Nobile Rim 2",
                "DM2 – Nobile rim 2"),
    CatalogSite("SL2", "de_gerlache_rim_2", "de Gerlache Rim (SL2)",
                "SL2 – de Gerlache rim"),
    CatalogSite("SL3", "connecting_ridge_ext", "Connecting Ridge Extension",
                "SL3 – Connecting ridge extension"),
    CatalogSite("NPA", "cabeus_wall", "Cabeus Exterior Wall 1",
                "NPA – Cabeus exterior wall 1"),
    CatalogSite("NPB", "amundsen_1", "Amundsen 1",
                "NPB – Amundsen 1"),
    CatalogSite("NPC", "idelson_l", "Idel'son L Crater 1",
                "NPC – Idel'son L crater 1"),
    CatalogSite("NPD", "malapert_crater", "Malapert Crater 1",
                "NPD – Malapert crater 1"),
    CatalogSite("LM1", "shackleton_rim_b", "Shackleton Rim B",
                "LM1 – Shackleton Rim B"),
    CatalogSite("LM2", "shoemaker_rim_a", "Shoemaker Rim A",
                "LM2 – Shoemaker Rim A"),
    CatalogSite("LM3", "shoemaker_rim_b", "Shoemaker Rim B",
                "LM3 – Shoemaker Rim B"),
    CatalogSite("LM4", "shoemaker_rim_c", "Shoemaker Rim C",
                "LM4 – Shoemaker Rim C"),
    CatalogSite("LM5", "shoemaker_rim_d", "Shoemaker Rim D",
                "LM5 – Shoemaker Rim D"),
    CatalogSite("LM6", "shoemaker_rim_e", "Shoemaker Rim E",
                "LM6 – Shoemaker Rim E"),
    CatalogSite("LM7", "faustini_rim_a", "Faustini Rim A",
                "LM7 – Faustini Rim A"),
    CatalogSite("LM8", "shoemaker_rim_f", "Shoemaker Rim F",
                "LM8 – Shoemaker Rim F"),
]}


def list_sites() -> list[CatalogSite]:
    """Return all catalog sites in insertion order."""
    return list(SITE_CATALOG.values())


def get_site(name: str) -> CatalogSite:
    """Get a catalog site by name. Raises KeyError if not found."""
    try:
        return SITE_CATALOG[name]
    except KeyError:
        available = sorted(SITE_CATALOG.keys())
        raise KeyError(
            f"Site {name!r} not in catalog. Available: {available}"
        ) from None
