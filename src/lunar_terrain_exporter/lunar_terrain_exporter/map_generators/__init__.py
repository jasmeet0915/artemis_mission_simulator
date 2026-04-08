"""Map generator modules: DEM processing and normal map generation."""

from .heightmap_generator import DEMProcessor
from .normal_map_generator import NormalMapGenerator

__all__ = ["DEMProcessor", "NormalMapGenerator"]
