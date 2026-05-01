# Artemis Mission Simulator

An open-source Gazebo and ROS 2 based simulation platform aiming to simulate NASA's Artemis programme moon base and scientific operations as close to reality as possible.

![Shackleton Rim terrain in Gazebo](media/hero.gif)
<p align="center"><em>GIF showing the Shackleton Rim terrain in Gazebo which comes pre-generated with this repo. You can generate your own using the lunar_terrain_exporter cli tool of this workspace</em></p>

**Stack:** ROS 2 Jazzy · Gazebo Harmonic · Docker

---

## Setup

### Prerequisites

- Docker
- X11 display server (Linux) or XQuartz (macOS)
- (Optional) NVIDIA GPU + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### Build & Run

```bash
# Build the Docker image
./docker/build.sh

# Start the container (auto-detects NVIDIA GPU, mounts workspace)
./docker/run.sh

# Inside the container
colcon build --symlink-install
source install/setup.bash
```

## Launch

### Lunar Surface (pre-built terrain)

```bash
ros2 launch artemis_mission_launcher lunar_surface.launch.py world:=lunar_empty_world
```

## Packages

| Package | Description |
|---------|-------------|
| [`lunar_terrain_exporter`](lunar_terrain_exporter/) | CLI tool and pipeline for generating Gazebo terrain models from NASA PGDA-78 south-pole DEMs |
| [`artemis_mission_launcher`](artemis_mission_launcher/) | ROS 2 launch files and Gazebo world definitions |

More packages upcoming!

## Contributing

Checkout [Contributing.md](CONTRIBUTING.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
