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
- NVIDIA GPU + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### Build & Run

Two supported workflows — pick whichever fits your tooling. Both use the same `docker/Dockerfile`.

Both workflows build a non-root user named `commander_${USER}` (e.g. `commander_alice`) with your host UID/GID, so files created inside the container are owned by your host user on disk. The container hostname is `artemis` — your shell prompt will look like `commander_alice@artemis:/workspace$`.

#### Option A: Docker scripts (no IDE required)

```bash
# Build the Docker image (uses your host UID/GID and username)
./docker/build.sh

# Start the container (auto-detects NVIDIA GPU, mounts workspace)
./docker/run.sh

# Inside the container
cd /workspace && colcon build --symlink-install
source install/setup.bash
```

#### Option B: VS Code Devcontainer

Requires the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

1. Open the repo in VS Code.
2. Run **Dev Containers: Reopen in Container** from the command palette.
3. VS Code builds the image from `docker/Dockerfile` and drops you into a shell as `commander_${USER}@artemis`.

The repo is mounted at `/workspace/src`, so `colcon build` runs from `/workspace`:

```bash
cd /workspace && colcon build --symlink-install
```

NVIDIA GPU passthrough is opt-in for the devcontainer — uncomment the `--gpus=all` lines in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) if you have `nvidia-container-toolkit` installed.

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
