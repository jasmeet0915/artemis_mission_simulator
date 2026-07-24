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

"""
Compute a celestial body's place over an observer's local lunar horizon.

Uses ephemeris data from SPICE kernels.

Note: The caller is responsible for furnishing the SPICE kernels (see
:class:`~lunar_sky_tracker.spice.kernel_manager.KernelManager`); an unfurnished
pool surfaces as a ``SpiceyError`` from the first SPICE call.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import math

import numpy as np
import spiceypy

MOON_FRAME = 'MOON_ME'
MOON = 'MOON'


@dataclass
class SkyObjectObservation:
    """A named sky object's direction over an observer's local lunar horizon."""

    name: str
    azimuth_deg: float
    elevation_deg: float
    direction_enu: tuple[float, float, float] = (0.0, 0.0, 0.0)


def posix_to_ephemeris_time(timestamp: float) -> float:
    """
    Convert a POSIX timestamp (seconds since the Unix epoch) to SPICE ET.

    :param timestamp: POSIX seconds timestamp.
    """
    # datetime rejects NaN and out-of-range values on its own, so let those
    # surface rather than restating the check here.
    utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return spiceypy.str2et(utc.strftime('%Y-%m-%dT%H:%M:%S.%f'))


def rotate_to_local_enu(
        vec_moon_me: np.ndarray,
        observer_moon_me: np.ndarray) -> np.ndarray:
    """
    Rotate a MOON_ME vector into the observer's local ENU frame.

    :param vec_moon_me: any rectangular MOON_ME vector.
    :param observer_moon_me: the observer's rectangular MOON_ME position, as
        from :func:`spiceypy.srfrec`; its surface normal defines up.
    """
    # Compute the surface normal at observer which is basically the local Up
    _count, radii = spiceypy.bodvrd(MOON, 'RADII', 3)
    up_axis = spiceypy.surfnm(radii[0], radii[1], radii[2], observer_moon_me)

    north_pole = np.array([0.0, 0.0, 1.0])

    # Computes rotation matrix by defining a frame using the local up as Z
    # projected north pole as Y and their cross product as X (east)
    m_rotation = spiceypy.twovec(up_axis, 3, north_pole, 2)

    return np.asarray(m_rotation) @ np.asarray(vec_moon_me)


def get_solar_system_body_position(
        body: str,
        timestamp: float,
        observer_lat_deg: float,
        observer_lon_deg: float,
        aberration_correction: str = 'LT+S') -> SkyObjectObservation:
    """
    Return a solar-system body's az/el over the local horizon at the observer.

    :param body: SPICE body name or id for the target, e.g. ``'SUN'``,
        ``'EARTH'``, ``'MARS BARYCENTER'``.
    :param timestamp: POSIX seconds timestamp.
    :param observer_lat_deg: Observer latitude degrees.
    :param observer_lon_deg: Observer longitude degrees.
    :param aberration_correction: SPICE aberration correction, ``'LT+S'``
        (apparent position) by default.
    """
    if not -90.0 < observer_lat_deg < 90.0:
        raise ValueError(
            f'Observer latitude {observer_lat_deg} is outside (-90, 90). The '
            'function does not support observations directly at the poles to '
            'avoid azimuth confusion.')

    ephemeris_time = posix_to_ephemeris_time(timestamp)
    lat_rad = math.radians(observer_lat_deg)
    lon_rad = math.radians(observer_lon_deg)

    # Body relative to the Moon's bodycenter in the MOON_ME frame
    body_in_moon_me, _light_time = spiceypy.spkpos(
        body, ephemeris_time, MOON_FRAME, aberration_correction, MOON)

    # Observer in the MOON_ME frame. Converting surface
    # lat/lon to rectangular using srfrec (surface to rectangular)
    observer_in_moon_me = spiceypy.srfrec(spiceypy.bodn2c(MOON), lon_rad, lat_rad)

    # Vector from the observer to the body. This is still in MOON_ME axes
    body_from_observer_moon_me = np.asarray(body_in_moon_me) - np.asarray(
        observer_in_moon_me)

    # Rotate the body vector in MOON_ME into the observer's local ENU frame, then
    # normalise: this unit vector is both what we publish and what feeds recazl.
    body_in_local_enu = rotate_to_local_enu(
        body_from_observer_moon_me, observer_in_moon_me)
    direction_enu = body_in_local_enu / np.linalg.norm(body_in_local_enu)

    # recazl would measures azimuth from +X toward -Y (increasing clockwise because
    # we set azccw as False), we rearrange the input vector such that the result
    # matches convention for azimuth (north is 0 degrees)
    east, north, up = direction_enu
    _range_km, azimuth_rad, elevation_rad = spiceypy.recazl(
        [north, -east, up], azccw=False, elplsz=True)

    return SkyObjectObservation(
        name=body,
        azimuth_deg=math.degrees(azimuth_rad),
        elevation_deg=math.degrees(elevation_rad),
        direction_enu=(float(east), float(north), float(up)))
