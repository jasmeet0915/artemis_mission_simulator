<p align="center">
  <img src="media/logo.png" alt="Artemis Mission Simulator" width="600"/>
</p>

<p align="center">
  <a href="https://github.com/jasmeet0915/artemis_mission_simulator/actions/workflows/build_and_test.yml">
    <img src="https://github.com/jasmeet0915/artemis_mission_simulator/actions/workflows/build_and_test.yml/badge.svg" alt="Build & Test"/>
  </a>
  <img src="https://img.shields.io/badge/ROS_2-Jazzy-blue" alt="ROS 2 Jazzy"/>
  <img src="https://img.shields.io/badge/Gazebo-Harmonic-orange" alt="Gazebo Harmonic"/>
  <img src="https://img.shields.io/badge/license-Apache_2.0-green" alt="License"/>
</p>

<p align="center">
  An open-source ROS 2 + Gazebo platform for simulating NASA's Artemis lunar missions —
  terrain, illumination, robotics, and beyond.
</p>

---

<p align="center">
  <img src="media/hero.gif" alt="Launching an Artemis mission with the artemis CLI"/>
  <br/>
  <em>One command — <code>artemis liftoff</code> — boots the mission-control dashboard, Gazebo, and the mission manager in a single tmux session</em>
</p>

---

## Overview

Artemis Mission Simulator is a plug-and-play simulation playground for researchers and engineers working on space robotics for the Artemis programme. The goal is two-fold: simulate the lunar environment as faithfully as possible, and provide a ready-to-use testing ground for rovers, drones, humanoids, and other systems intended for lunar surface operations.

The whole stack is driven by a single command-line tool, **`artemis`**: `artemis liftoff` brings up a live terminal mission-control dashboard, the Gazebo simulation, and the mission manager together, each in its own pane of a dedicated tmux session.

**Milestone 1 — Lunar Environment (in progress)**
- Real terrain from NASA PGDA-78 LRO elevation data for Artemis south-pole landing sites
- Accurate solar illumination and permanently shadowed regions via ephemeris data
- Procedural surface texturing for VO and SLAM testing

**Upcoming milestones**
- Moonfall drone simulation
- Lunar Terrain Vehicles (LTVs) and rovers
- Lunar base environment

## Packages

| Package | Description |
|---------|-------------|
| [`artemis_mission_launcher`](artemis_mission_launcher/) | The `artemis` command-line tool, the terminal mission-control dashboard, and the Gazebo world launch files |
| [`artemis_mission_manager`](artemis_mission_manager/) | Mission-level orchestration; publishes latched site metadata on `/mission/site_metadata` |
| [`artemis_mission_interfaces`](artemis_mission_interfaces/) | ROS 2 message definitions for mission-level information (e.g. `SiteMetadata`) |
| [`artemis_assets`](artemis_assets/) | Pre-built Gazebo terrain models for the supported sites (and future props/robots) |
| [`lunar_terrain_exporter`](lunar_terrain_exporter/) | CLI tool for generating Gazebo SDF terrain models from NASA PGDA-78 south-pole DEMs |

## Setup

### Prerequisites

- Docker
- X11 display server (Linux) or XQuartz (macOS)
- NVIDIA GPU + [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### Option A — Docker scripts

```bash
# Build the image
./docker/build.sh

# Launch the container (auto-detects NVIDIA GPU, mounts workspace)
./docker/run.sh

# Inside the container
colcon build --symlink-install
source install/setup.bash
```

### Option B — VS Code Devcontainer

Requires the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

1. Open the repo in VS Code.
2. Run **Dev Containers: Reopen in Container**.
3. Build from the terminal:

```bash
colcon build --symlink-install
source install/setup.bash
```

> NVIDIA GPU passthrough is opt-in — uncomment the `--gpus=all` lines in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json).

Both flows map your host UID/GID into the container so mounted files are always owned by your host user. Build artifacts persist across restarts in named Docker volumes. To wipe them after an image rebuild:

```bash
docker volume rm artemis-build artemis-install artemis-log
```

## Mission Control — the `artemis` CLI

Once the workspace is built and sourced, a single command launches a full mission:

```bash
artemis liftoff --site shackleton_rim
```

`artemis liftoff` creates a tmux session named `artemis` with one window per stack and **attaches you to it**:

| Window | What it runs |
|--------|--------------|
| `mission-control` | A live terminal dashboard — mission clock, site overview, and host telemetry, over a starfield |
| `simulation` | The Gazebo world for the selected site (`lunar_world.launch.py`) |
| `mission_manager` | Publishes latched site metadata on `/mission/site_metadata` |

**Options**

| Flag | Description |
|------|-------------|
| `--site <name>` | Mission site (default: `empty_lunar`). See sites below. |
| `--epoch <when>` | Mission UTC epoch: `now`, `now+<N>{s,m,h,d}`, `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SSZ` (default: `now`) |
| `-d`, `--detached` | Launch in the background instead of attaching to the tmux session |
| `--no-home` | Skip the mission-control dashboard |

**Available sites:** `empty_lunar`, `shackleton_rim`, `de_gerlache_rim`, `peak_near_shackleton`, `connecting_ridge`

**Shutting down** — from the attached session press `Ctrl-C` to shut the mission down cleanly. If you launched with `--detached`:

```bash
tmux attach -t artemis        # re-attach
tmux kill-session -t artemis  # force-stop
```

### Launching the simulation alone

To bring up only the Gazebo world without the full mission stack:

```bash
ros2 launch artemis_mission_launcher lunar_world.launch.py site:=shackleton_rim
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Logo generated with Google Gemini.</sub>
</p>
