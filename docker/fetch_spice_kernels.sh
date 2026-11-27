#!/usr/bin/env bash
# Download the pinned NASA SPICE generic kernels into the image.
#
# Authoritative set: lunar_sky_tracker/lunar_sky_tracker/spice/kernel_manifest.py
# Keep this list in sync with it. KernelManager.furnish() verifies these exact
# filenames at runtime and fails loudly if the set drifts.
set -euo pipefail

KERNEL_DIR="${1:-/opt/spice_kernels}"
NAIF_BASE="https://naif.jpl.nasa.gov/pub/naif/generic_kernels"

KERNEL_URLS=(
    "${NAIF_BASE}/lsk/naif0012.tls"
    "${NAIF_BASE}/spk/planets/de440s.bsp"
    "${NAIF_BASE}/pck/pck00011.tpc"
    "${NAIF_BASE}/pck/moon_pa_de440_200625.bpc"
    "${NAIF_BASE}/fk/satellites/moon_de440_250416.tf"
)

mkdir -p "${KERNEL_DIR}"
for url in "${KERNEL_URLS[@]}"; do
    echo "Downloading ${url}"
    wget --no-verbose --directory-prefix="${KERNEL_DIR}" "${url}"
done
echo "SPICE kernels downloaded to ${KERNEL_DIR}:"
ls -la "${KERNEL_DIR}"
