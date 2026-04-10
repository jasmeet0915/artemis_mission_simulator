"""Utility modules for terrain generation: downloading, writing, types, site catalog."""

from .types import BoundingBox, ROI, LunarSite
from .file_downloader import FileDownloader
from .model_writer import ModelWriter  # backward compat alias
from .site_catalog import CatalogEntry, list_sites as list_catalog_sites, get_site as get_catalog_site

__all__ = [
    "BoundingBox", "ROI", "LunarSite",
    "FileDownloader", "ModelWriter",
    "CatalogEntry", "list_catalog_sites", "get_catalog_site",
]
