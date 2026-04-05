#!/usr/bin/env bash
# Run the Artemis Mission Simulator container with the workspace volume-mounted.
# Auto-detects NVIDIA GPU and enables hardware acceleration when available.
#
# Usage:
#   ./docker/run.sh          # interactive shell
#
# Inside the container:
#   colcon build --symlink-install              # build workspace
#   source install/setup.bash                   # source workspace
#   ros2 launch artemis_mission_launcher lunar_surface.launch.py site:=connecting_ridge

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="artemis-mission-simulator:latest"
CONTAINER_NAME="artemis-sim"

if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "❌ Image $IMAGE_NAME not found. Run ./docker/build.sh first."
    exit 1
fi

# Detect NVIDIA GPU
GPU_FLAGS=()
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "🖥  NVIDIA GPU detected — using hardware acceleration"
    GPU_FLAGS=(--gpus all -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=all)
else
    echo "🖥  No NVIDIA GPU detected — using software rendering"
fi

# Allow X11 forwarding
xhost +local:docker &>/dev/null || true

echo "🌙 Starting container (workspace mounted at /workspace)"
exec docker run --rm -it \
    --name "$CONTAINER_NAME" \
    --network host \
    -e DISPLAY="${DISPLAY}" \
    -e QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "$REPO_ROOT":/workspace \
    "${GPU_FLAGS[@]}" \
    "$IMAGE_NAME"
