# Copyright 2026 Jasmeet Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Frame math: rotation aligning a polar-stereo terrain to local ENU."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation


def terrain_enu_rotation_rpy(
    lat_deg: float, lon_deg: float,
) -> tuple[float, float, float]:
    """
    Compute roll/pitch/yaw aligning a polar-stereo terrain to local ENU.

    Returns SDF ``xyz`` Euler angles (radians) that rotate a south-polar-
    stereographic terrain so local ENU at ``(lat_deg, lon_deg)`` aligns with
    Gazebo world axes (X=East, Y=North, Z=Up).

    Assumes the source CRS is south-polar-stereographic with ``lon_0=0`` (the
    PGDA-78 lunar DEM CRS); east-positive longitude. The returned angles satisfy
    ``R = Rz(yaw) @ Ry(pitch) @ Rx(roll)`` and map the terrain's stereo axes onto
    local ENU.
    """
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    sp, cp = math.sin(phi), math.cos(phi)
    sl, cl = math.sin(lam), math.cos(lam)

    # Local ENU axes in ECEF / MOON_ME (sphere: radial == surface normal).
    east = np.array([-sl, cl, 0.0])
    north = np.array([-sp * cl, -sp * sl, cp])
    up = np.array([cp * cl, cp * sl, sp])

    # Polar-stereographic world axes in ECEF (south pole, lon_0=0):
    # world +X = +Y_ecef, +Y = +X_ecef, +Z = -Z_ecef. Verified against pyproj
    # (reproduces East@worldX = -lon).
    stereo = np.array([[0.0, 1.0, 0.0],
                       [1.0, 0.0, 0.0],
                       [0.0, 0.0, -1.0]])
    enu = np.array([east, north, up])

    # P[i][j] = enu_i . stereo_j -> maps stereo-frame components to ENU.
    rotation = enu @ stereo.T
    roll, pitch, yaw = Rotation.from_matrix(rotation).as_euler('xyz')
    return float(roll), float(pitch), float(yaw)
