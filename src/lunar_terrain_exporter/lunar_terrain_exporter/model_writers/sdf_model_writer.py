"""Gazebo SDF model writer — generates SDF, model.config, metadata, and textures."""

from pathlib import Path
from string import Template

import numpy as np
import rasterio
import yaml
from PIL import Image

_MODEL_SDF_TEMPLATE = Template("""\
<?xml version="1.0"?>
<sdf version="1.11">
  <model name="${site_id}">
    <static>true</static>
    <link name="terrain_link">
      <collision name="terrain_collision">
        <geometry>
          <heightmap>
            <uri>materials/textures/heightmap.tif</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
          </heightmap>
        </geometry>
      </collision>
      <visual name="terrain_visual">
        <geometry>
          <heightmap>
            <uri>materials/textures/heightmap.tif</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
            <texture>
              <normal>materials/textures/normal.png</normal>
              <size>10</size>
            </texture>
          </heightmap>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>
""")

_MODEL_CONFIG_TEMPLATE = Template("""\
<?xml version="1.0"?>
<model>
  <name>${display_name}</name>
  <version>1.0</version>
  <sdf version="1.11">model.sdf</sdf>
  <author>
    <name>Artemis Mission Simulator</name>
  </author>
  <description>${description}</description>
</model>
""")


class SDFModelWriter:
    """Writes a complete Gazebo SDF terrain model to disk."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def write(
        self,
        site_id: str,
        display_name: str,
        description: str,
        elevations: np.ndarray,
        dem_profile: dict,
        normal_map: np.ndarray,
        size_x_m: int,
        size_y_m: int,
        elevation_min: float,
        elevation_max: float,
        lat: float,
        lon: float,
        source: str,
    ) -> Path:
        """Write all model files (SDF, config, textures, metadata)."""
        model_dir = self._output_dir / site_id
        textures_dir = model_dir / "materials" / "textures"
        textures_dir.mkdir(parents=True, exist_ok=True)

        # GeoTIFF DEM heightmap (preserves CRS and resolution)
        height, width = elevations.shape
        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 1,
            "dtype": "float32",
            **dem_profile,
        }
        with rasterio.open(textures_dir / "heightmap.tif", "w", **profile) as dst:
            dst.write(elevations.astype(np.float32), 1)

        # RGB normal map PNG
        Image.fromarray(normal_map, mode="RGB").save(
            textures_dir / "normal.png")

        elevation_range = max(elevation_max - elevation_min, 1.0)

        sdf_content = _MODEL_SDF_TEMPLATE.substitute(
            site_id=site_id,
            size_x=size_x_m,
            size_y=size_y_m,
            size_z=f"{elevation_range:.1f}",
            z_offset=f"{elevation_min:.1f}",
        )
        (model_dir / "model.sdf").write_text(sdf_content)

        config_content = _MODEL_CONFIG_TEMPLATE.substitute(
            display_name=display_name,
            description=description,
        )
        (model_dir / "model.config").write_text(config_content)

        metadata = {
            "site_id": site_id,
            "display_name": display_name,
            "description": description,
            "coordinates": {"lat": float(lat), "lon": float(lon)},
            "size_x_m": size_x_m,
            "size_y_m": size_y_m,
            "resolution_x": int(elevations.shape[1]),
            "resolution_y": int(elevations.shape[0]),
            "elevation_min_m": round(elevation_min, 2),
            "elevation_max_m": round(elevation_max, 2),
            "elevation_range_m": round(elevation_range, 2),
            "source": source,
        }
        with open(model_dir / "metadata.yaml", "w") as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

        print(f"  Model written to: {model_dir}")
        return model_dir
