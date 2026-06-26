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
"""Immutable-ish snapshot of everything the dashboard renders.

Widgets receive a :class:`DashboardState` and never query psutil/ROS directly;
providers own the data collection and mutate the state each tick.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

HISTORY = 30  # samples kept for sparklines / charts


def _hist() -> Deque[float]:
    return deque(maxlen=HISTORY)


@dataclass
class DashboardState:
    """All values shown on the dashboard for a single frame."""

    # --- header ---
    utc_time: str = '------ -- --:--:--'
    uptime: str = '0d 00:00:00'
    hostname: str = 'artemis'

    # --- mission overview ---
    site_name: str = 'Shackleton Rim'
    coordinates: str = '89.76° S, 0.00° E'
    elevation: str = '-3923 m'
    sun_elevation: str = '1.23°'
    earth_visible: bool = True
    mission_phase: str = 'Surface Ops'

    # --- mission clock ---
    mission_date: str = '2030-01-15'
    mission_clock: str = '08:32:11'
    simulation_time: str = '01:23:45:67'
    time_acceleration: float = 100.0
    solar_day_progress: float = 0.05

    # --- system monitor ---
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used: float = 0.0   # GiB
    memory_total: float = 0.0  # GiB
    gpu_percent: Optional[float] = None
    vram_used: Optional[float] = None   # GiB
    vram_total: Optional[float] = None  # GiB
    disk_used: float = 0.0     # GiB
    disk_total: float = 0.0    # GiB
    disk_percent: float = 0.0
    network_up: float = 0.0    # KB/s
    network_down: float = 0.0  # KB/s

    # --- rolling histories (oldest -> newest) ---
    cpu_history: Deque[float] = field(default_factory=_hist)
    memory_history: Deque[float] = field(default_factory=_hist)
    gpu_history: Deque[float] = field(default_factory=_hist)
    net_up_history: Deque[float] = field(default_factory=_hist)
    net_down_history: Deque[float] = field(default_factory=_hist)

    def push_histories(self) -> None:
        """Append the current scalar samples onto the rolling buffers."""
        self.cpu_history.append(self.cpu_percent)
        self.memory_history.append(self.memory_percent)
        self.gpu_history.append(self.gpu_percent or 0.0)
        self.net_up_history.append(self.network_up)
        self.net_down_history.append(self.network_down)
