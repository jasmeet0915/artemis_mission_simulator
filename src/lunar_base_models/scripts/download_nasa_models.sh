#!/usr/bin/env bash
# Downloads NASA 3D Resources GLB models for lunar base simulation.
# Source: https://github.com/nasa/NASA-3D-Resources (public domain)
#
# Usage: ./download_nasa_models.sh [target_dir]
#   target_dir defaults to the models/ directory next to this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-${SCRIPT_DIR}/../models}"

BASE_URL="https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models"

declare -A DOWNLOADS=(
  ["${TARGET_DIR}/astronaut/meshes/astronaut.glb"]="${BASE_URL}/Astronaut/Astronaut.glb"
  ["${TARGET_DIR}/habitat_module/meshes/habitat_part1.glb"]="${BASE_URL}/Habitat%20Demonstration%20Unit/Habitat%20Demonstration%20Unit%20(part%201).glb"
  ["${TARGET_DIR}/habitat_module/meshes/habitat_part2.glb"]="${BASE_URL}/Habitat%20Demonstration%20Unit/Habitat%20Demonstration%20Unit%20(part%202).glb"
  ["${TARGET_DIR}/rassor/meshes/rassor.glb"]="${BASE_URL}/Regolith%20Advanced%20Surface%20Systems%20Operations%20Robot%20(RASSOR)/Regolith%20Advanced%20Surface%20Systems%20Operations%20Robot%20(RASSOR).glb"
)

echo "Downloading NASA 3D models to ${TARGET_DIR}..."

for dest in "${!DOWNLOADS[@]}"; do
  url="${DOWNLOADS[$dest]}"
  filename="$(basename "$dest")"
  if [[ -f "$dest" ]]; then
    echo "  [SKIP] ${filename} already exists"
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  echo "  [GET]  ${filename}..."
  curl -fSL -o "$dest" "$url"
  echo "  [OK]   ${filename} ($(du -h "$dest" | cut -f1))"
done

echo "Done. All NASA models downloaded."
