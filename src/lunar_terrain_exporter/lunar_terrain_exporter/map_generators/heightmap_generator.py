"""Heightmap generation from PGDA Product 78 polar stereographic GeoTIFF DEMs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.windows import from_bounds

from ..utils.types import ROI


class HeightmapGenerator:
    """Extracts elevation data from PGDA Product 78 polar DEM GeoTIFFs.

    Handles the south pole polar stereographic projection used by
    Barker et al. (2021) 5 m/pix LOLA DEMs.
    """

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
        """Normalize elevation data to [0, 1] range. NaN becomes 0.

        Useful for derived products (e.g. normal-map generation) that
        expect input in a uniform [0, 1] range.
        """
        data = np.nan_to_num(data, nan=np.nanmin(
            data) if not np.all(np.isnan(data)) else 0.0)
        vmin = float(np.min(data))
        vmax = float(np.max(data))
        if vmax > vmin:
            return (data - vmin) / (vmax - vmin)
        return np.zeros_like(data, dtype=np.float64)

    @staticmethod
    def from_dem(
        dem_path: Path,
        roi: ROI,
    ) -> tuple[np.ndarray, float, float, dict, dict]:
        """Extract elevation data from a DEM, full-tile or bounding-box crop.

        Uses the CRS embedded in the GeoTIFF and *pyproj* for all
        coordinate transformations.

        Args:
            dem_path: Local path to the DEM GeoTIFF.
            roi: Region of interest.  When ``roi.use_full`` is True the
                 entire raster is read; otherwise the area is cropped to
                 ``roi.bounding_box``.

        Returns:
            (elevations, elev_min, elev_max, bounds, dem_profile)

            *elevations*: float64 array of elevation values in meters.
            *bounds*: dict with ``center_lat``, ``center_lon``,
            ``width_km``, ``height_km``.
            *dem_profile*: dict with ``crs`` and ``transform`` suitable
            for writing a GeoTIFF of the output array.
        """
        with rasterio.open(dem_path) as src:
            geographic_crs = CRS(src.crs).geodetic_crs
            to_projected = Transformer.from_crs(
                geographic_crs, src.crs, always_xy=True,
            )
            to_geographic = Transformer.from_crs(
                src.crs, geographic_crs, always_xy=True,
            )

            if roi.use_full:
                # ---- read entire raster --------------------------------
                raw = src.read(1)
                out_transform = src.transform

                rb = src.bounds
                x_min, y_min = rb.left, rb.bottom
                x_max, y_max = rb.right, rb.top
            else:
                # ---- crop to bounding box ------------------------------
                bb = roi.bounding_box
                # lon first because always_xy=True
                x_center, y_center = to_projected.transform(bb.lon, bb.lat)
                half_w = bb.width_km * 1000.0 / 2.0
                half_h = bb.height_km * 1000.0 / 2.0
                x_min = x_center - half_w
                x_max = x_center + half_w
                y_min = y_center - half_h
                y_max = y_center + half_h

                window = from_bounds(
                    x_min, y_min, x_max, y_max, src.transform,
                )
                raw = src.read(1, window=window)
                out_transform = src.window_transform(window)

            nodata = src.nodata
            scale = src.scales[0] if src.scales else 1.0
            offset = src.offsets[0] if src.offsets else 0.0
            crs = src.crs

        # ---- raw → elevation in meters ---------------------------------
        elevations = HeightmapGenerator._read_elevations(
            raw, nodata, scale, offset,
        )
        elev_min = float(np.nanmin(elevations))
        elev_max = float(np.nanmax(elevations))

        # ---- geographic bounds -----------------------------------------
        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0
        center_lon, center_lat = to_geographic.transform(x_center, y_center)

        bounds = {
            "center_lat": center_lat,
            "center_lon": center_lon,
            "width_km": (x_max - x_min) / 1000.0,
            "height_km": (y_max - y_min) / 1000.0,
        }

        dem_profile = {
            "crs": crs,
            "transform": out_transform,
        }

        return elevations, elev_min, elev_max, bounds, dem_profile
