# Lunar Terrain Simulation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Dockerized Gazebo Harmonic simulation with 5 pre-built NASA lunar terrain models that users can launch immediately.

**Architecture:** Single ROS 2 package `lunar_simulation` containing pre-built SDF terrain models, Gazebo worlds, launch files, and a developer Python script (`generate_lunar_sdf`) for creating new terrain models from NASA LOLA/LROC data. Two launch modes: quick-start with a site argument, and sandbox with Gazebo's Resource Spawner GUI.

**Tech Stack:** ROS 2 Jazzy · Gazebo Harmonic · Docker · Python (numpy, scipy, Pillow, rasterio, requests, PyYAML) · Apache 2.0

---

## File Structure

```
artemis_mission_simulator/
├── src/
│   └── lunar_simulation/                          # Single ROS 2 ament_cmake package
│       ├── package.xml
│       ├── CMakeLists.txt
│       ├── models/                                # Pre-built terrain SDF models (~2-3 MB each)
│       │   ├── shackleton_crater/
│       │   │   ├── model.sdf                      # Heightmap geometry + PBR material
│       │   │   ├── model.config                   # Gazebo model metadata
│       │   │   ├── metadata.yaml                  # Source coords, elevation range, provenance
│       │   │   └── materials/
│       │   │       └── textures/
│       │   │           ├── heightmap.png           # 16-bit grayscale, 513×513
│       │   │           ├── albedo.png              # RGB diffuse texture, 513×513
│       │   │           └── normal.png              # RGB normal map, 513×513
│       │   ├── nobile_rim_1/                       # Same structure as above
│       │   ├── connecting_ridge/
│       │   ├── de_gerlache_rim_1/
│       │   └── malapert_massif/
│       ├── worlds/
│       │   └── lunar_surface.world                 # Base world: lunar gravity, Sun, plugins
│       ├── launch/
│       │   ├── lunar_surface.launch.py             # Quick start: site:=shackleton_crater
│       │   └── world_builder.launch.py             # Sandbox with Resource Spawner GUI
│       ├── config/
│       │   └── gui.config                          # Gazebo GUI layout with Resource Spawner
│       └── scripts/
│           └── generate_lunar_sdf/                 # Developer tool (not installed by colcon)
│               ├── generate_lunar_sdf.py           # Main script
│               ├── requirements.txt                # Python dependencies
│               ├── sites.yaml                      # 13 NASA candidate regions
│               ├── tests/
│               │   └── test_terrain_processing.py
│               └── README.md                       # Usage docs for contributors
├── docker/
│   ├── Dockerfile                                  # ros:jazzy + gz-harmonic + Python deps
│   ├── docker-compose.yml                          # X11 forwarding + optional NVIDIA GPU
│   └── .dockerignore
├── data/                                           # Gitignored: raw GeoTIFF cache
├── README.md                                       # Project overview + quickstart
├── READING_LIST.md                                 # Theory/background for all concepts
├── LICENSE                                         # Apache 2.0
├── .gitignore
└── colcon.meta
```

---

## Terrain Data Pipeline

### Data Sources

| Data       | Instrument | Resolution | Format         | Use                    |
|------------|-----------|------------|----------------|------------------------|
| Elevation  | LOLA      | ~60 m/px   | GeoTIFF (PDS)  | 16-bit PNG heightmap   |
| Albedo     | LROC WAC  | ~100 m/px  | GeoTIFF (ASU)  | RGB diffuse texture    |
| Normal map | Derived   | —          | —              | Sobel from heightmap   |

### Pre-Built Sites (5 models, all within 6° of South Pole)

| Site                 | ID                   | Lat      | Lon    | Size    |
|----------------------|----------------------|----------|--------|---------|
| Peak Near Shackleton | shackleton_crater    | -89.7°S  | 0°E    | 5×5 km  |
| Nobile Rim 1         | nobile_rim_1         | -85.3°S  | 53°E   | 5×5 km  |
| Connecting Ridge     | connecting_ridge     | -88.5°S  | -10°E  | 5×5 km  |
| de Gerlache Rim 1    | de_gerlache_rim_1    | -88.5°S  | -87°E  | 5×5 km  |
| Malapert Massif      | malapert_massif      | -86.0°S  | 3°E    | 5×5 km  |

### generate_lunar_sdf Modes

- **Real data** (default): Downloads LOLA + LROC WAC → crop → reproject → resample → normalize → export PNG + SDF
- **Synthetic** (`--synthetic`): Procedural lunar terrain with craters + noise. Works offline, good for testing.

---

### Task 1: Repository Initialization

**Files:**
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `colcon.meta`

- [ ] **Step 1: Clean up stale empty directories**

```bash
rm -rf src/artemis_terrain src/artemis_gazebo src/artemis_description src/artemis_msgs src/artemis_common
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Colcon
build/
install/
log/

# Python
__pycache__/
*.pyc
*.egg-info/
.venv/
venv/

# Raw satellite data cache
data/*.tif
data/*.img
data/*.lbl
data/*.jp2

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Create LICENSE (Apache 2.0)**

```bash
curl -sL https://www.apache.org/licenses/LICENSE-2.0.txt > LICENSE
```

If offline, create with the standard Apache 2.0 header text.

- [ ] **Step 4: Create colcon.meta**

```json
{
  "names": {
    "lunar_simulation": {
      "cmake-args": ["-DCMAKE_BUILD_TYPE=Release"]
    }
  }
}
```

- [ ] **Step 5: Initialize git repo**

```bash
git init
git add .gitignore LICENSE colcon.meta
git commit -m "chore: initialize repository with gitignore, license, and colcon config"
```

---

### Task 2: Docker Environment

**Files:**
- Create: `docker/Dockerfile`
- Create: `docker/docker-compose.yml`
- Create: `docker/.dockerignore`

- [ ] **Step 1: Create Dockerfile**

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
    rasterio>=1.3 \
    requests>=2.28

WORKDIR /ws

# Copy and build workspace
COPY . /ws/
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Source on shell entry
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /ws/install/setup.bash" >> /root/.bashrc && \
    echo 'export GZ_SIM_RESOURCE_PATH=/ws/install/lunar_simulation/share/lunar_simulation/models:${GZ_SIM_RESOURCE_PATH}' >> /root/.bashrc

ENTRYPOINT ["/bin/bash"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
services:
  sim:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    environment:
      - DISPLAY=${DISPLAY}
      - QT_X11_NO_MITSHM=1
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    network_mode: host
    stdin_open: true
    tty: true

  # Use this service for NVIDIA GPU support (requires nvidia-container-toolkit)
  sim-nvidia:
    extends:
      service: sim
    environment:
      - DISPLAY=${DISPLAY}
      - QT_X11_NO_MITSHM=1
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

- [ ] **Step 3: Create .dockerignore**

```
build/
install/
log/
.git/
data/*.tif
data/*.img
__pycache__/
*.pyc
.vscode/
.idea/
```

- [ ] **Step 4: Commit**

```bash
git add docker/
git commit -m "chore: add Docker setup with ROS 2 Jazzy and Gazebo Harmonic"
```

---

### Task 3: ROS 2 Package Scaffold

**Files:**
- Create: `src/lunar_simulation/package.xml`
- Create: `src/lunar_simulation/CMakeLists.txt`
- Create: directory structure for models, worlds, launch, config, scripts

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/lunar_simulation/{models,worlds,launch,config}
mkdir -p src/lunar_simulation/scripts/generate_lunar_sdf/tests
```

- [ ] **Step 2: Create package.xml**

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>lunar_simulation</name>
  <version>0.1.0</version>
  <description>Lunar surface simulation for NASA Artemis programme using Gazebo Harmonic</description>
  <maintainer email="todo@example.com">Artemis Simulator Contributors</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <exec_depend>ros2launch</exec_depend>
  <exec_depend>ros_gz_sim</exec_depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

- [ ] **Step 3: Create CMakeLists.txt**

```cmake
cmake_minimum_required(VERSION 3.8)
project(lunar_simulation)

find_package(ament_cmake REQUIRED)

# Install all resource directories to the package share
install(DIRECTORY
  models
  worlds
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

- [ ] **Step 4: Commit**

```bash
git add src/lunar_simulation/
git commit -m "feat: scaffold lunar_simulation ROS 2 package"
```

---

### Task 4: Terrain Generation Tool — Site Config and Dependencies

**Files:**
- Create: `src/lunar_simulation/scripts/generate_lunar_sdf/sites.yaml`
- Create: `src/lunar_simulation/scripts/generate_lunar_sdf/requirements.txt`

- [ ] **Step 1: Create sites.yaml**

All 13 NASA Artemis III candidate landing regions. The 5 priority sites have `enabled: true`.

```yaml
# NASA Artemis III Candidate Landing Regions
# Source: NASA Artemis III Science Definition Team Report (2020)
# All sites are near the lunar South Pole (within ~6 degrees)

defaults:
  size_m: 5000           # 5 km × 5 km tile
  resolution: 513        # Gazebo heightmap: power-of-2 + 1
  lola_url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_20m_float.img"
  lroc_wac_url: "https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LROC_WAC_Mosaic_Global_303ppd_v02.tif"

sites:
  shackleton_crater:
    name: "Peak Near Shackleton"
    enabled: true
    lat: -89.7
    lon: 0.0
    size_m: 5000
    description: "Most studied Artemis candidate site, rim of Shackleton crater near South Pole"
    seed: 42

  nobile_rim_1:
    name: "Nobile Rim 1"
    enabled: true
    lat: -85.3
    lon: 53.0
    size_m: 5000
    description: "Rim of Nobile crater, candidate for Artemis IV/V landing"
    seed: 43

  connecting_ridge:
    name: "Connecting Ridge"
    enabled: true
    lat: -88.5
    lon: -10.0
    size_m: 5000
    description: "Ridge between Shackleton and de Gerlache craters"
    seed: 44

  de_gerlache_rim_1:
    name: "de Gerlache Rim 1"
    enabled: true
    lat: -88.5
    lon: -87.0
    size_m: 5000
    description: "Western rim of de Gerlache crater"
    seed: 45

  malapert_massif:
    name: "Malapert Massif"
    enabled: true
    lat: -86.0
    lon: 3.0
    size_m: 5000
    description: "Elevated massif with near-continuous sunlight"
    seed: 46

  # --- Future sites (enabled: false) ---

  faustini_rim_a:
    name: "Faustini Rim A"
    enabled: false
    lat: -87.2
    lon: 77.0
    size_m: 5000
    description: "Rim of Faustini crater"
    seed: 47

  connecting_ridge_extension:
    name: "Connecting Ridge Extension"
    enabled: false
    lat: -88.0
    lon: -15.0
    size_m: 5000
    description: "Extended ridge area between Shackleton and de Gerlache"
    seed: 48

  de_gerlache_rim_2:
    name: "de Gerlache Rim 2"
    enabled: false
    lat: -88.7
    lon: -70.0
    size_m: 5000
    description: "Second candidate site on de Gerlache rim"
    seed: 49

  de_gerlache_kocher_massif:
    name: "de Gerlache-Kocher Massif"
    enabled: false
    lat: -88.0
    lon: -80.0
    size_m: 5000
    description: "Massif between de Gerlache and Kocher craters"
    seed: 50

  haworth:
    name: "Haworth"
    enabled: false
    lat: -87.5
    lon: -5.0
    size_m: 5000
    description: "Near Haworth crater"
    seed: 51

  leibnitz_beta_plateau:
    name: "Leibnitz Beta Plateau"
    enabled: false
    lat: -85.0
    lon: 37.0
    size_m: 5000
    description: "Plateau near Leibnitz Beta crater"
    seed: 52

  nobile_rim_2:
    name: "Nobile Rim 2"
    enabled: false
    lat: -85.5
    lon: 48.0
    size_m: 5000
    description: "Second candidate on Nobile rim"
    seed: 53

  amundsen_rim:
    name: "Amundsen Rim"
    enabled: false
    lat: -84.5
    lon: -85.0
    size_m: 5000
    description: "Rim of Amundsen crater"
    seed: 54
```

- [ ] **Step 2: Create requirements.txt**

```
numpy>=1.24
scipy>=1.10
Pillow>=9.0
rasterio>=1.3
requests>=2.28
PyYAML>=6.0
```

- [ ] **Step 3: Commit**

```bash
git add src/lunar_simulation/scripts/generate_lunar_sdf/
git commit -m "feat: add terrain tool config with 13 NASA Artemis candidate sites"
```

---

### Task 5: Terrain Generation Tool — Core Implementation

**Files:**
- Create: `src/lunar_simulation/scripts/generate_lunar_sdf/generate_lunar_sdf.py`

The script has two modes: `--synthetic` (procedural terrain, works offline) and real data (downloads from NASA). Both produce identical output structure.

- [ ] **Step 1: Create generate_lunar_sdf.py**

```python
#!/usr/bin/env python3
"""
generate_lunar_sdf — Convert NASA LOLA/LROC data to Gazebo SDF terrain models.

Usage:
    # Generate from a preset site (synthetic mode for offline testing):
    python generate_lunar_sdf.py --site shackleton_crater --synthetic

    # Generate from a preset site (real NASA data):
    python generate_lunar_sdf.py --site shackleton_crater

    # Generate all enabled sites:
    python generate_lunar_sdf.py --all --synthetic

    # Custom coordinates:
    python generate_lunar_sdf.py --lat -89.7 --lon 0.0 --size 5000 --name my_site --synthetic
"""

import argparse
import os
import sys
from pathlib import Path
from string import Template

import numpy as np
import yaml
from PIL import Image
from scipy.ndimage import sobel

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SITES_YAML = SCRIPT_DIR / "sites.yaml"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent.parent / "models"

# ---------------------------------------------------------------------------
# Site configuration
# ---------------------------------------------------------------------------

def load_sites(sites_yaml: Path = DEFAULT_SITES_YAML) -> dict:
    """Load site definitions from sites.yaml."""
    with open(sites_yaml, "r") as f:
        config = yaml.safe_load(f)
    defaults = config.get("defaults", {})
    sites = config.get("sites", {})
    for site_id, site in sites.items():
        for key, value in defaults.items():
            site.setdefault(key, value)
    return sites


def get_site(sites: dict, site_id: str) -> dict:
    """Look up a site by ID; raise if not found."""
    if site_id not in sites:
        available = ", ".join(sites.keys())
        raise ValueError(f"Unknown site '{site_id}'. Available: {available}")
    return sites[site_id]

# ---------------------------------------------------------------------------
# Synthetic terrain generation (offline mode)
# ---------------------------------------------------------------------------

def generate_synthetic_heightmap(size: int = 513, seed: int = 42) -> np.ndarray:
    """
    Procedurally generate a lunar-like heightmap.

    Returns a float64 array in [0, 1] range, shape (size, size).
    Features: base undulation, impact craters with rims, fine noise.
    """
    rng = np.random.default_rng(seed)
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)

    # Base undulating terrain (large-scale topography)
    terrain = (
        0.15 * np.sin(1.5 * np.pi * xx + 0.3) * np.cos(2.0 * np.pi * yy + 0.7)
        + 0.08 * np.sin(4.0 * np.pi * xx) * np.sin(3.0 * np.pi * yy)
    )

    # Impact craters: Gaussian depression + raised rim
    num_craters = rng.integers(4, 9)
    for _ in range(num_craters):
        cx, cy = rng.uniform(-0.8, 0.8, 2)
        radius = rng.uniform(0.04, 0.22)
        depth = rng.uniform(0.08, 0.35)
        dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
        r_sq = radius ** 2
        # Bowl
        terrain -= depth * np.exp(-dist_sq / (2 * r_sq))
        # Rim
        terrain += depth * 0.3 * np.exp(
            -(np.sqrt(dist_sq) - radius) ** 2 / (2 * (radius * 0.25) ** 2)
        )

    # Fine-scale noise (regolith roughness)
    terrain += 0.03 * rng.standard_normal((size, size))

    # Normalize to [0, 1]
    terrain -= terrain.min()
    if terrain.max() > 0:
        terrain /= terrain.max()

    return terrain


def generate_synthetic_albedo(size: int = 513, seed: int = 42) -> np.ndarray:
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

# ---------------------------------------------------------------------------
# Real data processing (requires rasterio + network)
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path) -> Path:
    """Download a file if not already cached."""
    if dest.exists():
        print(f"  Using cached: {dest}")
        return dest
    import requests
    print(f"  Downloading: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  Saved to: {dest}")
    return dest


def process_real_elevation(
    geotiff_path: Path, lat: float, lon: float, size_m: int, resolution: int
) -> tuple[np.ndarray, float, float]:
    """
    Crop and resample LOLA elevation data to a heightmap.

    Returns (heightmap_float64_01, elevation_min_m, elevation_max_m).
    """
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.enums import Resampling

    # Approximate degrees per meter at the given latitude
    deg_per_m_lat = 1.0 / 30_000.0  # ~30 km per degree on the Moon
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

    # Normalize to [0, 1]
    if elev_max > elev_min:
        heightmap = (data - elev_min) / (elev_max - elev_min)
    else:
        heightmap = np.zeros_like(data, dtype=np.float64)

    return heightmap, elev_min, elev_max


def process_real_albedo(
    geotiff_path: Path, lat: float, lon: float, size_m: int, resolution: int
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
        albedo = np.stack([grey, grey, grey], axis=-1)
    else:
        albedo = np.moveaxis(bands[:3], 0, -1).astype(np.uint8)

    return albedo

# ---------------------------------------------------------------------------
# Normal map generation
# ---------------------------------------------------------------------------

def compute_normal_map(heightmap: np.ndarray, strength: float = 2.0) -> np.ndarray:
    """
    Derive an RGB normal map from a heightmap using Sobel gradients.

    Parameters:
        heightmap: float64 array in [0, 1], shape (H, W)
        strength: exaggeration factor for surface detail

    Returns:
        uint8 RGB array of shape (H, W, 3) encoding surface normals.
        Convention: R=X, G=Y, B=Z mapped from [-1,1] to [0,255].
    """
    # Compute gradients (rate of height change in x and y directions)
    dx = sobel(heightmap, axis=1) * strength
    dy = sobel(heightmap, axis=0) * strength

    # Construct normal vectors: N = normalize(-dx, -dy, 1)
    normals = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
    norms = np.linalg.norm(normals, axis=-1, keepdims=True)
    normals /= np.where(norms > 0, norms, 1.0)

    # Map from [-1, 1] to [0, 255]
    normal_map = ((normals + 1.0) * 0.5 * 255.0).clip(0, 255).astype(np.uint8)
    return normal_map

# ---------------------------------------------------------------------------
# SDF / model file generation
# ---------------------------------------------------------------------------

MODEL_SDF_TEMPLATE = Template("""\
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

MODEL_CONFIG_TEMPLATE = Template("""\
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


def write_model_files(
    output_dir: Path,
    site_id: str,
    display_name: str,
    description: str,
    heightmap: np.ndarray,
    albedo: np.ndarray,
    normal_map: np.ndarray,
    size_m: int,
    elevation_min: float,
    elevation_max: float,
):
    """Write all model files (SDF, config, textures, metadata) to output_dir."""
    textures_dir = output_dir / "materials" / "textures"
    textures_dir.mkdir(parents=True, exist_ok=True)

    # Save heightmap as 16-bit grayscale PNG
    hm_16bit = (heightmap * 65535).clip(0, 65535).astype(np.uint16)
    Image.fromarray(hm_16bit, mode="I;16").save(textures_dir / "heightmap.png")

    # Save albedo as RGB PNG
    Image.fromarray(albedo, mode="RGB").save(textures_dir / "albedo.png")

    # Save normal map as RGB PNG
    Image.fromarray(normal_map, mode="RGB").save(textures_dir / "normal.png")

    # Compute elevation range for SDF <size> z component
    elevation_range = max(elevation_max - elevation_min, 1.0)

    # model.sdf
    sdf_content = MODEL_SDF_TEMPLATE.substitute(
        site_id=site_id,
        size_x=size_m,
        size_y=size_m,
        size_z=f"{elevation_range:.1f}",
        z_offset=f"{elevation_min:.1f}",
    )
    (output_dir / "model.sdf").write_text(sdf_content)

    # model.config
    config_content = MODEL_CONFIG_TEMPLATE.substitute(
        display_name=display_name,
        description=description,
    )
    (output_dir / "model.config").write_text(config_content)

    # metadata.yaml
    metadata = {
        "site_id": site_id,
        "display_name": display_name,
        "description": description,
        "coordinates": {"lat": float(elevation_min), "lon": 0.0},
        "size_m": size_m,
        "resolution": int(heightmap.shape[0]),
        "elevation_min_m": round(elevation_min, 2),
        "elevation_max_m": round(elevation_max, 2),
        "elevation_range_m": round(elevation_range, 2),
        "source": "synthetic",
    }
    with open(output_dir / "metadata.yaml", "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    print(f"  Model written to: {output_dir}")

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def generate_site(
    site_id: str,
    site_config: dict,
    output_dir: Path,
    synthetic: bool = False,
    cache_dir: Path | None = None,
):
    """Generate a complete Gazebo terrain model for one site."""
    lat = site_config["lat"]
    lon = site_config["lon"]
    size_m = site_config["size_m"]
    resolution = site_config.get("resolution", 513)
    seed = site_config.get("seed", 42)

    print(f"\n=== Generating: {site_config['name']} ({site_id}) ===")
    print(f"    Lat: {lat}, Lon: {lon}, Size: {size_m}m, Resolution: {resolution}px")

    if synthetic:
        print("  Mode: synthetic (procedural terrain)")
        heightmap = generate_synthetic_heightmap(resolution, seed)
        albedo = generate_synthetic_albedo(resolution, seed)
        elevation_min = 0.0
        elevation_max = 500.0  # Approximate lunar terrain range in meters
    else:
        print("  Mode: real data (NASA LOLA + LROC WAC)")
        if cache_dir is None:
            cache_dir = SCRIPT_DIR.parents[3] / "data"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Download LOLA elevation
        lola_url = site_config.get("lola_url", "")
        lola_file = download_file(lola_url, cache_dir / "lola_dem.tif")
        heightmap, elevation_min, elevation_max = process_real_elevation(
            lola_file, lat, lon, size_m, resolution
        )

        # Download LROC WAC albedo
        lroc_url = site_config.get("lroc_wac_url", "")
        lroc_file = download_file(lroc_url, cache_dir / "lroc_wac.tif")
        albedo = process_real_albedo(lroc_file, lat, lon, size_m, resolution)

    # Generate normal map from heightmap
    normal_map = compute_normal_map(heightmap)

    # Write model files
    site_output = output_dir / site_id
    write_model_files(
        output_dir=site_output,
        site_id=site_id,
        display_name=site_config["name"],
        description=site_config.get("description", ""),
        heightmap=heightmap,
        albedo=albedo,
        normal_map=normal_map,
        size_m=size_m,
        elevation_min=elevation_min,
        elevation_max=elevation_max,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate Gazebo SDF terrain models from NASA lunar data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--site", help="Site ID from sites.yaml")
    group.add_argument("--all", action="store_true", help="Generate all enabled sites")
    group.add_argument("--lat", type=float, help="Custom latitude (use with --lon, --size, --name)")

    parser.add_argument("--lon", type=float, help="Custom longitude")
    parser.add_argument("--size", type=int, default=5000, help="Tile side length in meters (default: 5000)")
    parser.add_argument("--name", help="Custom site ID/name")
    parser.add_argument("--synthetic", action="store_true", help="Use procedural terrain instead of NASA data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic mode")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--sites-yaml", type=Path, default=DEFAULT_SITES_YAML, help="Path to sites.yaml")
    parser.add_argument("--cache-dir", type=Path, default=None, help="Cache directory for downloaded data")

    args = parser.parse_args()
    sites = load_sites(args.sites_yaml)

    if args.all:
        for site_id, site_config in sites.items():
            if site_config.get("enabled", False):
                generate_site(site_id, site_config, args.output, args.synthetic, args.cache_dir)
    elif args.site:
        site_config = get_site(sites, args.site)
        generate_site(args.site, site_config, args.output, args.synthetic, args.cache_dir)
    elif args.lat is not None:
        if args.lon is None or args.name is None:
            parser.error("--lat requires --lon and --name")
        site_config = {
            "name": args.name,
            "lat": args.lat,
            "lon": args.lon,
            "size_m": args.size,
            "resolution": 513,
            "seed": args.seed,
            "description": f"Custom site at ({args.lat}, {args.lon})",
        }
        generate_site(args.name, site_config, args.output, args.synthetic, args.cache_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make script executable**

```bash
chmod +x src/lunar_simulation/scripts/generate_lunar_sdf/generate_lunar_sdf.py
```

- [ ] **Step 3: Commit**

```bash
git add src/lunar_simulation/scripts/generate_lunar_sdf/generate_lunar_sdf.py
git commit -m "feat: implement generate_lunar_sdf terrain generation tool"
```

---

### Task 6: Terrain Generation Tool — Tests

**Files:**
- Create: `src/lunar_simulation/scripts/generate_lunar_sdf/tests/test_terrain_processing.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for generate_lunar_sdf terrain processing functions."""

import sys
from pathlib import Path
import tempfile

import numpy as np
import pytest
import yaml

# Add parent to path so we can import the script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_lunar_sdf import (
    generate_synthetic_heightmap,
    generate_synthetic_albedo,
    compute_normal_map,
    write_model_files,
    load_sites,
    get_site,
)

# --- Synthetic heightmap tests ---

class TestSyntheticHeightmap:
    def test_shape(self):
        hm = generate_synthetic_heightmap(size=513, seed=42)
        assert hm.shape == (513, 513)

    def test_range_normalized(self):
        hm = generate_synthetic_heightmap(size=257, seed=42)
        assert hm.min() >= 0.0
        assert hm.max() <= 1.0

    def test_dtype_float64(self):
        hm = generate_synthetic_heightmap(size=129, seed=42)
        assert hm.dtype == np.float64

    def test_deterministic_with_same_seed(self):
        hm1 = generate_synthetic_heightmap(size=65, seed=99)
        hm2 = generate_synthetic_heightmap(size=65, seed=99)
        np.testing.assert_array_equal(hm1, hm2)

    def test_different_seeds_produce_different_terrain(self):
        hm1 = generate_synthetic_heightmap(size=65, seed=1)
        hm2 = generate_synthetic_heightmap(size=65, seed=2)
        assert not np.array_equal(hm1, hm2)


# --- Synthetic albedo tests ---

class TestSyntheticAlbedo:
    def test_shape_rgb(self):
        albedo = generate_synthetic_albedo(size=513, seed=42)
        assert albedo.shape == (513, 513, 3)

    def test_dtype_uint8(self):
        albedo = generate_synthetic_albedo(size=129, seed=42)
        assert albedo.dtype == np.uint8

    def test_grey_centered(self):
        albedo = generate_synthetic_albedo(size=513, seed=42)
        mean_val = albedo.mean()
        assert 100 < mean_val < 155, f"Mean albedo {mean_val} not in expected grey range"

    def test_channels_equal(self):
        """Lunar regolith albedo should be greyscale (R == G == B)."""
        albedo = generate_synthetic_albedo(size=129, seed=42)
        np.testing.assert_array_equal(albedo[:, :, 0], albedo[:, :, 1])
        np.testing.assert_array_equal(albedo[:, :, 1], albedo[:, :, 2])


# --- Normal map tests ---

class TestNormalMap:
    def test_shape_rgb(self):
        hm = generate_synthetic_heightmap(size=129, seed=42)
        nm = compute_normal_map(hm)
        assert nm.shape == (129, 129, 3)

    def test_dtype_uint8(self):
        hm = generate_synthetic_heightmap(size=129, seed=42)
        nm = compute_normal_map(hm)
        assert nm.dtype == np.uint8

    def test_flat_surface_points_up(self):
        """A perfectly flat heightmap should produce normals pointing straight up (0, 0, 1) → (128, 128, 255)."""
        flat = np.full((65, 65), 0.5, dtype=np.float64)
        nm = compute_normal_map(flat, strength=1.0)
        # Z channel (blue) should be near 255 (pointing up)
        assert nm[:, :, 2].mean() > 200
        # X and Y channels should be near 128 (neutral)
        assert 120 < nm[:, :, 0].mean() < 136
        assert 120 < nm[:, :, 1].mean() < 136

    def test_strength_affects_output(self):
        hm = generate_synthetic_heightmap(size=65, seed=42)
        nm_weak = compute_normal_map(hm, strength=0.5)
        nm_strong = compute_normal_map(hm, strength=5.0)
        # Stronger normals → more variation in X/Y channels
        assert nm_strong[:, :, 0].std() > nm_weak[:, :, 0].std()


# --- Model file writing tests ---

class TestWriteModelFiles:
    def test_writes_all_files(self):
        hm = generate_synthetic_heightmap(size=65, seed=42)
        albedo = generate_synthetic_albedo(size=65, seed=42)
        nm = compute_normal_map(hm)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "test_site"
            write_model_files(
                output_dir=out,
                site_id="test_site",
                display_name="Test Site",
                description="A test site",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=5000,
                elevation_min=0.0,
                elevation_max=500.0,
            )

            assert (out / "model.sdf").exists()
            assert (out / "model.config").exists()
            assert (out / "metadata.yaml").exists()
            assert (out / "materials" / "textures" / "heightmap.png").exists()
            assert (out / "materials" / "textures" / "albedo.png").exists()
            assert (out / "materials" / "textures" / "normal.png").exists()

    def test_sdf_contains_site_id(self):
        hm = generate_synthetic_heightmap(size=65, seed=42)
        albedo = generate_synthetic_albedo(size=65, seed=42)
        nm = compute_normal_map(hm)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "my_site"
            write_model_files(
                output_dir=out,
                site_id="my_site",
                display_name="My Site",
                description="Desc",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=3000,
                elevation_min=-100.0,
                elevation_max=200.0,
            )

            sdf = (out / "model.sdf").read_text()
            assert 'name="my_site"' in sdf
            assert "3000" in sdf

    def test_metadata_yaml_valid(self):
        hm = generate_synthetic_heightmap(size=65, seed=42)
        albedo = generate_synthetic_albedo(size=65, seed=42)
        nm = compute_normal_map(hm)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "meta_test"
            write_model_files(
                output_dir=out,
                site_id="meta_test",
                display_name="Meta Test",
                description="Testing metadata",
                heightmap=hm,
                albedo=albedo,
                normal_map=nm,
                size_m=5000,
                elevation_min=0.0,
                elevation_max=500.0,
            )

            with open(out / "metadata.yaml") as f:
                meta = yaml.safe_load(f)
            assert meta["site_id"] == "meta_test"
            assert meta["size_m"] == 5000
            assert meta["elevation_range_m"] == 500.0


# --- Site config tests ---

class TestSiteConfig:
    def test_load_sites(self):
        sites = load_sites()
        assert "shackleton_crater" in sites
        assert sites["shackleton_crater"]["lat"] == -89.7

    def test_get_site_raises_on_unknown(self):
        sites = load_sites()
        with pytest.raises(ValueError, match="Unknown site"):
            get_site(sites, "nonexistent_site")

    def test_defaults_applied(self):
        sites = load_sites()
        # All sites should have size_m from defaults or explicit
        for site_id, site in sites.items():
            assert "size_m" in site, f"{site_id} missing size_m"
            assert "resolution" in site, f"{site_id} missing resolution"
```

- [ ] **Step 2: Run tests**

```bash
cd src/lunar_simulation/scripts/generate_lunar_sdf
pip install -r requirements.txt
python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/lunar_simulation/scripts/generate_lunar_sdf/tests/
git commit -m "test: add unit tests for terrain generation tool"
```

---

### Task 7: Generate 5 Preset Terrain Models

- [ ] **Step 1: Run the generation tool for all enabled sites**

```bash
cd src/lunar_simulation/scripts/generate_lunar_sdf
python generate_lunar_sdf.py --all --synthetic
```

Expected output: 5 model directories created under `src/lunar_simulation/models/`.

- [ ] **Step 2: Verify output structure**

```bash
find ../../models -type f | sort
```

Expected: Each of the 5 sites has `model.sdf`, `model.config`, `metadata.yaml`, and 3 PNG textures.

- [ ] **Step 3: Commit**

```bash
cd /path/to/repo
git add src/lunar_simulation/models/
git commit -m "feat: add 5 pre-built lunar terrain models (synthetic)"
```

---

### Task 8: Gazebo World File and GUI Config

**Files:**
- Create: `src/lunar_simulation/worlds/lunar_surface.world`
- Create: `src/lunar_simulation/config/gui.config`

- [ ] **Step 1: Create lunar_surface.world**

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="lunar_surface">

    <!-- Lunar gravity: 1.625 m/s² (≈ 1/6 Earth) -->
    <gravity>0 0 -1.625</gravity>

    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>

    <!-- Black sky, no atmosphere -->
    <scene>
      <ambient>0.05 0.05 0.05 1.0</ambient>
      <background>0 0 0 1.0</background>
      <shadows>true</shadows>
    </scene>

    <!-- Sun: directional light approximating low-angle polar illumination -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>1.0 1.0 0.98 1.0</diffuse>
      <specular>0.5 0.5 0.48 1.0</specular>
      <attenuation>
        <range>10000</range>
        <constant>0.9</constant>
        <linear>0.0</linear>
        <quadratic>0.0</quadratic>
      </attenuation>
      <!-- Low elevation angle typical for south pole -->
      <direction>0.5 0.2 -0.3</direction>
    </light>

    <!-- Required Gazebo Harmonic system plugins -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics">
      <engine>
        <filename>gz-physics-dartsim-plugin</filename>
      </engine>
    </plugin>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>

  </world>
</sdf>
```

- [ ] **Step 2: Create gui.config**

```xml
<?xml version="1.0"?>

<!-- Gazebo GUI configuration for world_builder mode -->

<plugin filename="GzScene3D" name="3D View">
  <gz-gui>
    <title>3D View</title>
    <property type="bool" key="showTitleBar">false</property>
    <property type="string" key="state">docked</property>
  </gz-gui>
  <engine>ogre2</engine>
  <scene>scene</scene>
  <ambient_light>0.05 0.05 0.05</ambient_light>
  <background_color>0 0 0</background_color>
  <camera_pose>0 -50 30 0 0.5 1.57</camera_pose>
</plugin>

<plugin filename="WorldControl" name="World control">
  <gz-gui>
    <title>World control</title>
    <property type="bool" key="showTitleBar">false</property>
    <property type="string" key="state">floating</property>
    <property type="double" key="x">0</property>
    <property type="double" key="y">0</property>
    <property type="double" key="width">250</property>
    <property type="double" key="height">50</property>
  </gz-gui>
  <play_pause>true</play_pause>
  <step>true</step>
</plugin>

<plugin filename="WorldStats" name="World stats">
  <gz-gui>
    <title>World stats</title>
    <property type="bool" key="showTitleBar">false</property>
    <property type="string" key="state">floating</property>
    <property type="double" key="x">250</property>
    <property type="double" key="y">0</property>
    <property type="double" key="width">250</property>
    <property type="double" key="height">50</property>
  </gz-gui>
</plugin>

<plugin filename="ResourceSpawner" name="Resource spawner">
  <gz-gui>
    <title>Terrain Models</title>
    <property type="bool" key="showTitleBar">true</property>
    <property type="string" key="state">docked</property>
  </gz-gui>
</plugin>

<plugin filename="EntityTree" name="Entity tree">
  <gz-gui>
    <title>Entity Tree</title>
    <property type="bool" key="showTitleBar">true</property>
    <property type="string" key="state">docked</property>
  </gz-gui>
</plugin>
```

- [ ] **Step 3: Commit**

```bash
git add src/lunar_simulation/worlds/ src/lunar_simulation/config/
git commit -m "feat: add lunar surface world file and GUI config"
```

---

### Task 9: Launch Files

**Files:**
- Create: `src/lunar_simulation/launch/lunar_surface.launch.py`
- Create: `src/lunar_simulation/launch/world_builder.launch.py`

- [ ] **Step 1: Create lunar_surface.launch.py**

Quick-start mode: launches Gazebo with a specific terrain model pre-loaded.

```python
"""
Launch Gazebo with a pre-loaded lunar terrain model.

Usage:
    ros2 launch lunar_simulation lunar_surface.launch.py
    ros2 launch lunar_simulation lunar_surface.launch.py site:=nobile_rim_1
"""

import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.actions import ExecuteProcess


def launch_setup(context, *args, **kwargs):
    site = LaunchConfiguration("site").perform(context)
    pkg_share = FindPackageShare("lunar_simulation").perform(context)
    world_file = os.path.join(pkg_share, "worlds", "lunar_surface.world")
    model_path = os.path.join(pkg_share, "models")

    # Verify the requested site model exists
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

    # Read the base world file and inject the terrain model
    with open(world_file, "r") as f:
        world_content = f.read()

    include_sdf = (
        f'    <include>\n'
        f'      <uri>model://{site}</uri>\n'
        f'      <pose>0 0 0 0 0 0</pose>\n'
        f'    </include>\n'
    )
    modified_world = world_content.replace("</world>", include_sdf + "  </world>")

    # Write modified world to a temp file
    tmp = tempfile.NamedTemporaryFile(
        suffix=".world", mode="w", delete=False, prefix=f"lunar_{site}_"
    )
    tmp.write(modified_world)
    tmp.close()

    gz_env = {"GZ_SIM_RESOURCE_PATH": model_path}

    gz_sim = ExecuteProcess(
        cmd=["gz", "sim", "-r", tmp.name],
        additional_env=gz_env,
        output="screen",
    )

    return [
        LogInfo(msg=f"Loading lunar terrain: {site}"),
        gz_sim,
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "site",
                default_value="shackleton_crater",
                description="Lunar site to load (e.g., shackleton_crater, nobile_rim_1)",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
```

- [ ] **Step 2: Create world_builder.launch.py**

Sandbox mode: empty world with Resource Spawner for drag-and-drop terrain placement.

```python
"""
Launch Gazebo in world-builder sandbox mode with the Resource Spawner GUI.

Users can browse and place terrain models interactively.

Usage:
    ros2 launch lunar_simulation world_builder.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("lunar_simulation")

    world_file = [pkg_share, "/worlds/lunar_surface.world"]
    gui_config = [pkg_share, "/config/gui.config"]
    model_path = [pkg_share, "/models"]

    gz_sim = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r",
            world_file,
            "--gui-config", gui_config,
        ],
        additional_env={"GZ_SIM_RESOURCE_PATH": model_path},
        output="screen",
    )

    return LaunchDescription(
        [
            LogInfo(msg="Launching Gazebo in world-builder mode with Resource Spawner"),
            gz_sim,
        ]
    )
```

- [ ] **Step 3: Commit**

```bash
git add src/lunar_simulation/launch/
git commit -m "feat: add launch files for quick-start and world-builder modes"
```

---

### Task 10: Project Documentation

**Files:**
- Create: `README.md`
- Create: `READING_LIST.md`
- Create: `src/lunar_simulation/scripts/generate_lunar_sdf/README.md`

- [ ] **Step 1: Create project README.md**

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
  ros2 launch lunar_simulation lunar_surface.launch.py site:=shackleton_crater"

# Or launch in world-builder sandbox mode
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch lunar_simulation world_builder.launch.py"
```

### NVIDIA GPU

```bash
docker compose run sim-nvidia bash -c "source /ws/install/setup.bash && \
  ros2 launch lunar_simulation lunar_surface.launch.py"
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
ros2 launch lunar_simulation lunar_surface.launch.py site:=nobile_rim_1
```

### World Builder
Open an empty lunar world with the Resource Spawner panel to place terrain interactively:
```bash
ros2 launch lunar_simulation world_builder.launch.py
```

## Project Structure

```
src/lunar_simulation/     # ROS 2 package
  models/                 # Pre-built SDF terrain models
  worlds/                 # Gazebo world files
  launch/                 # ROS 2 launch files
  config/                 # Gazebo GUI configs
  scripts/                # Developer tools (terrain generator)
docker/                   # Dockerfile + Compose
```

## Adding New Terrain Sites

See [scripts/generate_lunar_sdf/README.md](src/lunar_simulation/scripts/generate_lunar_sdf/README.md)
for the developer terrain generation tool.

## License

Apache 2.0 — see [LICENSE](LICENSE).
```

- [ ] **Step 2: Create terrain tool README**

`src/lunar_simulation/scripts/generate_lunar_sdf/README.md`:

```markdown
# generate_lunar_sdf — Terrain Generation Tool

Developer tool for creating Gazebo SDF terrain models from NASA satellite data
or procedural generation.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Generate all enabled preset sites (synthetic/offline)

```bash
python generate_lunar_sdf.py --all --synthetic
```

### Generate a specific preset site (real NASA data)

```bash
python generate_lunar_sdf.py --site shackleton_crater
```

### Generate from custom coordinates

```bash
python generate_lunar_sdf.py --lat -89.7 --lon 0.0 --size 5000 --name my_site --synthetic
```

## Output Structure

Each site generates a complete Gazebo model directory:

```
models/<site_id>/
├── model.sdf                   # SDF with heightmap geometry + material
├── model.config                # Gazebo model metadata
├── metadata.yaml               # Source coordinates, elevation range
└── materials/textures/
    ├── heightmap.png            # 16-bit grayscale (513×513)
    ├── albedo.png               # RGB diffuse texture (513×513)
    └── normal.png               # RGB normal map (513×513)
```

## How It Works

1. **Heightmap**: NASA LOLA elevation data (or synthetic noise) → normalized to
   16-bit grayscale PNG. Gazebo reads this at runtime and creates 3D geometry
   where pixel brightness = height.

2. **Albedo**: NASA LROC WAC reflectance data (or synthetic grey) → RGB PNG
   used as the diffuse color texture on the terrain surface.

3. **Normal map**: Computed from the heightmap using a Sobel filter. Adds
   perceived surface detail (bumps, ridges) without extra geometry.

4. **SDF model**: References the three PNGs and defines the terrain size,
   collision geometry, and visual material.

## Data Sources

- **LOLA (Lunar Orbiter Laser Altimeter)**: Elevation data at ~60m/px
  - PDS: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/
  - USGS: https://astrogeology.usgs.gov/search?pmi-target=moon

- **LROC WAC (Wide Angle Camera)**: Albedo/reflectance at ~100m/px
  - ASU: https://wms.lroc.asu.edu/lroc/
  - USGS: https://astrogeology.usgs.gov/search?pmi-target=moon

## Running Tests

```bash
python -m pytest tests/ -v
```

## Adding a New Site

1. Add the site definition to `sites.yaml`
2. Run: `python generate_lunar_sdf.py --site <site_id> [--synthetic]`
3. Verify the model loads: `gz sim -r models/<site_id>/model.sdf`
4. Commit the generated model directory
```

- [ ] **Step 3: Create READING_LIST.md** (see Task 11)

- [ ] **Step 4: Commit**

```bash
git add README.md src/lunar_simulation/scripts/generate_lunar_sdf/README.md
git commit -m "docs: add project README and terrain tool documentation"
```

---

### Task 11: Reading List — Theory and Background

**Files:**
- Create: `READING_LIST.md`

This covers everything you need to understand **why** each technology and technique is used in this project.

- [ ] **Step 1: Create READING_LIST.md**

```markdown
# Reading List — Theory & Background

Everything you need to understand the technologies and techniques used in the
Artemis Mission Simulator. Organized from foundational concepts to
project-specific details.

---

## 1. Heightmaps (Displacement Maps)

A heightmap is a 2D image where each pixel's brightness represents elevation.
This is how we turn satellite elevation data into 3D terrain without creating
heavy 3D mesh files.

- **What is a heightmap:**
  https://en.wikipedia.org/wiki/Heightmap

- **How game engines use heightmaps for terrain:**
  https://docs.unity3d.com/Manual/terrain-Heightmaps.html
  (Unity docs, but the concept is universal — Gazebo uses the same approach)

- **Why power-of-2+1 resolution (257, 513, 1025)?**
  Terrain engines subdivide the heightmap into a grid of quads. A 513×513
  image creates 512×512 quads. The +1 is because you need one more vertex
  than the number of quads in each direction (fence-post problem).

- **16-bit vs 8-bit heightmaps:**
  8-bit gives 256 height levels (staircase artifacts). 16-bit gives 65,536
  levels — smooth enough for realistic terrain. Gazebo Harmonic supports both.

---

## 2. Texture Mapping

How 2D images are painted onto 3D surfaces.

- **Diffuse / Albedo map:**
  The base color texture. For lunar terrain, this comes from LROC WAC
  reflectance data — it captures the actual surface color/brightness.
  https://en.wikipedia.org/wiki/Texture_mapping

- **Normal map:**
  A special RGB texture that encodes surface orientation per pixel. It makes
  flat geometry look bumpy by changing how light reflects. Each pixel stores
  a 3D normal vector: R=X, G=Y, B=Z, mapped from [-1,1] to [0,255].
  https://en.wikipedia.org/wiki/Normal_mapping

- **Learn OpenGL — Normal Mapping (excellent visual tutorial):**
  https://learnopengl.com/Advanced-Lighting/Normal-Mapping

- **PBR (Physically Based Rendering) basics:**
  Modern rendering uses PBR materials (albedo + normal + roughness + metallic).
  For lunar regolith we only need albedo + normal. Roughness is uniformly high
  (regolith is matte), metallic is 0.
  https://learnopengl.com/PBR/Theory

---

## 3. Sobel Filter — Normal Map Generation

We derive the normal map from the heightmap using the Sobel operator (an image
processing technique). No additional data download needed.

- **Sobel operator — how it works:**
  A 3×3 convolution kernel that computes the gradient (rate of change) of image
  intensity in the X and Y directions. Applied to a heightmap, it tells you the
  slope at each pixel.
  https://en.wikipedia.org/wiki/Sobel_operator

- **From heightmap to normal map (algorithm):**
  1. Apply Sobel in X direction → gradient_x (how fast height changes left-right)
  2. Apply Sobel in Y direction → gradient_y (how fast height changes up-down)
  3. Construct normal vector: N = normalize(-gradient_x, -gradient_y, 1.0)
  4. Map from [-1,1] range to [0,255] range for storage as an image

- **Image convolution (prerequisite to understanding Sobel):**
  https://en.wikipedia.org/wiki/Kernel_(image_processing)

- **scipy.ndimage.sobel documentation:**
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.sobel.html

---

## 4. NASA LOLA — Lunar Elevation Data

The **Lunar Orbiter Laser Altimeter (LOLA)** flew on the Lunar Reconnaissance
Orbiter (LRO). It fires laser pulses at the Moon's surface and measures the
return time to calculate elevation. This is where our heightmap data comes from.

- **LOLA instrument overview:**
  https://lunar.gsfc.nasa.gov/lola.html

- **How laser altimetry works:**
  https://en.wikipedia.org/wiki/Lidar#Spaceborne

- **LOLA data products (LDEM = Lunar Digital Elevation Model):**
  https://pds-geosciences.wustl.edu/missions/lro/lola.htm
  - LDEM products give gridded elevation in meters, available at various
    resolutions (20m, 60m, 118m per pixel)
  - South pole specific product: LDEM_80S — covers 80°S to pole

- **USGS Astropedia lunar maps (browse LOLA products):**
  https://astrogeology.usgs.gov/search?pmi-target=moon

---

## 5. NASA LROC WAC — Lunar Surface Imagery

The **Lunar Reconnaissance Orbiter Camera (LROC)** has two components:
- **NAC (Narrow Angle Camera):** Very high resolution (0.5 m/px) but small coverage
- **WAC (Wide Angle Camera):** Lower resolution (~100 m/px) but global coverage

We use WAC global mosaics for our albedo textures because they cover the entire
Moon uniformly.

- **LROC instrument overview:**
  https://www.lroc.asu.edu/about

- **WAC global mosaic products:**
  https://wms.lroc.asu.edu/lroc/view_rdr_product/WAC_GLOBAL

- **Difference between WAC and NAC:**
  https://www.lroc.asu.edu/about/specs
  NAC is for close-up detail, WAC is for regional/global context.

- **LROC data browsing (QuickMap):**
  https://quickmap.lroc.asu.edu/
  Interactive lunar map — zoom to any Artemis candidate site and see what
  NAC/WAC data looks like.

---

## 6. GeoTIFF and Geospatial Rasters

Satellite data is stored as **GeoTIFF** files — regular images (TIFF format)
with embedded geographic metadata (coordinate system, projection, extent).

- **What is GeoTIFF:**
  https://en.wikipedia.org/wiki/GeoTIFF

- **Coordinate Reference Systems (CRS):**
  Every geospatial dataset uses a CRS to map pixel coordinates to real-world
  positions. Lunar data uses selenographic coordinates (latitude/longitude on
  the Moon) or polar stereographic projections.
  https://en.wikipedia.org/wiki/Spatial_reference_system

- **Selenographic coordinates:**
  Latitude and longitude on the Moon. Similar to Earth, but centred on the
  Moon's equator and prime meridian.
  https://en.wikipedia.org/wiki/Selenographic_coordinates

- **Rasterio (Python library for reading GeoTIFFs):**
  https://rasterio.readthedocs.io/en/stable/quickstart.html

- **GDAL (the underlying engine rasterio uses):**
  https://gdal.org/en/stable/
  Handles format conversion, reprojection, resampling of geospatial rasters.

---

## 7. Gazebo SDF Format

**SDF (Simulation Description Format)** is the XML format Gazebo uses to
describe worlds, models, physics, and sensors.

- **SDF specification:**
  http://sdformat.org/spec

- **Heightmap element in SDF:**
  http://sdformat.org/spec?ver=1.9&elem=geometry#geometry_heightmap
  This is the specific SDF element we use — it tells Gazebo to create terrain
  geometry from a PNG heightmap at runtime.

- **Model structure (model.sdf + model.config):**
  https://gazebosim.org/api/sim/8/resources.html
  Every Gazebo model needs model.sdf (the geometry/physics) and model.config
  (metadata like name, author, description). The Resource Spawner reads
  model.config to display models in the GUI.

---

## 8. Gazebo Harmonic

Gazebo Harmonic is the LTS release of the Gazebo simulator (formerly Ignition
Gazebo). It uses OGRE2 for rendering and DART for physics.

- **Gazebo Harmonic overview:**
  https://gazebosim.org/docs/harmonic/getstarted/

- **Gazebo system plugins (Physics, Sensors, SceneBroadcaster, etc.):**
  https://gazebosim.org/api/sim/8/createsystemplugins.html
  Our world file loads these plugins to enable physics simulation, rendering,
  and user interaction.

- **Resource Spawner plugin:**
  https://gazebosim.org/api/sim/8/resources.html
  Discovers models from `GZ_SIM_RESOURCE_PATH` and lets users drag-and-drop
  them into the scene. This is what powers our world-builder mode.

- **Gazebo GUI configuration (gui.config):**
  https://gazebosim.org/api/gui/8/config.html
  XML file that defines which GUI plugins to load and their layout.

---

## 9. ROS 2 Jazzy + Gazebo Integration

- **ROS 2 Jazzy overview:**
  https://docs.ros.org/en/jazzy/

- **ros_gz (ROS-Gazebo integration packages):**
  https://github.com/gazebosim/ros_gz
  Provides `ros_gz_sim` (launch utilities), `ros_gz_bridge` (topic bridging),
  and `ros_gz_image` (camera bridging).

- **ROS 2 Launch system:**
  https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html
  Python-based launch files that start nodes, set parameters, and compose
  complex launch configurations.

- **ament_cmake build system:**
  https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Documentation.html
  The build system for ROS 2 C++ and mixed packages. Our package uses it to
  install resource files (models, worlds, configs, launch files).

---

## 10. Artemis Programme — Mission Context

Understanding the mission helps you understand why we chose specific sites
and terrain parameters.

- **NASA Artemis programme overview:**
  https://www.nasa.gov/artemis/

- **Artemis III candidate landing regions (13 sites near South Pole):**
  https://www.nasa.gov/press-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-moon
  All sites are within ~6° of the South Pole — chosen for near-permanent
  sunlight on crater rims (power) and permanently shadowed craters nearby
  (water ice).

- **Why the South Pole?**
  https://science.nasa.gov/lunar-science/nasas-lunar-exploration/artemis-iii/
  Water ice in shadowed craters, near-continuous sunlight on peaks,
  scientifically interesting geology.

- **Artemis Science Definition Team Report (2020):**
  https://www.nasa.gov/wp-content/uploads/2020/12/artemis-iii-science-definition-report.pdf
  Detailed rationale for site selection and science objectives.

---

## 11. Docker for Robotics Simulation

- **Docker basics:**
  https://docs.docker.com/get-started/

- **Docker Compose:**
  https://docs.docker.com/compose/

- **X11 forwarding in Docker (GUI applications):**
  https://wiki.ros.org/docker/Tutorials/GUI

- **NVIDIA Container Toolkit (GPU passthrough):**
  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
  Required for hardware-accelerated rendering in Gazebo inside Docker.

---

## Suggested Reading Order

For someone new to all of this:

1. Heightmaps (§1) — the core concept everything else builds on
2. Texture mapping + Normal maps (§2)
3. Sobel filter (§3) — how we make normal maps from heightmaps
4. SDF format (§7) — how Gazebo consumes our data
5. Gazebo Harmonic (§8) — the simulation platform
6. LOLA + LROC (§4, §5) — where our data comes from
7. GeoTIFF / rasterio (§6) — how we process the data
8. Artemis programme (§10) — mission context
9. ROS 2 (§9) — the robotics framework
10. Docker (§11) — the deployment mechanism
```

- [ ] **Step 2: Commit**

```bash
git add READING_LIST.md
git commit -m "docs: add comprehensive reading list for project theory and background"
```

---

### Task 12: End-to-End Verification

- [ ] **Step 1: Build Docker image**

```bash
cd docker && docker compose build
```

Expected: Image builds successfully.

- [ ] **Step 2: Verify colcon build inside container**

```bash
docker compose run sim bash -c "source /opt/ros/jazzy/setup.bash && cd /ws && colcon build"
```

Expected: `lunar_simulation` package builds with no errors.

- [ ] **Step 3: Verify terrain models are installed**

```bash
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ls \$AMENT_PREFIX_PATH/share/lunar_simulation/models/"
```

Expected: Lists 5 site directories.

- [ ] **Step 4: Test quick-start launch**

```bash
xhost +local:docker
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch lunar_simulation lunar_surface.launch.py site:=shackleton_crater"
```

Expected: Gazebo opens with Shackleton terrain visible. Verify terrain renders, physics runs.

- [ ] **Step 5: Test world-builder launch**

```bash
docker compose run sim bash -c "source /ws/install/setup.bash && \
  ros2 launch lunar_simulation world_builder.launch.py"
```

Expected: Gazebo opens with Resource Spawner panel showing 5 terrain models.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: final verification pass for initial release"
```

---

## What Is NOT in This Initial Version

- Vehicle models (LTV, rovers)
- Moonfall drone simulation
- Environment plugins (illumination cycles, power systems, dust)
- Mission orchestration / demo scenarios
- Real NASA data in pre-built models (currently synthetic; regenerate with internet)
- CI/CD pipeline
- ros_gz_bridge
- Terrain resolution above 513×513
