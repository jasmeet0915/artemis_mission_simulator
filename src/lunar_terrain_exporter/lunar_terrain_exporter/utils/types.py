"""Data types for terrain generation configuration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_BASE_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp"


@dataclass
class BoundingBox:
    """Geographic bounding box defined by center and dimensions."""

    lat: float
    lon: float
    width_km: float = 10.0
    height_km: float = 10.0

    def validate(self) -> None:
        """Validate bounding box values. Raises ValueError on invalid data."""
        if self.lat > -80.0:
            raise ValueError(
                f"lat must be <= -80.0 for south pole DEMs (got: {self.lat})"
            )
        if self.width_km <= 0:
            raise ValueError(f"width_km must be > 0 (got: {self.width_km})")
        if self.height_km <= 0:
            raise ValueError(f"height_km must be > 0 (got: {self.height_km})")


@dataclass
class ROI:
    """Defines how much of a DEM to use: full ROI or a bounding box crop."""

    use_full: bool = False
    bounding_box: BoundingBox | None = None

    def validate(self) -> None:
        """Validate ROI configuration. Raises ValueError on invalid data."""
        if not self.use_full:
            if self.bounding_box is None:
                raise ValueError(
                    "bounding_box is required when use_full is False"
                )
            self.bounding_box.validate()


@dataclass
class LunarSite:
    """A single lunar terrain site with its DEM source and region of interest.

    The DEM and slope URLs are derived automatically from *site_code*.
    """

    site_code: str
    name: str
    description: str = ""
    roi: ROI = field(default_factory=ROI)

    @classmethod
    def from_catalog(cls, identifier: str, roi: ROI | None = None) -> LunarSite:
        """Build a LunarSite by looking up *identifier* (name or code) in the PGDA-78 catalog."""
        from .site_catalog import get_site
        entry = get_site(identifier)
        return cls(
            site_code=entry["site_code"],
            name=entry["site_name"],
            description=entry["description"],
            roi=roi or ROI(use_full=True),
        )

    @property
    def dem_url(self) -> str:
        """DEM (surface elevation) GeoTIFF URL."""
        return f"{_BASE_URL}/{self.site_code}/{self.site_code}_final_adj_5mpp_surf.tif"

    @property
    def slope_url(self) -> str:
        """Slope map GeoTIFF URL."""
        return f"{_BASE_URL}/{self.site_code}/{self.site_code}_final_adj_5mpp_slp.tif"

    def validate(self) -> None:
        """Validate configuration values. Raises ValueError on invalid data."""
        if not self.name or not _VALID_NAME_RE.match(self.name):
            raise ValueError(
                f"name must be non-empty and contain only alphanumeric, "
                f"hyphens, or underscores (got: {self.name!r})"
            )
        if not self.site_code:
            raise ValueError("site_code must be a non-empty string")
        self.roi.validate()
