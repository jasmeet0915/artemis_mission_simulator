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

"""Tests for the terrain ENU-alignment rotation."""

import math

from lunar_terrain_exporter.utils.frames import terrain_enu_rotation_rpy
import numpy as np
from numpy.testing import assert_allclose
from scipy.spatial.transform import Rotation

_STEREO = np.array([[0.0, 1.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 0.0, -1.0]])


def _matrix(lat, lon):
    r, p, y = terrain_enu_rotation_rpy(lat, lon)
    return Rotation.from_euler('xyz', [r, p, y]).as_matrix()


def _enu_axes(lat, lon):
    phi, lam = math.radians(lat), math.radians(lon)
    sp, cp, sl, cl = math.sin(phi), math.cos(phi), math.sin(lam), math.cos(lam)
    east = np.array([-sl, cl, 0.0])
    north = np.array([-sp * cl, -sp * sl, cp])
    up = np.array([cp * cl, cp * sl, sp])
    return east, north, up


class TestTerrainEnuRotation:
    def test_orthonormal_proper_rotation(self):
        R = _matrix(-88.7, -67.9)
        assert_allclose(R @ R.T, np.eye(3), atol=1e-9)
        assert_allclose(np.linalg.det(R), 1.0, atol=1e-9)

    def test_enu_axes_map_to_world_axes(self):
        lat, lon = -89.0, 123.7
        east, north, up = _enu_axes(lat, lon)
        R = _matrix(lat, lon)
        assert_allclose(R @ (_STEREO @ east), [1, 0, 0], atol=1e-9)
        assert_allclose(R @ (_STEREO @ north), [0, 1, 0], atol=1e-9)
        assert_allclose(R @ (_STEREO @ up), [0, 0, 1], atol=1e-9)

    def test_prime_meridian_is_pure_tilt(self):
        roll, pitch, yaw = terrain_enu_rotation_rpy(-89.0, 0.0)
        assert abs(yaw) < 1e-9
        assert abs(pitch) < 1e-9
        assert abs(roll) > 1e-3  # colatitude tilt present

    def test_rpy_convention_roundtrip(self):
        roll, pitch, yaw = terrain_enu_rotation_rpy(-88.6, -67.9)
        R = (Rotation.from_euler('z', yaw) *
             Rotation.from_euler('y', pitch) *
             Rotation.from_euler('x', roll)).as_matrix()
        assert_allclose(R, _matrix(-88.6, -67.9), atol=1e-9)

    def test_horizontal_matches_pyproj(self):
        from pyproj import CRS, Transformer
        lat, lon = -88.7, -67.9
        stereo_crs = CRS.from_proj4(
            '+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +k=1 '
            '+x_0=0 +y_0=0 +R=1737400 +units=m +no_defs')
        to_proj = Transformer.from_crs(
            stereo_crs.geodetic_crs, stereo_crs, always_xy=True)
        x0, y0 = to_proj.transform(lon, lat)
        xe, ye = to_proj.transform(lon + 1e-4, lat)  # +lon = East
        east_proj = np.array([xe - x0, ye - y0, 0.0])
        east_proj /= np.linalg.norm(east_proj)
        assert_allclose(_matrix(lat, lon) @ east_proj, [1, 0, 0], atol=1e-3)
