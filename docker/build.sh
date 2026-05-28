#!/usr/bin/env bash
# Build the Artemis Mission Simulator Docker image.
#
# Usage:
#   ./docker/build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE_NAME="artemis-mission-simulator:latest"

echo "🌕 Building $IMAGE_NAME (user: commander_${USER}, uid: $(id -u), gid: $(id -g))"
docker build \
    --build-arg HOST_USERNAME="${USER}" \
    --build-arg HOST_UID="$(id -u)" \
    --build-arg HOST_GID="$(id -g)" \
    -t "$IMAGE_NAME" \
    -f "$SCRIPT_DIR/Dockerfile" \
    "$SCRIPT_DIR"

echo "✅ Built: $IMAGE_NAME"
