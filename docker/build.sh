#!/usr/bin/env bash
# Build the Artemis Mission Simulator Docker image.
#
# Usage:
#   ./docker/build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE_NAME="artemis-mission-simulator:latest"

echo "🔨 Building $IMAGE_NAME ..."
docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

echo "✅ Built: $IMAGE_NAME"
