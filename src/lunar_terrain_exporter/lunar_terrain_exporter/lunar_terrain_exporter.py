"""Terrain generation pipeline."""

from pathlib import Path

from .utils.types import LunarSite
from .utils.file_downloader import FileDownloader
from .utils.model_writer import ModelWriter
from .map_generators.heightmap_generator import HeightmapGenerator
from .map_generators.normal_map_generator import NormalMapGenerator


class LunarTerrainExporter:
    """Generates Gazebo SDF terrain models from PGDA Product 78 LOLA DEMs."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._default_cache_dir = Path(
            __file__).resolve().parents[3] / ".dem_cache"
        self._downloader = FileDownloader(self._default_cache_dir)

    def export_model(self, site: LunarSite) -> Path:
        """Export a complete Gazebo terrain model for a site."""
        print(f"\n=== Generating: {site.name} ===")

        dem_file = self._downloader.download(site.dem_url)

        elevations, elev_min, elev_max, bounds, dem_profile = (
            HeightmapGenerator.from_dem(dem_file, site.roi)
        )
        lat = bounds["center_lat"]
        lon = bounds["center_lon"]
        width_km = bounds["width_km"]
        height_km = bounds["height_km"]
        print(f"    ROI: center=({lat:.4f}, {lon:.4f}), "
              f"{width_km:.1f}x{height_km:.1f}km")

        normalized = HeightmapGenerator.normalize(elevations)
        normal_map = NormalMapGenerator.from_heightmap(normalized)

        size_x_m = int(width_km * 1000)
        size_y_m = int(height_km * 1000)
        model_dir = self._output_dir / site.name
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.name,
            display_name=site.name.replace("_", " ").title(),
            description=site.description or f"Lunar terrain at ({lat}, {lon})",
            elevations=elevations,
            dem_profile=dem_profile,
            normal_map=normal_map,
            size_x_m=size_x_m,
            size_y_m=size_y_m,
            elevation_min=elev_min,
            elevation_max=elev_max,
            lat=lat,
            lon=lon,
            source="nasa_pgda_78",
        )
        return model_dir
