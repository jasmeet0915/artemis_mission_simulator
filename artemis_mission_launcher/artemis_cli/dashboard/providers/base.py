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
"""Shared provider base that drives the mission clock and overview fields."""
from __future__ import annotations

from datetime import datetime, timezone
import time

from ..state import DashboardState

_SOLAR_DAY_S = 708.7 * 3600.0  # lunar synodic day (~29.5 d) in seconds
_DEFAULT_EPOCH = 1893456000    # 2030-01-01T00:00:00Z


class Provider:
    """Base data provider. Call :meth:`update` once per frame."""

    def __init__(self, *, site: str = 'shackleton_rim',
                 epoch_sec: int = _DEFAULT_EPOCH,
                 acceleration: float = 100.0,
                 sky_source=None) -> None:
        self._epoch_sec = epoch_sec
        self._accel = acceleration
        self._start = time.monotonic()
        self._sky = sky_source
        self.site_name = site.replace('_', ' ').title()

    # -- to be implemented by subclasses --
    def _sample_system(self, state: DashboardState) -> None:
        raise NotImplementedError

    def hostname(self) -> str:
        raise NotImplementedError

    def uptime_seconds(self) -> float:
        raise NotImplementedError

    # -- shared frame update --
    def update(self, state: DashboardState) -> None:
        self._sample_system(state)

        state.hostname = self.hostname()
        state.uptime = _fmt_uptime(self.uptime_seconds())
        state.utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        sim_elapsed = (time.monotonic() - self._start) * self._accel
        mission_dt = datetime.fromtimestamp(
            self._epoch_sec + sim_elapsed, tz=timezone.utc)
        state.mission_date = mission_dt.strftime('%Y-%m-%d')
        state.mission_clock = mission_dt.strftime('%H:%M:%S')
        state.simulation_time = _fmt_sim(sim_elapsed)
        state.time_acceleration = self._accel
        state.solar_day_progress = (
            (self._epoch_sec + sim_elapsed) % _SOLAR_DAY_S) / _SOLAR_DAY_S

        state.site_name = self.site_name

        if self._sky is not None:
            sample = self._sky.latest
            # Never write None back: a tracker that goes quiet leaves the last
            # angles on screen rather than blanking the row.
            if sample is not None:
                state.sun_azimuth_deg, state.sun_elevation_deg = sample

        state.push_histories()


def _fmt_uptime(seconds: float) -> str:
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{days}d {hours:02d}:{minutes:02d}:{secs:02d}'


def _fmt_sim(seconds: float) -> str:
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{days:02d}:{hours:02d}:{minutes:02d}:{secs:02d}'
