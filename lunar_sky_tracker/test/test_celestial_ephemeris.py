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
Implementation tests for the SPICE celestial ephemeris core.

These cover the module's contract: return types, output ranges, input
validation, error wrapping and determinism. They deliberately do **not**
assert that the computed angles are astronomically correct — scientific
validation is handled separately, outside the unit test suite.
"""

import math

from lunar_sky_tracker.spice.celestial_ephemeris import (
    get_solar_system_body_position,
    posix_to_ephemeris_time,
    rotate_to_local_enu,
    SkyObjectObservation,
)
from lunar_sky_tracker.spice.kernel_manager import KernelManager
import numpy as np
import pytest
import spiceypy
from spiceypy.utils.exceptions import SpiceyError

# 2026-01-01T00:00:00Z, comfortably inside every furnished kernel's coverage.
EPOCH = 1767225600.0

# The SPICE body used throughout these tests; the pathway is body-agnostic.
SUN = 'SUN'

# A spread of observers: equator, mid-latitudes, and an Artemis-like polar site.
SAMPLE_SITES = [
    (0.0, 0.0),
    (45.0, 90.0),
    (-45.0, -120.0),
    (-89.9, 0.0),
    (12.5, 179.9),
]


@pytest.fixture(scope='module', autouse=True)
def furnished_kernels():
    """Furnish the pinned kernel set once for every test in this module."""
    manager = KernelManager()
    manager.furnish()
    yield manager
    manager.unload()


class TestSkyObjectObservation:
    def test_exposes_its_fields(self):
        position = SkyObjectObservation(
            name='sun', azimuth_deg=12.0, elevation_deg=-3.0)
        assert position.name == 'sun'
        assert position.azimuth_deg == 12.0
        assert position.elevation_deg == -3.0


class TestPosixToEphemerisTime:
    def test_matches_str2et_for_the_same_utc_instant(self):
        """The sub-second case also guards the '%f' in the strftime format."""
        assert posix_to_ephemeris_time(EPOCH) == pytest.approx(
            spiceypy.str2et('2026-01-01T00:00:00.000000'), abs=1e-6)

        # Another assertion for a non-integer second timestamp
        assert posix_to_ephemeris_time(EPOCH + 0.25) == pytest.approx(
            spiceypy.str2et('2026-01-01T00:00:00.250000'), abs=1e-6)

    @pytest.mark.parametrize('timestamp,expected', [
        (float('nan'), ValueError),
        (float('inf'), OverflowError),
        (float('-inf'), OverflowError),
        (1e30, (OverflowError, OSError)),
    ])
    def test_unusable_timestamps_raise(self, timestamp, expected):
        with pytest.raises(expected):
            posix_to_ephemeris_time(timestamp)


class TestRotateToLocalEnu:
    # Probes covering each axis, an oblique direction, and a Sun-scale magnitude.
    VECTORS = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.3, -0.7, 0.5],
        [1.4e8, -2.1e7, 9.0e6],
    ]

    @staticmethod
    def observer(lat, lon):
        return spiceypy.srfrec(
            spiceypy.bodn2c('MOON'), math.radians(lon), math.radians(lat))

    def test_known_axes_at_reference_points(self):
        """At (0, 0) the body-fixed axes map onto ENU in a known way."""
        observer = self.observer(0.0, 0.0)
        assert np.allclose(
            rotate_to_local_enu([1.0, 0.0, 0.0], observer),
            [0.0, 0.0, 1.0], atol=1e-12)  # prime meridian -> up
        assert np.allclose(
            rotate_to_local_enu([0.0, 1.0, 0.0], observer),
            [1.0, 0.0, 0.0], atol=1e-12)  # 90E -> east
        assert np.allclose(
            rotate_to_local_enu([0.0, 0.0, 1.0], observer),
            [0.0, 1.0, 0.0], atol=1e-12)  # polar axis -> north

    @pytest.mark.parametrize('lat,lon', SAMPLE_SITES)
    def test_preserves_magnitude(self, lat, lon):
        """A pure rotation, so only the components change."""
        observer = self.observer(lat, lon)
        for vector in self.VECTORS:
            rotated = rotate_to_local_enu(vector, observer)
            assert np.linalg.norm(rotated) == pytest.approx(
                np.linalg.norm(vector), rel=1e-12)


class TestGetSolarSystemBodyPosition:
    @pytest.mark.parametrize('lat,lon', SAMPLE_SITES)
    def test_returns_a_well_formed_observation(self, lat, lon):
        """The observation names the requested body and is self-consistent."""
        position = get_solar_system_body_position(SUN, EPOCH, lat, lon)
        assert position.name == SUN
        assert 0.0 <= position.azimuth_deg < 360.0
        assert -90.0 <= position.elevation_deg <= 90.0
        assert np.linalg.norm(position.direction_enu) == pytest.approx(
            1.0, abs=1e-12)

        # The published vector must be the az/el reconstructed as ENU;
        # azimuth is from north toward east, so north takes cos and east sin.
        az = math.radians(position.azimuth_deg)
        el = math.radians(position.elevation_deg)
        expected = np.array([
            math.cos(el) * math.sin(az),
            math.cos(el) * math.cos(az),
            math.sin(el)])
        assert np.allclose(position.direction_enu, expected, atol=1e-9)

    def test_works_with_different_spice_bodies(self):
        """The body argument selects the target; the pathway is unchanged."""
        earth = 'EARTH'
        sun = 'SUN'

        earth_obs = get_solar_system_body_position(earth, EPOCH, -89.9, 0.0)
        assert earth_obs.name == earth

        sun_obs = get_solar_system_body_position(sun, EPOCH, -89.9, 0.0)
        assert sun_obs.name == sun
        assert earth_obs.direction_enu != sun_obs.direction_enu

        # Test unkown body raises
        with pytest.raises(SpiceyError):
            get_solar_system_body_position('NOT_A_BODY', EPOCH, 0.0, 0.0)

    def test_tracks_the_body_across_a_full_lunar_month(self):
        previous = None
        for hours in range(0, 30 * 24, 6):
            position = get_solar_system_body_position(SUN, EPOCH + hours * 3600, -89.9, 0.0)
            assert 0.0 <= position.azimuth_deg < 360.0
            assert -90.0 <= position.elevation_deg <= 90.0

            # The epoch must reach the computation, not be quietly ignored
            assert position != previous
            previous = position

    def test_latitude_is_bounded_but_longitude_wraps(self):
        """Latitude is checked against the open interval (-90, 90)."""
        # Out of range latitudes should raise ValueError
        for lat in (90.0, -90.0, 90.001, -90.001, 120.0, -1000.0):
            with pytest.raises(ValueError, match='latitude'):
                get_solar_system_body_position(SUN, EPOCH, lat, 0.0)

        # No exceptions if latitude is within bounds
        for lat in (89.999999, -89.999999, 0.0):
            assert isinstance(
                get_solar_system_body_position(SUN, EPOCH, lat, 0.0),
                SkyObjectObservation)

        # Longitude is not bounded and wraps around
        # Computation for 40 and 360 + 40 degrees should be same
        base = get_solar_system_body_position(SUN, EPOCH, 30.0, 40.0)
        wrapped = get_solar_system_body_position(SUN, EPOCH, 30.0, 400.0)
        assert wrapped.azimuth_deg == pytest.approx(base.azimuth_deg, abs=1e-9)
        assert wrapped.elevation_deg == pytest.approx(
            base.elevation_deg, abs=1e-9)

    def test_aberration_correction_is_selectable(self):
        """The documented default is 'LT+S', the apparent position."""
        assert get_solar_system_body_position(
            SUN, EPOCH, 0.0, 0.0) == get_solar_system_body_position(
            SUN, EPOCH, 0.0, 0.0, aberration_correction='LT+S')

        # Every standard reception correction is accepted
        for abcorr in ('NONE', 'LT', 'LT+S', 'CN', 'CN+S'):
            assert isinstance(
                get_solar_system_body_position(
                    SUN, EPOCH, 10.0, 20.0, aberration_correction=abcorr),
                SkyObjectObservation)

        # Anything else is rejected by SPICE
        with pytest.raises(SpiceyError):
            get_solar_system_body_position(SUN, EPOCH, 0.0, 0.0, aberration_correction='BOGUS')

    def test_epoch_outside_ephemeris_coverage_raises(self):
        # Year 2400 — beyond de440s.bsp's 2150 coverage limit.
        with pytest.raises(SpiceyError):
            get_solar_system_body_position(SUN, 13569465600.0, 0.0, 0.0)

    def test_unfurnished_kernels_raise(self, furnished_kernels):
        spiceypy.kclear()
        try:
            with pytest.raises(SpiceyError):
                get_solar_system_body_position(SUN, EPOCH, 0.0, 0.0)
        finally:
            furnished_kernels.furnish()
