# Package Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic `lunar_simulation` ament_cmake package into two focused packages: `lunar_terrain_generator` (ament_python, OO/modular terrain tool + preset models + env hooks) and `artemis_mission_launcher` (ament_cmake, launch files + worlds + GUI config).

**Architecture:** `lunar_terrain_generator` is a ROS 2 Python package containing a class-based, modular terrain generation tool with an argparse CLI, preset SDF terrain models, and ament environment hooks that auto-set `GZ_SIM_RESOURCE_PATH`. `artemis_mission_launcher` is a lightweight ament_cmake package that installs launch files, Gazebo world files, and GUI configs — it depends on `lunar_terrain_generator` for models. The Dockerfile and README are updated to reference the new packages.

**Tech Stack:** ROS 2 Jazzy · ament_python · ament_cmake · Gazebo Harmonic · Python 3 (numpy, scipy, Pillow, rasterio, requests, PyYAML) · Docker · Apache 2.0

---

## File Structure

```
src/
├── lunar_terrain_generator/                    # ament_python package
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── lunar_terrain_generator             # empty ament marker
│   ├── lunar_terrain_generator/                # Python module
│   │   ├── __init__.py
│   │   ├── site_config.py                      # SiteConfig dataclass + SiteRegistry
│   │   ├── heightmap.py                        # HeightmapGenerator class
│   │   ├── albedo.py                           # AlbedoGenerator class
│   │   ├── normal_map.py                       # NormalMapGenerator class
│   │   ├── downloader.py                       # FileDownloader class
│   │   ├── model_writer.py                     # ModelWriter class (SDF, config, metadata, textures)
│   │   ├── terrain_generator.py                # TerrainGenerator orchestrator class
│   │   └── cli.py                              # argparse CLI entry point
│   ├── config/
│   │   └── sites.yaml                          # 13 NASA candidate sites
│   ├── models/                                 # Pre-built SDF terrain models (moved from old pkg)
│   │   ├── shackleton_crater/
│   │   ├── nobile_rim_1/
│   │   ├── connecting_ridge/
│   │   ├── de_gerlache_rim_1/
│   │   └── malapert_massif/
│   ├── hooks/
│   │   ├── lunar_terrain_generator.dsv         # DSV env hook for GZ_SIM_RESOURCE_PATH
│   │   └── lunar_terrain_generator.sh          # Shell env hook (backup for non-DSV systems)
│   ├── test/
│   │   ├── __init__.py
│   │   └── test_terrain_processing.py
│   └── README.md
│
└── artemis_mission_launcher/                   # ament_cmake package
    ├── package.xml
    ├── CMakeLists.txt
    ├── launch/
    │   ├── lunar_surface.launch.py
    │   └── world_builder.launch.py
    ├── worlds/
    │   └── lunar_surface.world
    └── config/
        └── gui.config
```

---

### Task 1: Create lunar_terrain_generator Package Scaffold

**Files:**
- Create: `src/lunar_terrain_generator/package.xml`
- Create: `src/lunar_terrain_generator/setup.py`
- Create: `src/lunar_terrain_generator/setup.cfg`
- Create: `src/lunar_terrain_generator/resource/lunar_terrain_generator`
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/lunar_terrain_generator/{resource,lunar_terrain_generator,config,hooks,test,models}
```

- [ ] **Step 2: Create package.xml**

Create `src/lunar_terrain_generator/package.xml`:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>lunar_terrain_generator</name>
  <version>0.1.0</version>
  <description>Terrain generation tool and preset lunar terrain models for Gazebo Harmonic</description>
  <maintainer email="todo@example.com">Artemis Simulator Contributors</maintainer>
  <license>Apache-2.0</license>

  <exec_depend>python3-numpy</exec_depend>
  <exec_depend>python3-scipy</exec_depend>
  <exec_depend>python3-yaml</exec_depend>
  <exec_depend>python3-pil</exec_depend>

  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

- [ ] **Step 3: Create setup.cfg**

Create `src/lunar_terrain_generator/setup.cfg`:

```ini
[develop]
script_dir=$base/lib/lunar_terrain_generator

[install]
install_scripts=$base/lib/lunar_terrain_generator
```

- [ ] **Step 4: Create setup.py**

Create `src/lunar_terrain_generator/setup.py`:

```python
import os
from setuptools import setup, find_packages

package_name = 'lunar_terrain_generator'


def collect_data_files(source_dir, install_prefix):
    """Walk a directory tree and return (install_dir, [files]) tuples."""
    data_files = []
    for root, _dirs, files in os.walk(source_dir):
        if files:
            install_dir = os.path.join(install_prefix, root)
            file_paths = [os.path.join(root, f) for f in files]
            data_files.append((install_dir, file_paths))
    return data_files


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/sites.yaml']),
        ('share/' + package_name + '/environment',
            ['hooks/' + package_name + '.dsv',
             'hooks/' + package_name + '.sh']),
    ] + collect_data_files('models', 'share/' + package_name),
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'generate_lunar_sdf = lunar_terrain_generator.cli:main',
        ],
    },
)
```

- [ ] **Step 5: Create ament resource marker and __init__.py**

Create empty `src/lunar_terrain_generator/resource/lunar_terrain_generator` (empty file, no content).

Create `src/lunar_terrain_generator/lunar_terrain_generator/__init__.py`:

```python
"""Lunar terrain generation tool for Gazebo Harmonic."""
```

- [ ] **Step 6: Commit scaffold**

```bash
git add src/lunar_terrain_generator/
git commit -m "feat: scaffold lunar_terrain_generator ament_python package"
```

---

### Task 2: Site Configuration Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/site_config.py`
- Create: `src/lunar_terrain_generator/test/__init__.py`
- Create: `src/lunar_terrain_generator/test/test_site_config.py`

- [ ] **Step 1: Write test_site_config.py**

Create `src/lunar_terrain_generator/test/test_site_config.py`:

```python
"""Tests for the site configuration module."""

import pytest
from pathlib import Path

from lunar_terrain_generator.site_config import SiteConfig, SiteRegistry

SITES_YAML = Path(__file__).resolve().parents[1] / "config" / "sites.yaml"


class TestSiteConfig:
    def test_from_dict_with_defaults(self):
        data = {"name": "Test Site", "lat": -89.0, "lon": 5.0, "seed": 42}
        defaults = {"size_m": 5000, "resolution": 513}
        config = SiteConfig.from_dict("test_site", data, defaults)
        assert config.site_id == "test_site"
        assert config.name == "Test Site"
        assert config.lat == -89.0
        assert config.size_m == 5000
        assert config.resolution == 513

    def test_site_overrides_defaults(self):
        data = {"name": "Big Site", "lat": -85.0, "lon": 10.0, "size_m": 10000, "seed": 1}
        defaults = {"size_m": 5000, "resolution": 513}
        config = SiteConfig.from_dict("big", data, defaults)
        assert config.size_m == 10000

    def test_enabled_defaults_to_false(self):
        data = {"name": "X", "lat": 0, "lon": 0, "seed": 1}
        config = SiteConfig.from_dict("x", data, {})
        assert config.enabled is False


class TestSiteRegistry:
    def test_load_from_yaml(self):
        registry = SiteRegistry.from_yaml(SITES_YAML)
        assert "shackleton_crater" in registry
        assert registry["shackleton_crater"].lat == -89.7

    def test_get_existing_site(self):
        registry = SiteRegistry.from_yaml(SITES_YAML)
        site = registry.get("shackleton_crater")
        assert site.name == "Peak Near Shackleton"

    def test_get_unknown_site_raises(self):
        registry = SiteRegistry.from_yaml(SITES_YAML)
        with pytest.raises(KeyError, match="nonexistent"):
            registry.get("nonexistent")

    def test_enabled_sites(self):
        registry = SiteRegistry.from_yaml(SITES_YAML)
        enabled = registry.enabled_sites()
        assert len(enabled) == 5
        ids = [s.site_id for s in enabled]
        assert "shackleton_crater" in ids

    def test_defaults_applied_to_all(self):
        registry = SiteRegistry.from_yaml(SITES_YAML)
        for site in registry.all_sites():
            assert site.size_m > 0
            assert site.resolution > 0
```

Create empty `src/lunar_terrain_generator/test/__init__.py`.

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_site_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'lunar_terrain_generator.site_config'`

- [ ] **Step 3: Implement site_config.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/site_config.py`:

```python
"""Site configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml


@dataclass(frozen=True)
class SiteConfig:
    """Configuration for a single lunar terrain site."""

    site_id: str
    name: str
    lat: float
    lon: float
    size_m: int = 5000
    resolution: int = 513
    seed: int = 42
    description: str = ""
    enabled: bool = False
    lola_url: str = ""
    lroc_wac_url: str = ""

    @classmethod
    def from_dict(
        cls, site_id: str, data: dict, defaults: dict
    ) -> SiteConfig:
        merged = {**defaults, **data}
        return cls(
            site_id=site_id,
            name=merged["name"],
            lat=float(merged["lat"]),
            lon=float(merged["lon"]),
            size_m=int(merged.get("size_m", 5000)),
            resolution=int(merged.get("resolution", 513)),
            seed=int(merged.get("seed", 42)),
            description=str(merged.get("description", "")),
            enabled=bool(merged.get("enabled", False)),
            lola_url=str(merged.get("lola_url", "")),
            lroc_wac_url=str(merged.get("lroc_wac_url", "")),
        )


class SiteRegistry:
    """Registry of available lunar terrain sites loaded from sites.yaml."""

    def __init__(self, sites: dict[str, SiteConfig]) -> None:
        self._sites = sites

    @classmethod
    def from_yaml(cls, path: Path) -> SiteRegistry:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        defaults = config.get("defaults", {})
        sites = {}
        for site_id, site_data in config.get("sites", {}).items():
            sites[site_id] = SiteConfig.from_dict(site_id, site_data, defaults)
        return cls(sites)

    def __contains__(self, site_id: str) -> bool:
        return site_id in self._sites

    def __getitem__(self, site_id: str) -> SiteConfig:
        return self._sites[site_id]

    def get(self, site_id: str) -> SiteConfig:
        if site_id not in self._sites:
            available = ", ".join(sorted(self._sites.keys()))
            raise KeyError(
                f"Unknown site '{site_id}'. Available: {available}"
            )
        return self._sites[site_id]

    def all_sites(self) -> list[SiteConfig]:
        return list(self._sites.values())

    def enabled_sites(self) -> list[SiteConfig]:
        return [s for s in self._sites.values() if s.enabled]

    def __iter__(self) -> Iterator[str]:
        return iter(self._sites)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_site_config.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/site_config.py \
        src/lunar_terrain_generator/test/
git commit -m "feat: add SiteConfig dataclass and SiteRegistry"
```

---

### Task 3: Heightmap Generation Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`
- Create: `src/lunar_terrain_generator/test/test_heightmap.py`

- [ ] **Step 1: Write test_heightmap.py**

Create `src/lunar_terrain_generator/test/test_heightmap.py`:

```python
"""Tests for the heightmap generation module."""

import numpy as np
from lunar_terrain_generator.heightmap import HeightmapGenerator


class TestSyntheticHeightmap:
    def test_shape(self):
        hm = HeightmapGenerator.generate_synthetic(size=513, seed=42)
        assert hm.shape == (513, 513)

    def test_range_normalized(self):
        hm = HeightmapGenerator.generate_synthetic(size=257, seed=42)
        assert hm.min() >= 0.0
        assert hm.max() <= 1.0

    def test_dtype_float64(self):
        hm = HeightmapGenerator.generate_synthetic(size=129, seed=42)
        assert hm.dtype == np.float64

    def test_deterministic_with_same_seed(self):
        hm1 = HeightmapGenerator.generate_synthetic(size=65, seed=99)
        hm2 = HeightmapGenerator.generate_synthetic(size=65, seed=99)
        np.testing.assert_array_equal(hm1, hm2)

    def test_different_seeds_differ(self):
        hm1 = HeightmapGenerator.generate_synthetic(size=65, seed=1)
        hm2 = HeightmapGenerator.generate_synthetic(size=65, seed=2)
        assert not np.array_equal(hm1, hm2)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_heightmap.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement heightmap.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py`:

```python
"""Heightmap generation from synthetic data or NASA LOLA GeoTIFFs."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class HeightmapGenerator:
    """Generates normalized heightmap arrays for Gazebo terrain models."""

    @staticmethod
    def generate_synthetic(size: int = 513, seed: int = 42) -> np.ndarray:
        """
        Procedurally generate a lunar-like heightmap.

        Returns a float64 array in [0, 1], shape (size, size).
        Features: base undulation, impact craters with rims, fine noise.
        """
        rng = np.random.default_rng(seed)
        x = np.linspace(-1, 1, size)
        y = np.linspace(-1, 1, size)
        xx, yy = np.meshgrid(x, y)

        terrain = (
            0.15 * np.sin(1.5 * np.pi * xx + 0.3) * np.cos(2.0 * np.pi * yy + 0.7)
            + 0.08 * np.sin(4.0 * np.pi * xx) * np.sin(3.0 * np.pi * yy)
        )

        num_craters = rng.integers(4, 9)
        for _ in range(num_craters):
            cx, cy = rng.uniform(-0.8, 0.8, 2)
            radius = rng.uniform(0.04, 0.22)
            depth = rng.uniform(0.08, 0.35)
            dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
            r_sq = radius**2
            terrain -= depth * np.exp(-dist_sq / (2 * r_sq))
            terrain += depth * 0.3 * np.exp(
                -(np.sqrt(dist_sq) - radius) ** 2 / (2 * (radius * 0.25) ** 2)
            )

        terrain += 0.03 * rng.standard_normal((size, size))

        terrain -= terrain.min()
        if terrain.max() > 0:
            terrain /= terrain.max()

        return terrain

    @staticmethod
    def from_geotiff(
        geotiff_path: Path,
        lat: float,
        lon: float,
        size_m: int,
        resolution: int,
    ) -> tuple[np.ndarray, float, float]:
        """
        Crop and resample LOLA elevation data to a heightmap.

        Returns (heightmap_float64_01, elevation_min_m, elevation_max_m).
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling

        deg_per_m_lat = 1.0 / 30_000.0
        deg_per_m_lon = deg_per_m_lat / max(np.cos(np.radians(lat)), 0.01)
        half_lat = (size_m / 2) * deg_per_m_lat
        half_lon = (size_m / 2) * deg_per_m_lon

        with rasterio.open(geotiff_path) as src:
            window = from_bounds(
                lon - half_lon, lat - half_lat,
                lon + half_lon, lat + half_lat,
                src.transform,
            )
            data = src.read(
                1,
                window=window,
                out_shape=(resolution, resolution),
                resampling=Resampling.bilinear,
            )

        elev_min = float(np.nanmin(data))
        elev_max = float(np.nanmax(data))
        data = np.nan_to_num(data, nan=elev_min)

        if elev_max > elev_min:
            heightmap = (data - elev_min) / (elev_max - elev_min)
        else:
            heightmap = np.zeros_like(data, dtype=np.float64)

        return heightmap, elev_min, elev_max
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_heightmap.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/heightmap.py \
        src/lunar_terrain_generator/test/test_heightmap.py
git commit -m "feat: add HeightmapGenerator class"
```

---

### Task 4: Albedo Generation Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/albedo.py`
- Create: `src/lunar_terrain_generator/test/test_albedo.py`

- [ ] **Step 1: Write test_albedo.py**

Create `src/lunar_terrain_generator/test/test_albedo.py`:

```python
"""Tests for the albedo generation module."""

import numpy as np
from lunar_terrain_generator.albedo import AlbedoGenerator


class TestSyntheticAlbedo:
    def test_shape_rgb(self):
        albedo = AlbedoGenerator.generate_synthetic(size=513, seed=42)
        assert albedo.shape == (513, 513, 3)

    def test_dtype_uint8(self):
        albedo = AlbedoGenerator.generate_synthetic(size=129, seed=42)
        assert albedo.dtype == np.uint8

    def test_grey_centered(self):
        albedo = AlbedoGenerator.generate_synthetic(size=513, seed=42)
        mean_val = albedo.mean()
        assert 100 < mean_val < 155, f"Mean albedo {mean_val} not in expected grey range"

    def test_channels_equal(self):
        albedo = AlbedoGenerator.generate_synthetic(size=129, seed=42)
        np.testing.assert_array_equal(albedo[:, :, 0], albedo[:, :, 1])
        np.testing.assert_array_equal(albedo[:, :, 1], albedo[:, :, 2])
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_albedo.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement albedo.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/albedo.py`:

```python
"""Albedo texture generation from synthetic data or NASA LROC WAC GeoTIFFs."""

from __future__ import annotations

from pathlib import Path

import numpy as np


class AlbedoGenerator:
    """Generates RGB albedo textures for Gazebo terrain models."""

    @staticmethod
    def generate_synthetic(size: int = 513, seed: int = 42) -> np.ndarray:
        """
        Generate a synthetic lunar albedo texture.

        Returns a uint8 RGB array of shape (size, size, 3).
        Lunar regolith is roughly uniform grey (~110-140 in 0-255 range).
        """
        rng = np.random.default_rng(seed + 1000)
        base_grey = 127
        noise = rng.integers(-12, 12, (size, size), dtype=np.int16)
        grey = np.clip(base_grey + noise, 0, 255).astype(np.uint8)
        return np.stack([grey, grey, grey], axis=-1)

    @staticmethod
    def from_geotiff(
        geotiff_path: Path,
        lat: float,
        lon: float,
        size_m: int,
        resolution: int,
    ) -> np.ndarray:
        """
        Crop and resample LROC WAC albedo data.

        Returns uint8 RGB array of shape (resolution, resolution, 3).
        """
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling

        deg_per_m_lat = 1.0 / 30_000.0
        deg_per_m_lon = deg_per_m_lat / max(np.cos(np.radians(lat)), 0.01)
        half_lat = (size_m / 2) * deg_per_m_lat
        half_lon = (size_m / 2) * deg_per_m_lon

        with rasterio.open(geotiff_path) as src:
            window = from_bounds(
                lon - half_lon, lat - half_lat,
                lon + half_lon, lat + half_lat,
                src.transform,
            )
            band_count = min(src.count, 3)
            bands = src.read(
                list(range(1, band_count + 1)),
                window=window,
                out_shape=(band_count, resolution, resolution),
                resampling=Resampling.bilinear,
            )

        if band_count == 1:
            grey = np.clip(bands[0], 0, 255).astype(np.uint8)
            return np.stack([grey, grey, grey], axis=-1)

        return np.moveaxis(bands[:3], 0, -1).astype(np.uint8)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_albedo.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/albedo.py \
        src/lunar_terrain_generator/test/test_albedo.py
git commit -m "feat: add AlbedoGenerator class"
```

---

### Task 5: Normal Map Generation Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/normal_map.py`
- Create: `src/lunar_terrain_generator/test/test_normal_map.py`

- [ ] **Step 1: Write test_normal_map.py**

Create `src/lunar_terrain_generator/test/test_normal_map.py`:

```python
"""Tests for the normal map generation module."""

import numpy as np
from lunar_terrain_generator.normal_map import NormalMapGenerator
from lunar_terrain_generator.heightmap import HeightmapGenerator


class TestNormalMap:
    def test_shape_rgb(self):
        hm = HeightmapGenerator.generate_synthetic(size=129, seed=42)
        nm = NormalMapGenerator.from_heightmap(hm)
        assert nm.shape == (129, 129, 3)

    def test_dtype_uint8(self):
        hm = HeightmapGenerator.generate_synthetic(size=129, seed=42)
        nm = NormalMapGenerator.from_heightmap(hm)
        assert nm.dtype == np.uint8

    def test_flat_surface_points_up(self):
        flat = np.full((65, 65), 0.5, dtype=np.float64)
        nm = NormalMapGenerator.from_heightmap(flat, strength=1.0)
        # Z channel (blue) should be high (~255), X/Y (red/green) near 128
        assert nm[:, :, 2].mean() > 200
        assert 120 < nm[:, :, 0].mean() < 136
        assert 120 < nm[:, :, 1].mean() < 136

    def test_strength_affects_output(self):
        hm = HeightmapGenerator.generate_synthetic(size=65, seed=42)
        nm_weak = NormalMapGenerator.from_heightmap(hm, strength=0.5)
        nm_strong = NormalMapGenerator.from_heightmap(hm, strength=5.0)
        assert nm_strong[:, :, 0].std() > nm_weak[:, :, 0].std()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_normal_map.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement normal_map.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/normal_map.py`:

```python
"""Normal map generation from heightmap data using Sobel gradients."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import sobel


class NormalMapGenerator:
    """Derives RGB normal maps from heightmap arrays."""

    @staticmethod
    def from_heightmap(
        heightmap: np.ndarray, strength: float = 2.0
    ) -> np.ndarray:
        """
        Derive an RGB normal map from a heightmap using Sobel gradients.

        Args:
            heightmap: float64 array in [0, 1], shape (H, W).
            strength: exaggeration factor for surface detail.

        Returns:
            uint8 RGB array of shape (H, W, 3) encoding surface normals.
            Convention: R=X, G=Y, B=Z mapped from [-1,1] to [0,255].
        """
        dx = sobel(heightmap, axis=1) * strength
        dy = sobel(heightmap, axis=0) * strength

        normals = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
        norms = np.linalg.norm(normals, axis=-1, keepdims=True)
        normals /= np.where(norms > 0, norms, 1.0)

        normal_map = ((normals + 1.0) * 0.5 * 255.0).clip(0, 255).astype(np.uint8)
        return normal_map
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_normal_map.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/normal_map.py \
        src/lunar_terrain_generator/test/test_normal_map.py
git commit -m "feat: add NormalMapGenerator class"
```

---

### Task 6: File Downloader Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/downloader.py`

- [ ] **Step 1: Implement downloader.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/downloader.py`:

```python
"""File download utility with local caching."""

from __future__ import annotations

from pathlib import Path


class FileDownloader:
    """Downloads remote files with local cache support."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, filename: str) -> Path:
        """Download a file if not already cached. Returns local path."""
        dest = self._cache_dir / filename
        if dest.exists():
            print(f"  Using cached: {dest}")
            return dest

        import requests

        print(f"  Downloading: {url}")
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Saved to: {dest}")
        return dest
```

- [ ] **Step 2: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/downloader.py
git commit -m "feat: add FileDownloader class with caching"
```

---

### Task 7: Model Writer Module

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/model_writer.py`
- Create: `src/lunar_terrain_generator/test/test_model_writer.py`

- [ ] **Step 1: Write test_model_writer.py**

Create `src/lunar_terrain_generator/test/test_model_writer.py`:

```python
"""Tests for the model writer module."""

import tempfile
from pathlib import Path

import numpy as np
import yaml

from lunar_terrain_generator.heightmap import HeightmapGenerator
from lunar_terrain_generator.albedo import AlbedoGenerator
from lunar_terrain_generator.normal_map import NormalMapGenerator
from lunar_terrain_generator.model_writer import ModelWriter


class TestModelWriter:
    def _generate_test_data(self, size: int = 65):
        hm = HeightmapGenerator.generate_synthetic(size=size, seed=42)
        albedo = AlbedoGenerator.generate_synthetic(size=size, seed=42)
        nm = NormalMapGenerator.from_heightmap(hm)
        return hm, albedo, nm

    def test_writes_all_files(self):
        hm, albedo, nm = self._generate_test_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "test_site")
            writer.write(
                site_id="test_site",
                display_name="Test Site",
                description="A test site",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=5000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="synthetic",
            )
            out = Path(tmpdir) / "test_site"
            assert (out / "model.sdf").exists()
            assert (out / "model.config").exists()
            assert (out / "metadata.yaml").exists()
            assert (out / "materials" / "textures" / "heightmap.png").exists()
            assert (out / "materials" / "textures" / "albedo.png").exists()
            assert (out / "materials" / "textures" / "normal.png").exists()

    def test_sdf_contains_site_id(self):
        hm, albedo, nm = self._generate_test_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "my_site")
            writer.write(
                site_id="my_site",
                display_name="My Site",
                description="Desc",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=3000,
                elevation_min=-100.0,
                elevation_max=200.0,
                lat=-85.0,
                lon=10.0,
                source="synthetic",
            )
            sdf = (Path(tmpdir) / "my_site" / "model.sdf").read_text()
            assert 'name="my_site"' in sdf
            assert "3000" in sdf

    def test_metadata_yaml_valid(self):
        hm, albedo, nm = self._generate_test_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ModelWriter(Path(tmpdir) / "meta_test")
            writer.write(
                site_id="meta_test",
                display_name="Meta Test",
                description="Testing metadata",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=5000,
                elevation_min=0.0,
                elevation_max=500.0,
                lat=-89.7,
                lon=0.0,
                source="synthetic",
            )
            with open(Path(tmpdir) / "meta_test" / "metadata.yaml") as f:
                meta = yaml.safe_load(f)
            assert meta["site_id"] == "meta_test"
            assert meta["size_m"] == 5000
            assert meta["elevation_range_m"] == 500.0
            assert meta["coordinates"]["lat"] == -89.7
            assert meta["source"] == "synthetic"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_model_writer.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement model_writer.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/model_writer.py`:

```python
"""Gazebo SDF model file writer (SDF, config, metadata, textures)."""

from __future__ import annotations

from pathlib import Path
from string import Template

import numpy as np
import yaml
from PIL import Image

_MODEL_SDF_TEMPLATE = Template("""\
<?xml version="1.0"?>
<sdf version="1.9">
  <model name="${site_id}">
    <static>true</static>
    <link name="terrain_link">
      <collision name="terrain_collision">
        <geometry>
          <heightmap>
            <uri>model://${site_id}/materials/textures/heightmap.png</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
          </heightmap>
        </geometry>
      </collision>
      <visual name="terrain_visual">
        <geometry>
          <heightmap>
            <uri>model://${site_id}/materials/textures/heightmap.png</uri>
            <size>${size_x} ${size_y} ${size_z}</size>
            <pos>0 0 ${z_offset}</pos>
            <texture>
              <diffuse>model://${site_id}/materials/textures/albedo.png</diffuse>
              <normal>model://${site_id}/materials/textures/normal.png</normal>
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
  <sdf version="1.9">model.sdf</sdf>
  <author>
    <name>Artemis Mission Simulator</name>
  </author>
  <description>${description}</description>
</model>
""")


class ModelWriter:
    """Writes a complete Gazebo SDF terrain model to disk."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def write(
        self,
        site_id: str,
        display_name: str,
        description: str,
        heightmap: np.ndarray,
        albedo: np.ndarray,
        normal_map: np.ndarray,
        size_m: int,
        elevation_min: float,
        elevation_max: float,
        lat: float,
        lon: float,
        source: str,
    ) -> None:
        """Write all model files (SDF, config, textures, metadata)."""
        textures_dir = self._output_dir / "materials" / "textures"
        textures_dir.mkdir(parents=True, exist_ok=True)

        # 16-bit grayscale heightmap PNG
        hm_16bit = (heightmap * 65535).clip(0, 65535).astype(np.uint16)
        Image.fromarray(hm_16bit, mode="I;16").save(textures_dir / "heightmap.png")

        # RGB albedo PNG
        Image.fromarray(albedo, mode="RGB").save(textures_dir / "albedo.png")

        # RGB normal map PNG
        Image.fromarray(normal_map, mode="RGB").save(textures_dir / "normal.png")

        elevation_range = max(elevation_max - elevation_min, 1.0)

        sdf_content = _MODEL_SDF_TEMPLATE.substitute(
            site_id=site_id,
            size_x=size_m,
            size_y=size_m,
            size_z=f"{elevation_range:.1f}",
            z_offset=f"{elevation_min:.1f}",
        )
        (self._output_dir / "model.sdf").write_text(sdf_content)

        config_content = _MODEL_CONFIG_TEMPLATE.substitute(
            display_name=display_name,
            description=description,
        )
        (self._output_dir / "model.config").write_text(config_content)

        metadata = {
            "site_id": site_id,
            "display_name": display_name,
            "description": description,
            "coordinates": {"lat": float(lat), "lon": float(lon)},
            "size_m": size_m,
            "resolution": int(heightmap.shape[0]),
            "elevation_min_m": round(elevation_min, 2),
            "elevation_max_m": round(elevation_max, 2),
            "elevation_range_m": round(elevation_range, 2),
            "source": source,
        }
        with open(self._output_dir / "metadata.yaml", "w") as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

        print(f"  Model written to: {self._output_dir}")
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd src/lunar_terrain_generator && python -m pytest test/test_model_writer.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/model_writer.py \
        src/lunar_terrain_generator/test/test_model_writer.py
git commit -m "feat: add ModelWriter class for SDF generation"
```

---

### Task 8: Terrain Generator Orchestrator

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py`

- [ ] **Step 1: Implement terrain_generator.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py`:

```python
"""Orchestrates the full terrain generation pipeline."""

from __future__ import annotations

from pathlib import Path

from .site_config import SiteConfig
from .heightmap import HeightmapGenerator
from .albedo import AlbedoGenerator
from .normal_map import NormalMapGenerator
from .downloader import FileDownloader
from .model_writer import ModelWriter


class TerrainGenerator:
    """Coordinates terrain generation from config to finished Gazebo model."""

    def __init__(
        self,
        output_dir: Path,
        cache_dir: Path | None = None,
    ) -> None:
        self._output_dir = output_dir
        self._cache_dir = cache_dir

    def generate(self, site: SiteConfig, synthetic: bool = False) -> Path:
        """
        Generate a complete Gazebo terrain model for one site.

        Returns the path to the generated model directory.
        """
        print(f"\n=== Generating: {site.name} ({site.site_id}) ===")
        print(f"    Lat: {site.lat}, Lon: {site.lon}, "
              f"Size: {site.size_m}m, Resolution: {site.resolution}px")

        if synthetic:
            heightmap, albedo, elevation_min, elevation_max, source = (
                self._generate_synthetic(site)
            )
        else:
            heightmap, albedo, elevation_min, elevation_max, source = (
                self._generate_from_real_data(site)
            )

        normal_map = NormalMapGenerator.from_heightmap(heightmap)

        model_dir = self._output_dir / site.site_id
        writer = ModelWriter(model_dir)
        writer.write(
            site_id=site.site_id,
            display_name=site.name,
            description=site.description,
            heightmap=heightmap,
            albedo=albedo,
            normal_map=normal_map,
            size_m=site.size_m,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            lat=site.lat,
            lon=site.lon,
            source=source,
        )
        return model_dir

    def _generate_synthetic(self, site: SiteConfig):
        print("  Mode: synthetic (procedural terrain)")
        heightmap = HeightmapGenerator.generate_synthetic(
            site.resolution, site.seed
        )
        albedo = AlbedoGenerator.generate_synthetic(
            site.resolution, site.seed
        )
        return heightmap, albedo, 0.0, 500.0, "synthetic"

    def _generate_from_real_data(self, site: SiteConfig):
        print("  Mode: real data (NASA LOLA + LROC WAC)")
        if self._cache_dir is None:
            raise ValueError("cache_dir is required for real data mode")

        downloader = FileDownloader(self._cache_dir)

        lola_file = downloader.download(site.lola_url, "lola_dem.tif")
        heightmap, elev_min, elev_max = HeightmapGenerator.from_geotiff(
            lola_file, site.lat, site.lon, site.size_m, site.resolution
        )

        lroc_file = downloader.download(site.lroc_wac_url, "lroc_wac.tif")
        albedo = AlbedoGenerator.from_geotiff(
            lroc_file, site.lat, site.lon, site.size_m, site.resolution
        )

        return heightmap, albedo, elev_min, elev_max, "nasa_lola_lroc"
```

- [ ] **Step 2: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/terrain_generator.py
git commit -m "feat: add TerrainGenerator orchestrator class"
```

---

### Task 9: CLI Entry Point

**Files:**
- Create: `src/lunar_terrain_generator/lunar_terrain_generator/cli.py`

- [ ] **Step 1: Implement cli.py**

Create `src/lunar_terrain_generator/lunar_terrain_generator/cli.py`:

```python
"""Command-line interface for the lunar terrain generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .site_config import SiteConfig, SiteRegistry
from .terrain_generator import TerrainGenerator


def _default_sites_yaml() -> Path:
    """Locate sites.yaml — prefer installed share location, fall back to source tree."""
    # Installed via ament (share/lunar_terrain_generator/config/sites.yaml)
    try:
        from ament_index_python.packages import get_package_share_directory
        share = Path(get_package_share_directory("lunar_terrain_generator"))
        installed = share / "config" / "sites.yaml"
        if installed.exists():
            return installed
    except Exception:
        pass
    # Source tree fallback
    return Path(__file__).resolve().parents[1] / "config" / "sites.yaml"


def _default_output_dir() -> Path:
    """Default output: models/ directory next to config/."""
    return Path(__file__).resolve().parents[1] / "models"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Gazebo SDF terrain models from NASA lunar data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  generate_lunar_sdf --site shackleton_crater --synthetic\n"
            "  generate_lunar_sdf --all --synthetic\n"
            "  generate_lunar_sdf --lat -89.7 --lon 0.0 --size 5000 "
            "--name my_site --synthetic\n"
            "  generate_lunar_sdf --list\n"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--site", help="Site ID from sites.yaml")
    group.add_argument(
        "--all", action="store_true", help="Generate all enabled sites"
    )
    group.add_argument(
        "--lat", type=float,
        help="Custom latitude (use with --lon, --size, --name)",
    )
    group.add_argument(
        "--list", action="store_true", help="List available sites and exit"
    )

    parser.add_argument("--lon", type=float, help="Custom longitude")
    parser.add_argument(
        "--size", type=int, default=5000,
        help="Tile side length in meters (default: 5000)",
    )
    parser.add_argument("--name", help="Custom site ID/name")
    parser.add_argument(
        "--synthetic", action="store_true",
        help="Use procedural terrain instead of NASA data",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for synthetic mode (default: 42)",
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output directory"
    )
    parser.add_argument(
        "--sites-yaml", type=Path, default=None, help="Path to sites.yaml"
    )
    parser.add_argument(
        "--cache-dir", type=Path, default=None,
        help="Cache directory for downloaded data",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    sites_yaml = args.sites_yaml or _default_sites_yaml()
    output_dir = args.output or _default_output_dir()
    registry = SiteRegistry.from_yaml(sites_yaml)

    if args.list:
        _print_sites(registry)
        return

    generator = TerrainGenerator(
        output_dir=output_dir, cache_dir=args.cache_dir
    )

    if args.all:
        for site in registry.enabled_sites():
            generator.generate(site, synthetic=args.synthetic)
    elif args.site:
        site = registry.get(args.site)
        generator.generate(site, synthetic=args.synthetic)
    elif args.lat is not None:
        if args.lon is None or args.name is None:
            parser.error("--lat requires --lon and --name")
        site = SiteConfig(
            site_id=args.name,
            name=args.name,
            lat=args.lat,
            lon=args.lon,
            size_m=args.size,
            resolution=513,
            seed=args.seed,
            description=f"Custom site at ({args.lat}, {args.lon})",
        )
        generator.generate(site, synthetic=args.synthetic)

    print("\nDone!")


def _print_sites(registry: SiteRegistry) -> None:
    print(f"{'ID':<30} {'Name':<30} {'Lat':>8} {'Lon':>8} {'Enabled'}")
    print("-" * 90)
    for site in registry.all_sites():
        enabled = "✓" if site.enabled else ""
        print(
            f"{site.site_id:<30} {site.name:<30} "
            f"{site.lat:>8.1f} {site.lon:>8.1f} {enabled:>7}"
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/lunar_terrain_generator/lunar_terrain_generator/cli.py
git commit -m "feat: add argparse CLI entry point with --list command"
```

---

### Task 10: Sites Config, Env Hooks, Models, and README

**Files:**
- Move: `src/lunar_simulation/scripts/generate_lunar_sdf/sites.yaml` → `src/lunar_terrain_generator/config/sites.yaml`
- Move: `src/lunar_simulation/models/*` → `src/lunar_terrain_generator/models/`
- Create: `src/lunar_terrain_generator/hooks/lunar_terrain_generator.dsv`
- Create: `src/lunar_terrain_generator/hooks/lunar_terrain_generator.sh`
- Move: `src/lunar_simulation/scripts/generate_lunar_sdf/README.md` → `src/lunar_terrain_generator/README.md`

- [ ] **Step 1: Copy sites.yaml**

```bash
cp src/lunar_simulation/scripts/generate_lunar_sdf/sites.yaml src/lunar_terrain_generator/config/sites.yaml
```

- [ ] **Step 2: Move models directory**

```bash
cp -r src/lunar_simulation/models/* src/lunar_terrain_generator/models/
```

- [ ] **Step 3: Create DSV env hook**

Create `src/lunar_terrain_generator/hooks/lunar_terrain_generator.dsv`:

```
prepend-non-duplicate;GZ_SIM_RESOURCE_PATH;share/lunar_terrain_generator/models
```

- [ ] **Step 4: Create shell env hook**

Create `src/lunar_terrain_generator/hooks/lunar_terrain_generator.sh`:

```bash
# Auto-generated env hook for lunar_terrain_generator
# Sets GZ_SIM_RESOURCE_PATH so Gazebo can find installed terrain models

ament_prepend_unique_value GZ_SIM_RESOURCE_PATH "$AMENT_CURRENT_PREFIX/share/lunar_terrain_generator/models"
```

- [ ] **Step 5: Create README.md**

Create `src/lunar_terrain_generator/README.md`:

```markdown
# lunar_terrain_generator

ROS 2 Python package for generating Gazebo SDF terrain models from NASA lunar
satellite data or procedural generation. Ships with 5 pre-built terrain models
for NASA Artemis candidate landing sites.

## Environment Hook

This package automatically sets `GZ_SIM_RESOURCE_PATH` to include the installed
models directory when you source the workspace. No manual path configuration
is needed.

## CLI Usage

The package installs a `generate_lunar_sdf` console script:

### List available sites

```bash
generate_lunar_sdf --list
```

### Generate a specific preset site (synthetic/offline)

```bash
generate_lunar_sdf --site shackleton_crater --synthetic
```

### Generate all enabled preset sites

```bash
generate_lunar_sdf --all --synthetic
```

### Generate from real NASA data

```bash
generate_lunar_sdf --site shackleton_crater
```

### Generate from custom coordinates

```bash
generate_lunar_sdf --lat -89.7 --lon 0.0 --size 5000 --name my_site --synthetic
```

## Output Structure

Each site generates a complete Gazebo model directory:

```
models/<site_id>/
├── model.sdf
├── model.config
├── metadata.yaml
└── materials/textures/
    ├── heightmap.png     # 16-bit grayscale (513×513)
    ├── albedo.png        # RGB diffuse texture (513×513)
    └── normal.png        # RGB normal map (513×513)
```

## How It Works

1. **Heightmap**: NASA LOLA elevation data (or synthetic noise) → normalized to
   16-bit grayscale PNG. Gazebo creates 3D geometry where brightness = height.

2. **Albedo**: NASA LROC WAC reflectance (or synthetic grey) → RGB PNG diffuse
   color texture.

3. **Normal map**: Sobel filter on heightmap → adds perceived surface detail
   without extra geometry.

4. **SDF model**: References the three PNGs and defines terrain size, collision
   geometry, and visual material.

## Data Sources

- **LOLA**: Elevation at ~60 m/px — https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/
- **LROC WAC**: Albedo at ~100 m/px — https://wms.lroc.asu.edu/lroc/

## Running Tests

```bash
cd src/lunar_terrain_generator
python -m pytest test/ -v
```
```

- [ ] **Step 6: Run all tests**

```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/lunar_terrain_generator/config/ src/lunar_terrain_generator/models/ \
        src/lunar_terrain_generator/hooks/ src/lunar_terrain_generator/README.md
git commit -m "feat: add sites config, models, env hooks, and README"
```

---

### Task 11: Create artemis_mission_launcher Package

**Files:**
- Create: `src/artemis_mission_launcher/package.xml`
- Create: `src/artemis_mission_launcher/CMakeLists.txt`
- Move: `src/lunar_simulation/launch/lunar_surface.launch.py` → adapted
- Move: `src/lunar_simulation/launch/world_builder.launch.py` → adapted
- Move: `src/lunar_simulation/worlds/lunar_surface.world`
- Move: `src/lunar_simulation/config/gui.config`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/artemis_mission_launcher/{launch,worlds,config}
```

- [ ] **Step 2: Create package.xml**

Create `src/artemis_mission_launcher/package.xml`:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>artemis_mission_launcher</name>
  <version>0.1.0</version>
  <description>Launch files and Gazebo worlds for the Artemis Mission Simulator</description>
  <maintainer email="todo@example.com">Artemis Simulator Contributors</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <exec_depend>ros2launch</exec_depend>
  <exec_depend>ros_gz_sim</exec_depend>
  <exec_depend>lunar_terrain_generator</exec_depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

- [ ] **Step 3: Create CMakeLists.txt**

Create `src/artemis_mission_launcher/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.8)
project(artemis_mission_launcher)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  worlds
  config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

- [ ] **Step 4: Copy and adapt world file**

```bash
cp src/lunar_simulation/worlds/lunar_surface.world src/artemis_mission_launcher/worlds/lunar_surface.world
```

No changes needed — the world file is package-independent.

- [ ] **Step 5: Copy GUI config**

```bash
cp src/lunar_simulation/config/gui.config src/artemis_mission_launcher/config/gui.config
```

- [ ] **Step 6: Create adapted lunar_surface.launch.py**

Create `src/artemis_mission_launcher/launch/lunar_surface.launch.py`:

```python
"""
Launch Gazebo with a pre-loaded lunar terrain model.

Usage:
    ros2 launch artemis_mission_launcher lunar_surface.launch.py
    ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=nobile_rim_1
"""

import atexit
import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    site = LaunchConfiguration("site").perform(context)
    launcher_share = FindPackageShare("artemis_mission_launcher").perform(context)
    terrain_share = FindPackageShare("lunar_terrain_generator").perform(context)

    world_file = os.path.join(launcher_share, "worlds", "lunar_surface.world")
    model_path = os.path.join(terrain_share, "models")

    site_model_dir = os.path.join(model_path, site)
    if not os.path.isdir(site_model_dir):
        available = [
            d for d in os.listdir(model_path)
            if os.path.isdir(os.path.join(model_path, d))
        ]
        raise RuntimeError(
            f"Site '{site}' not found in {model_path}. "
            f"Available sites: {', '.join(sorted(available))}"
        )

    with open(world_file, "r") as f:
        world_content = f.read()

    include_sdf = (
        f'    <include>\n'
        f'      <uri>model://{site}</uri>\n'
        f'      <pose>0 0 0 0 0 0</pose>\n'
        f'    </include>\n'
    )
    modified_world = world_content.replace("</world>", include_sdf + "  </world>")

    tmp_path = os.path.join(tempfile.gettempdir(), f"lunar_{site}.world")
    with open(tmp_path, "w") as f:
        f.write(modified_world)
    atexit.register(lambda p=tmp_path: os.remove(p) if os.path.exists(p) else None)

    gz_sim = ExecuteProcess(
        cmd=["gz", "sim", "-r", tmp_path],
        additional_env={"GZ_SIM_RESOURCE_PATH": model_path},
        output="screen",
    )

    return [
        LogInfo(msg=f"Loading lunar terrain: {site}"),
        gz_sim,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "site",
            default_value="shackleton_crater",
            description="Lunar site to load (e.g., shackleton_crater, nobile_rim_1)",
        ),
        OpaqueFunction(function=launch_setup),
    ])
```

- [ ] **Step 7: Create adapted world_builder.launch.py**

Create `src/artemis_mission_launcher/launch/world_builder.launch.py`:

```python
"""
Launch Gazebo in world-builder sandbox mode with the Resource Spawner GUI.

Users can browse and place terrain models interactively.

Usage:
    ros2 launch artemis_mission_launcher world_builder.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo, OpaqueFunction
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    launcher_share = FindPackageShare("artemis_mission_launcher").perform(context)
    terrain_share = FindPackageShare("lunar_terrain_generator").perform(context)

    world_file = os.path.join(launcher_share, "worlds", "lunar_surface.world")
    gui_config = os.path.join(launcher_share, "config", "gui.config")
    model_path = os.path.join(terrain_share, "models")

    gz_sim = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r",
            world_file,
            "--gui-config", gui_config,
        ],
        additional_env={"GZ_SIM_RESOURCE_PATH": model_path},
        output="screen",
    )

    return [
        LogInfo(msg="Launching Gazebo in world-builder mode with Resource Spawner"),
        gz_sim,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup),
    ])
```

- [ ] **Step 8: Commit**

```bash
git add src/artemis_mission_launcher/
git commit -m "feat: create artemis_mission_launcher package with launch files and worlds"
```

---

### Task 12: Update Supporting Files

**Files:**
- Modify: `docker/Dockerfile`
- Modify: `docker/docker-compose.yml`
- Modify: `colcon.meta`
- Modify: `README.md`

- [ ] **Step 1: Update Dockerfile**

Replace `docker/Dockerfile` contents with:

```dockerfile
FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

# Install Gazebo Harmonic + ROS-Gazebo integration
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-yaml \
    python3-pil \
    gdal-bin \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python deps for terrain tool
RUN pip3 install --break-system-packages \
    requests>=2.28 \
    pytest>=7.0 \
    && pip3 install --break-system-packages --no-deps rasterio>=1.3

WORKDIR /ws

# Copy and build workspace
COPY . /ws/
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Source on shell entry (env hooks auto-set GZ_SIM_RESOURCE_PATH)
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /ws/install/setup.bash" >> /root/.bashrc

ENTRYPOINT ["/bin/bash"]
```

Note: The `GZ_SIM_RESOURCE_PATH` line is removed from the Dockerfile since the env hook in `lunar_terrain_generator` now handles it automatically.

- [ ] **Step 2: Update colcon.meta**

Replace `colcon.meta` contents with:

```json
{
  "names": {
    "artemis_mission_launcher": {
      "cmake-args": ["-DCMAKE_BUILD_TYPE=Release"]
    }
  }
}
```

- [ ] **Step 3: Update README.md**

Replace `README.md` contents with:

```markdown
# Artemis Mission Simulator

An open-source Gazebo-based simulation platform for NASA's Artemis programme.
Launch Gazebo with realistic lunar terrain and start simulating missions immediately.

**Stack:** ROS 2 Jazzy · Gazebo Harmonic · Docker

## Quick Start

### Prerequisites
- Docker & Docker Compose
- X11 display server (Linux) or XQuartz (macOS)
- (Optional) NVIDIA GPU + nvidia-container-toolkit

### Build and Run

```bash
# Allow X11 forwarding
xhost +local:docker

# Build the Docker image
cd docker
docker compose build

# Launch with a specific terrain site
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=shackleton_crater"

# Or launch in world-builder sandbox mode
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch artemis_mission_launcher world_builder.launch.py"
```

### NVIDIA GPU

```bash
docker compose run sim-nvidia bash -c "source /ws/install/setup.bash && \
  ros2 launch artemis_mission_launcher lunar_surface.launch.py"
```

## Available Terrain Sites

| Site | Launch ID | Description |
|------|-----------|-------------|
| Peak Near Shackleton | `shackleton_crater` | Most studied site, rim of Shackleton crater |
| Nobile Rim 1 | `nobile_rim_1` | Candidate for Artemis IV/V landing |
| Connecting Ridge | `connecting_ridge` | Ridge between Shackleton and de Gerlache |
| de Gerlache Rim 1 | `de_gerlache_rim_1` | Western rim of de Gerlache crater |
| Malapert Massif | `malapert_massif` | Elevated massif with near-continuous sunlight |

## Launch Modes

### Quick Start
Load a pre-built terrain and start simulating:
```bash
ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=nobile_rim_1
```

### World Builder
Open an empty lunar world with the Resource Spawner panel to place terrain interactively:
```bash
ros2 launch artemis_mission_launcher world_builder.launch.py
```

## Project Structure

```
src/
  lunar_terrain_generator/      # ROS 2 Python package
    lunar_terrain_generator/    # Modular terrain generation tool
    models/                     # Pre-built SDF terrain models
    config/                     # Site definitions (sites.yaml)
    hooks/                      # Env hooks (auto-sets GZ_SIM_RESOURCE_PATH)
    test/                       # Unit tests
  artemis_mission_launcher/     # ROS 2 CMake package
    launch/                     # ROS 2 launch files
    worlds/                     # Gazebo world files
    config/                     # Gazebo GUI configs
docker/                         # Dockerfile + Compose
```

## Generating New Terrain

The `lunar_terrain_generator` package provides a CLI tool:

```bash
# List available sites
generate_lunar_sdf --list

# Generate a site with synthetic terrain (offline)
generate_lunar_sdf --site shackleton_crater --synthetic

# Generate all enabled sites
generate_lunar_sdf --all --synthetic

# Custom coordinates
generate_lunar_sdf --lat -89.7 --lon 0.0 --size 5000 --name my_site --synthetic
```

See [src/lunar_terrain_generator/README.md](src/lunar_terrain_generator/README.md) for details.

## License

Apache 2.0 — see [LICENSE](LICENSE).
```

- [ ] **Step 4: Commit**

```bash
git add docker/Dockerfile colcon.meta README.md
git commit -m "chore: update Dockerfile, colcon.meta, and README for new packages"
```

---

### Task 13: Remove Old Package and Final Verification

**Files:**
- Delete: `src/lunar_simulation/` (entire directory)

- [ ] **Step 1: Remove old package**

```bash
rm -rf src/lunar_simulation/
```

- [ ] **Step 2: Run all tests**

```bash
cd src/lunar_terrain_generator && python -m pytest test/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Verify package structure**

```bash
find src/ -type f -name "*.py" -o -name "*.xml" -o -name "*.cmake" -o -name "*.cfg" \
    -o -name "*.dsv" -o -name "*.sh" -o -name "*.yaml" -o -name "*.world" \
    -o -name "*.config" | sort
```

Expected: all files under `src/lunar_terrain_generator/` and `src/artemis_mission_launcher/`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove old lunar_simulation package

BREAKING CHANGE: The monolithic lunar_simulation package has been split into:
- lunar_terrain_generator: terrain tool + models + env hooks
- artemis_mission_launcher: launch files + worlds + GUI config"
```
