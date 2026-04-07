"""Command-line interface for generating lunar terrain models.

Subcommands
-----------
site   Export a single site (full DEM or custom bounding-box crop).
batch  Export multiple sites listed in a YAML config file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .lunar_terrain_exporter import LunarTerrainExporter
from .utils.types import BoundingBox, ROI, LunarSite
from .utils.site_catalog import get_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lunar_terrain_exporter",
        description=(
            "Export terrain models (only SDF models supported for now) from NASA"
            "PGDA (Planetary Geodesy Data Archive) Product 78: High resolution "
            "DEMs for Lunar South Pole Sites (main target for the Artemis Missions)."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # site subcommand
    site_parser = subparsers.add_parser(
        "site",
        help="Export model for a single site from the PGDA-78 catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  # Full DEM tile\n"
            "  lunar_terrain_exporter site connecting_ridge --output-dir ./models\n\n"
            "  # Custom ROI with bounding-box crop\n"
            "  lunar_terrain_exporter site shackleton_rim "
            "--lat -86.5 --lon -4.0 --width 5 --height 5 --output-dir ./models"
        ),
    )
    site_parser.add_argument(
        "site_name", type=str,
        help="Site name or site code from the PGDA-78 catalog (e.g. connecting_ridge or Site01)",
    )
    site_parser.add_argument(
        "--lat", type=float, default=None,
        help="Center latitude for custom crop",
    )
    site_parser.add_argument(
        "--lon", type=float, default=None,
        help="Center longitude for custom crop",
    )
    site_parser.add_argument(
        "--width", type=float, default=10.0,
        help="Region width in km (default: 10)",
    )
    site_parser.add_argument(
        "--height", type=float, default=10.0,
        help="Region height in km (default: 10)",
    )
    site_parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Output directory for generated models (default: .)",
    )

    # batch subcommand
    batch_parser = subparsers.add_parser(
        "batch",
        help="Export multiple sites from a YAML config file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  lunar_terrain_exporter batch "
            "--config config/artemis_sites.yaml --output-dir ./models"
        ),
    )
    batch_parser.add_argument(
        "--config", type=str, required=True,
        help="Path to YAML config file listing sites to export",
    )
    batch_parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Output directory for generated models (default: .)",
    )

    return parser


def load_sites_from_yaml(config_path: Path) -> list[LunarSite]:
    """Parse a YAML config file and return a list of LunarSite objects.

    Each entry must have a ``site`` key with a name or code from the
    PGDA-78 catalog.  An optional ``roi`` block can override the default
    full-DEM behaviour.
    """
    with open(config_path) as f:
        data = yaml.safe_load(f)

    sites: list[LunarSite] = []
    for entry in data["sites"]:
        # Build ROI from optional roi block (defaults to full DEM)
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

        try:
            config = LunarSite.from_catalog(entry["site"], roi=roi)
        except (KeyError, ValueError) as exc:
            print(f"Warning: skipping entry {entry!r}: {exc}", file=sys.stderr)
            continue
        sites.append(config)

    return sites


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    output_dir = Path(args.output_dir)
    sites: list[LunarSite] = []

    if args.command == "site":
        # Validate site exists in catalog (accepts name or code)
        try:
            catalog_entry = get_site(args.site_name)
        except KeyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

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

        site = LunarSite(
            site_code=catalog_entry["site_code"],
            name=catalog_entry["site_name"],
            description=catalog_entry["description"],
            roi=roi,
        )
        site.validate()
        sites.append(site)

    elif args.command == "batch":
        sites = load_sites_from_yaml(Path(args.config))

    exporter = LunarTerrainExporter(output_dir)
    for site in sites:
        exporter.export_model(site)

    print("\nDone!")
