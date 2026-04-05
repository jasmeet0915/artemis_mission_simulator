"""Heightmap generation from PGDA Product 78 polar stereographic GeoTIFF DEMs."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

# Lunar radius in meters (IAU mean)
_LUNAR_RADIUS_M = 1_737_400.0


class HeightmapGenerator:
    """Generates normalized heightmap arrays from PGDA Product 78 polar DEM GeoTIFFs.

    Handles the south pole polar stereographic projection used by
    Barker et al. (2021) 5 m/pix LOLA DEMs.
    """

    @staticmethod
    def latlon_to_stereo(lat: float, lon: float) -> tuple[float, float]:
        """Convert geographic lat/lon to lunar south pole stereographic (x, y).

        Projection: polar stereographic centered on south pole (-90, 0).
        Sphere radius: 1,737,400 m (IAU lunar mean).

        Returns (x, y) in meters.
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        # Colatitude from south pole
        colat = -(math.pi / 2 + lat_rad)
        r = 2.0 * _LUNAR_RADIUS_M * math.tan(colat / 2.0)
        x = r * math.sin(lon_rad)
        y = r * math.cos(lon_rad)
        return x, y

    @staticmethod
    def stereo_to_latlon(x: float, y: float) -> tuple[float, float]:
        """Convert lunar south pole stereographic (x, y) to geographic lat/lon.

        Inverse of latlon_to_stereo(). Returns (lat, lon) in degrees.
        """
        r = math.sqrt(x**2 + y**2)
        if r < 1e-10:
            return -90.0, 0.0
        colat = 2.0 * math.atan(r / (2.0 * _LUNAR_RADIUS_M))
        # For south pole stereographic, points away from pole have negative colat
        colat = -colat  
        lat = math.degrees(-colat - math.pi / 2)
        # Account for negative r flipping coordinates by 180°
        lon = math.degrees(math.atan2(x, y)) + 180.0
        # Normalize to [-180, 180]
        if lon > 180.0:
            lon -= 360.0
        return lat, lon

    @staticmethod
    def _read_elevations(
        raw: np.ndarray,
        nodata: float | int | None,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> np.ndarray:
        """Convert raw raster values to elevation in meters using dataset metadata.

        elevation_m = raw * scale + offset
        Pixels matching nodata become NaN.
        """
        result = raw.astype(np.float64) * scale + offset
        if nodata is not None:
            nodata_mask = np.isclose(raw.astype(np.float64), float(nodata))
            result[nodata_mask] = np.nan
        return result

    @staticmethod
    def normalize(data: np.ndarray) -> np.ndarray:
        """Normalize elevation data to [0, 1] range. NaN becomes 0."""
        data = np.nan_to_num(data, nan=np.nanmin(data) if not np.all(np.isnan(data)) else 0.0)
        vmin = float(np.min(data))
        vmax = float(np.max(data))
        if vmax > vmin:
            return (data - vmin) / (vmax - vmin)
        return np.zeros_like(data, dtype=np.float64)

    @staticmethod
    def nearest_gazebo_size(n: int) -> int:
        """Return the smallest 2^k + 1 >= n (Gazebo heightmap requirement)."""
        if n <= 3:
            return 3
        k = math.ceil(math.log2(n - 1))
        return (1 << k) + 1

    @staticmethod
    def from_dem(
        dem_path: Path,
        lat: float,
        lon: float,
        width_km: float,
        height_km: float,
    ) -> tuple[np.ndarray, float, float]:
        """Crop a rectangular region from a polar DEM and return a heightmap.

        Reads nodata, scale, and offset from the GeoTIFF metadata via rasterio.

        Args:
            dem_path: Local path to the DEM file.
            lat: Center latitude in degrees (negative for south).
            lon: Center longitude in degrees.
            width_km: Width of the region in km (east-west).
            height_km: Height of the region in km (north-south).

        Returns:
            (heightmap_float64_01, elevation_min_m, elevation_max_m)
            Heightmap is resized to the nearest 2^n+1 dimension per axis.
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling

        x_center, y_center = HeightmapGenerator.latlon_to_stereo(lat, lon)
        half_w = width_km * 1000.0 / 2.0
        half_h = height_km * 1000.0 / 2.0
        x_min = x_center - half_w
        x_max = x_center + half_w
        y_min = y_center - half_h
        y_max = y_center + half_h

        with rasterio.open(dem_path) as src:
            window = from_bounds(x_min, y_min, x_max, y_max, src.transform)
            raw_width = max(int(window.width), 1)
            raw_height = max(int(window.height), 1)
            target_w = HeightmapGenerator.nearest_gazebo_size(raw_width)
            target_h = HeightmapGenerator.nearest_gazebo_size(raw_height)

            raw = src.read(
                1,
                window=window,
                out_shape=(target_h, target_w),
                resampling=Resampling.bilinear,
            )

            nodata = src.nodata
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0

        elevations = HeightmapGenerator._read_elevations(raw, nodata, scale, offset)

        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))
        heightmap = HeightmapGenerator.normalize(elevations)

        return heightmap, elev_min, elev_max

    @staticmethod
    def from_dem_full_roi(
        dem_path: Path,
    ) -> tuple[np.ndarray, float, float, dict]:
        """Read an entire DEM file and return a heightmap with geographic bounds.

        For use with pre-cropped per-site DEM tiles where lat/lon cropping
        is not needed.

        Returns:
            (heightmap_float64_01, elevation_min_m, elevation_max_m, bounds)
            bounds is a dict with keys: center_lat, center_lon, width_km, height_km
        """
        import rasterio
        from rasterio.enums import Resampling

        with rasterio.open(dem_path) as src:
            target_w = HeightmapGenerator.nearest_gazebo_size(src.width)
            target_h = HeightmapGenerator.nearest_gazebo_size(src.height)

            raw = src.read(
                1,
                out_shape=(target_h, target_w),
                resampling=Resampling.bilinear,
            )

            nodata = src.nodata
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0

            raster_bounds = src.bounds
            x_min, y_min = raster_bounds.left, raster_bounds.bottom
            x_max, y_max = raster_bounds.right, raster_bounds.top

        elevations = HeightmapGenerator._read_elevations(raw, nodata, scale, offset)

        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))
        heightmap = HeightmapGenerator.normalize(elevations)

        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0
        center_lat, center_lon = HeightmapGenerator.stereo_to_latlon(x_center, y_center)

        bounds = {
            "center_lat": center_lat,
            "center_lon": center_lon,
            "width_km": (x_max - x_min) / 1000.0,
            "height_km": (y_max - y_min) / 1000.0,
        }

        return heightmap, elev_min, elev_max, bounds
