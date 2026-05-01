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


"""PGDA Product 78 site catalog — all 27 south pole landing sites.

Each entry stores only the site code, site name and description.
URL construction is handled by :class:`~.types.LunarSite`.
"""

from typing import TypedDict


class CatalogEntry(TypedDict):
    """Metadata for a single PGDA-78 south pole site."""

    site_code: str
    site_name: str
    description: str


_CATALOG: list[CatalogEntry] = [
    {"site_code": "Site01", "site_name": "connecting_ridge",
        "description": "Site 01 \u2013 Connecting ridge between Shackleton and de Gerlache craters"},
    {"site_code": "Site04", "site_name": "shackleton_rim",
        "description": "Site 04 \u2013 Rim of Shackleton crater"},
    {"site_code": "Site06", "site_name": "nobile_rim_1",
        "description": "Site 06 \u2013 Nobile rim 1"},
    {"site_code": "Site07", "site_name": "peak_near_shackleton",
        "description": "Site 07 \u2013 Isolated peak near Shackleton crater"},
    {"site_code": "Site11", "site_name": "de_gerlache_rim",
        "description": "Site 11 \u2013 Rim of de Gerlache crater"},
    {"site_code": "Site20", "site_name": "leibnitz_beta",
        "description": "Site 20 \u2013 Leibnitz beta plateau"},
    {"site_code": "Site20v2", "site_name": "leibnitz_beta_v2",
        "description": "Site 20v2 \u2013 Leibnitz beta plateau, extended boundaries"},
    {"site_code": "Site23", "site_name": "malapert_massif",
        "description": "Site 23 \u2013 Malapert massif"},
    {"site_code": "Site42", "site_name": "de_gerlache_kocher",
        "description": "Site 42 \u2013 de Gerlache-Kocher massif"},
    {"site_code": "Haworth", "site_name": "haworth",
        "description": "Haworth crater"},
    {"site_code": "Shoemaker", "site_name": "shoemaker",
        "description": "Shoemaker crater"},
    {"site_code": "DM1", "site_name": "amundsen_rim",
        "description": "DM1 \u2013 Amundsen rim"},
    {"site_code": "DM2", "site_name": "nobile_rim_2",
        "description": "DM2 \u2013 Nobile rim 2"},
    {"site_code": "SL2", "site_name": "de_gerlache_rim_2",
        "description": "SL2 \u2013 de Gerlache rim"},
    {"site_code": "SL3", "site_name": "connecting_ridge_ext",
        "description": "SL3 \u2013 Connecting ridge extension"},
    {"site_code": "NPA", "site_name": "cabeus_wall",
        "description": "NPA \u2013 Cabeus exterior wall 1"},
    {"site_code": "NPB", "site_name": "amundsen_1",
        "description": "NPB \u2013 Amundsen 1"},
    {"site_code": "NPC", "site_name": "idelson_l",
        "description": "NPC \u2013 Idel\u2019son L crater 1"},
    {"site_code": "NPD", "site_name": "malapert_crater",
        "description": "NPD \u2013 Malapert crater 1"},
    {"site_code": "LM1", "site_name": "shackleton_rim_b",
        "description": "LM1 \u2013 Shackleton Rim B"},
    {"site_code": "LM2", "site_name": "shoemaker_rim_a",
        "description": "LM2 \u2013 Shoemaker Rim A"},
    {"site_code": "LM3", "site_name": "shoemaker_rim_b",
        "description": "LM3 \u2013 Shoemaker Rim B"},
    {"site_code": "LM4", "site_name": "shoemaker_rim_c",
        "description": "LM4 \u2013 Shoemaker Rim C"},
    {"site_code": "LM5", "site_name": "shoemaker_rim_d",
        "description": "LM5 \u2013 Shoemaker Rim D"},
    {"site_code": "LM6", "site_name": "shoemaker_rim_e",
        "description": "LM6 \u2013 Shoemaker Rim E"},
    {"site_code": "LM7", "site_name": "faustini_rim_a",
        "description": "LM7 \u2013 Faustini Rim A"},
    {"site_code": "LM8", "site_name": "shoemaker_rim_f",
        "description": "LM8 \u2013 Shoemaker Rim F"},
]

# Build lookup indices
_BY_NAME: dict[str, CatalogEntry] = {e["site_name"]: e for e in _CATALOG}
_BY_CODE: dict[str, CatalogEntry] = {e["site_code"]: e for e in _CATALOG}


def list_sites() -> list[CatalogEntry]:
    """Return all catalog entries in insertion order."""
    return list(_CATALOG)


def get_site(identifier: str) -> CatalogEntry:
    """Look up a site by name **or** site code.

    Raises :exc:`KeyError` if no matching entry is found.
    """
    if identifier in _BY_NAME:
        return _BY_NAME[identifier]
    if identifier in _BY_CODE:
        return _BY_CODE[identifier]
    available_names = sorted(_BY_NAME.keys())
    available_codes = sorted(_BY_CODE.keys())
    raise KeyError(
        f"Site {identifier!r} not found in catalog. "
        f"Available names: {available_names}  "
        f"Available codes: {available_codes}"
    )
