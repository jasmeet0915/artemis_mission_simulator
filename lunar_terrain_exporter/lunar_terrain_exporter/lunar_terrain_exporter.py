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


"""Terrain generation pipeline."""

import math
import os
from pathlib import Path

from .model_writers.sdf_model_writer import SDFModelWriter
from .raster_processors.dem_processor import DEMProcessor
from .utils.file_downloader import FileDownloader
from .utils.frames import terrain_enu_rotation_rpy
from .utils.types import LunarSite


class LunarTerrainExporter:
    """Generates Gazebo SDF terrain models from PGDA Product 78 LOLA DEMs."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        workspace_dir = os.getenv('WORKSPACE_DIR', '/workspace/src')
        self._default_cache_dir = Path(workspace_dir) / '.dem_cache'
        self._downloader = FileDownloader(self._default_cache_dir)
        self._model_writer = SDFModelWriter(self._output_dir)

    def export_model(self, site: LunarSite) -> Path:
        """Export a complete Gazebo terrain model for a site."""
        print(f'\n=== Generating: {site.name} ===')

        dem_file = self._downloader.download(site.dem_url)

        elevations, elev_min, elev_max, bounds, dem_profile = (
            DEMProcessor.extract_from_raw(dem_file, site.roi)
        )
        lat = bounds['center_lat']
        lon = bounds['center_lon']
        size_km = bounds['size_km']
        print(f'    ROI: center=({lat:.4f}, {lon:.4f}), {size_km:.1f}km sq')

        size_m = int(size_km * 1000)
        size_x_m = size_y_m = size_m

        h, w = elevations.shape
        center_elevation = float(elevations[h // 2, w // 2])
        if not math.isfinite(center_elevation):
            center_elevation = (elev_min + elev_max) / 2.0
        roll, pitch, yaw = terrain_enu_rotation_rpy(lat, lon)

        self._model_writer.write(
            site_id=site.name,
            display_name=site.name.replace('_', ' ').title(),
            description=site.description or f'Lunar terrain at ({lat}, {lon})',
            elevations=elevations,
            dem_profile=dem_profile,
            size_x_m=size_x_m,
            size_y_m=size_y_m,
            elevation_min=elev_min,
            elevation_max=elev_max,
            lat=lat,
            lon=lon,
            source='nasa_pgda_78',
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            center_elevation=center_elevation,
        )
        return self._output_dir / site.name
