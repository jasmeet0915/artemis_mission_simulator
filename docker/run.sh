#!/usr/bin/env bash
# Run the Artemis Mission Simulator container with the workspace volume-mounted.
# Auto-detects NVIDIA GPU and enables hardware acceleration when available.
#
# Usage:
#   ./docker/run.sh          # interactive shell

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="artemis-mission-simulator:latest"
CONTAINER_NAME="artemis-sim"
USERNAME="commander_${USER}"

if [[ -z "$(docker images -q "$IMAGE_NAME" 2>/dev/null)" ]]; then
    echo "❌ Image $IMAGE_NAME not found. Run ./docker/build.sh first."
    exit 1
fi

# Require an NVIDIA GPU (with nvidia-container-toolkit) — Gazebo + the lunar
# terrain assets are too heavy for software rendering to be useful.
if ! command -v nvidia-smi &>/dev/null || ! nvidia-smi &>/dev/null; then
    echo "❌ No NVIDIA GPU detected."
    echo "   This simulator requires an NVIDIA GPU with nvidia-container-toolkit installed."
    echo "   See https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
    exit 1
fi
echo "🖥  NVIDIA GPU detected — using hardware acceleration"
GPU_FLAGS=(--gpus all -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=all)

# Allow X11 forwarding
xhost +local:docker &>/dev/null || true

echo "🌙 Starting container (workspace mounted at /home/$USERNAME/artemis_workspace)"
exec docker run --rm -it \
    --name "$CONTAINER_NAME" \
    --hostname artemis \
    --network host \
    -e DISPLAY="${DISPLAY}" \
    -e QT_X11_NO_MITSHM=1 \
    -e WORKSPACE_DIR="/home/$USERNAME/artemis_workspace" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "$REPO_ROOT":/home/$USERNAME/artemis_workspace/src \
    ${GPU_FLAGS[@]+"${GPU_FLAGS[@]}"} \
    "$IMAGE_NAME"
