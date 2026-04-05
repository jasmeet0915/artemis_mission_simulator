"""Command-line interface and terrain generation pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .utils.site_config_parser import (
    BoundingBox, ROI, SiteConfig, load_sites,
)
from .utils.file_downloader import FileDownloader
from .utils.model_writer import ModelWriter
from .map_generators.heightmap_generator import HeightmapGenerator
from .map_generators.normal_map_generator import NormalMapGenerator
from .map_generators.slope_texture_generator import SlopeTextureGenerator


class LunarTerrainExporter:
    """Generates Gazebo SDF terrain models from PGDA Product 78 LOLA DEMs.

    Handles both CLI parsing and the full terrain generation pipeline.
    """

    def __init__(self, output_dir: Path, cache_dir: Path) -> None:
        self._output_dir = output_dir
        self._downloader = FileDownloader(cache_dir)

    def generate(self, site: SiteConfig) -> Path:
        """Generate a complete Gazebo terrain model for a site."""
        print(f"\n=== Generating: {site.name} ===")

        dem_file = self._downloader.download(site.dem_url)
        slope_file = self._downloader.download(site.slope_url)

        if site.roi.use_full:
            heightmap, elev_min, elev_max, bounds = (
                HeightmapGenerator.from_dem_full_roi(dem_file)
            )
            diffuse = SlopeTextureGenerator.from_slope_geotiff(
                slope_file, heightmap.shape[0], heightmap.shape[1]
            )
            lat = bounds["center_lat"]
            lon = bounds["center_lon"]
            width_km = bounds["width_km"]
            height_km = bounds["height_km"]
            print(f"    Full ROI: center=({lat:.4f}, {lon:.4f}), "
                  f"{width_km:.1f}x{height_km:.1f}km")
        else:
            bb = site.roi.bounding_box
            heightmap, elev_min, elev_max = HeightmapGenerator.from_dem(
                dem_file, bb.lat, bb.lon, bb.width_km, bb.height_km
            )
            diffuse = SlopeTextureGenerator.from_slope_geotiff_cropped(
                slope_file, bb.lat, bb.lon, bb.width_km, bb.height_km,
                heightmap.shape[0], heightmap.shape[1]
            )
            lat = bb.lat
            lon = bb.lon
            width_km = bb.width_km
            height_km = bb.height_km
            print(f"    Lat: {lat}, Lon: {lon}, "
                  f"Region: {width_km}x{height_km}km")

        normal_map = NormalMapGenerator.from_heightmap(heightmap)

        size_x_m = int(width_km * 1000)
        size_y_m = int(height_km * 1000)
        model_dir = self._output_dir / site.name
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.name,
            display_name=site.name.replace("_", " ").title(),
            description=site.description or f"Lunar terrain at ({lat}, {lon})",
            heightmap=heightmap,
            diffuse_map=diffuse,
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

    @classmethod
    def _default_cache_dir(cls) -> Path:
        """Default cache: data/ directory at repository root."""
        return Path(__file__).resolve().parents[3] / "data"

    @classmethod
    def from_cli(cls, argv: list[str] | None = None) -> None:
        """Parse CLI arguments and run the terrain generation pipeline."""
        parser = cls._build_parser()
        args = parser.parse_args(argv)

        output_dir = Path(args.output_dir)
        cache_dir = Path(
            args.cache_dir) if args.cache_dir else cls._default_cache_dir()

        generator = cls(output_dir=output_dir, cache_dir=cache_dir)

        if args.config:
            config_path = Path(args.config)
            sites = load_sites(config_path)
            for site in sites:
                generator.generate(site)
        elif args.site:
            if args.lat is not None and args.lon is not None:
                roi = ROI(
                    use_full=False,
                    bounding_box=BoundingBox(
                        lat=args.lat,
                        lon=args.lon,
                        width_km=args.width,
                        height_km=args.height,
                    ),
                )
            else:
                roi = ROI(use_full=True)
            site = SiteConfig.from_catalog(args.site, roi=roi)
            site.validate()
            generator.generate(site)
        else:
            # Interactive mode
            site = cls._interactive_select()
            site.validate()
            generator.generate(site)

        print("\nDone!")
