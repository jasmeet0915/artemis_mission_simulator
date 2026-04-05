# Artemis Mission Simulator

An open-source Gazebo-based simulation platform for NASA's Artemis programme.
Launch Gazebo with realistic lunar terrain and start simulating missions immediately.

**Stack:** ROS 2 Jazzy · Gazebo Harmonic · Docker

## Quick Start

### Prerequisites
- Docker
- X11 display server (Linux) or XQuartz (macOS)
- (Optional) NVIDIA GPU + nvidia-container-toolkit

### Build and Run

```bash
# Build the Docker image (deps only — workspace is volume-mounted)
./docker/build.sh

# Start the container (auto-detects NVIDIA GPU, mounts workspace at /ws)
./docker/run.sh

# Inside the container:
colcon build --symlink-install
ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=connecting_ridge
```

## Available Terrain Sites

| Site | Launch ID | Barker ID | Description |
|------|-----------|-----------|-------------|
| Connecting Ridge | `connecting_ridge` | Site 01 | Ridge between Shackleton and de Gerlache |
| Shackleton Rim | `shackleton_rim` | Site 04 | Rim of Shackleton crater |
| Peak Near Shackleton | `peak_near_shackleton` | Site 07 | Isolated peak near Shackleton |
| De Gerlache Rim | `de_gerlache_rim` | Site 11 | Rim of de Gerlache crater |

## Launch Modes

### Quick Start
Load a pre-built terrain and start simulating:
```bash
ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=shackleton_rim
```

### World Builder
Open an empty lunar world with the Resource Spawner panel to place terrain interactively:
```bash
ros2 launch artemis_mission_launcher world_builder.launch.py
```

## Project Structure

```
src/
  generate_lunar_sdf/          # ROS 2 Python package
    generate_lunar_sdf/        # Terrain generation CLI and models
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

The `generate_lunar_sdf` package provides a CLI tool that downloads
NASA LOLA/LROC data and generates Gazebo-ready terrain models:

```bash
# Generate all preset sites
generate_lunar_sdf --config config/artemis_sites.yaml --output-dir ./models

# Generate a single preset site
generate_lunar_sdf --config config/artemis_sites.yaml --site connecting_ridge --output-dir ./models

# Use a pre-cropped DEM tile (full extent, no lat/lon needed)
generate_lunar_sdf --name my_site --dem-url https://example.com/dem.tif \
  --use-full-extent --output-dir ./models
```

See [src/generate_lunar_sdf/README.md](src/generate_lunar_sdf/README.md) for details.

## Data Sources & Citation

Terrain elevation data from:

> Barker, M.K., et al. (2021). Improved LOLA Elevation Maps for South Pole
> Landing Sites: Error Estimates and Their Impact on Illumination Conditions.
> *Planetary and Space Science*, 203, 105119.
> [doi:10.1016/j.pss.2020.105119](https://doi.org/10.1016/j.pss.2020.105119)

DEM tiles: [NASA PGDA Product 78](https://pgda.gsfc.nasa.gov/products/78) — 5 m/pix improved LOLA south-pole DEMs.
Albedo: LROC WAC Global Morphology Mosaic (100 m/pix).

## License

Apache 2.0 — see [LICENSE](LICENSE).