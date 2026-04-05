"""Site configuration dataclass and YAML parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


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
class SiteConfig:
    """Configuration for a single terrain generation site."""

    name: str
    dem_url: str
    roi: ROI = field(default_factory=ROI)
    description: str = ""

    @classmethod
    def from_catalog(cls, site_name: str, roi: ROI | None = None) -> SiteConfig:
        """Construct SiteConfig from the PGDA-78 site catalog."""
        from .site_catalog import get_site
        cat = get_site(site_name)
        return cls(
            name=cat.name,
            dem_url=cat.dem_url,
            roi=roi or ROI(use_full=True),
            description=cat.description,
        )

    @property
    def slope_url(self) -> str:
        """Derive slope GeoTIFF URL from DEM URL."""
        return self.dem_url.replace("_surf.tif", "_slp.tif")

    def validate(self) -> None:
        """Validate configuration values. Raises ValueError on invalid data."""
        if not self.name or not _VALID_NAME_RE.match(self.name):
            raise ValueError(
                f"name must be non-empty and contain only alphanumeric, "
                f"hyphens, or underscores (got: {self.name!r})"
            )
        if not self.dem_url:
            raise ValueError("dem_url must be a non-empty string")
        self.roi.validate()


def load_sites(config_path: Path) -> list[SiteConfig]:
    """Parse a YAML config file and return a list of validated SiteConfig objects."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    sites = []
    for entry in data["sites"]:
        # Catalog shorthand: { site: "connecting_ridge", roi: {...} }
        if "site" in entry:
            roi_raw = entry.get("roi", {})
            use_full = bool(roi_raw.get("use_full", True))

            bounding_box = None
            bb_raw = roi_raw.get("bounding_box")
            if bb_raw is not None:
                bounding_box = BoundingBox(
                    lat=float(bb_raw["lat"]),
                    lon=float(bb_raw["lon"]),
                    width_km=float(bb_raw.get("width_km", 10.0)),
                    height_km=float(bb_raw.get("height_km", 10.0)),
                )

            roi = ROI(use_full=use_full, bounding_box=bounding_box)
            config = SiteConfig.from_catalog(entry["site"], roi=roi)
            config.validate()
            sites.append(config)
            continue

        # Legacy explicit URL format: { name: ..., dem_url: ..., roi: {...} }
        roi_raw = entry.get("roi", {})
        use_full = bool(roi_raw.get("use_full", False))

        bounding_box = None
        bb_raw = roi_raw.get("bounding_box")
        if bb_raw is not None:
            bounding_box = BoundingBox(
                lat=float(bb_raw["lat"]),
                lon=float(bb_raw["lon"]),
                width_km=float(bb_raw.get("width_km", 10.0)),
                height_km=float(bb_raw.get("height_km", 10.0)),
            )

        config = SiteConfig(
            name=entry["name"],
            dem_url=entry["dem_url"],
            roi=ROI(use_full=use_full, bounding_box=bounding_box),
            description=entry.get("description", ""),
        )
        config.validate()
        sites.append(config)
    return sites


def load_site(config_path: Path, site_name: str) -> SiteConfig:
    """Load a single named site from a YAML config file."""
    sites = load_sites(config_path)
    for site in sites:
        if site.name == site_name:
            return site
    available = [s.name for s in sites]
    raise ValueError(
        f"Site {site_name!r} not found in {config_path}. "
        f"Available: {available}"
    )
