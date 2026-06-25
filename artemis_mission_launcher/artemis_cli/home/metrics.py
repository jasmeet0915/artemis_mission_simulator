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
"""Live host-system metrics for the mission-control dashboard."""
from dataclasses import dataclass
import time

import psutil

_GIB = 1024 ** 3
_THERMAL_ZONE0 = '/sys/class/thermal/thermal_zone0/temp'


@dataclass
class SystemMetrics:
    """A single sample of host telemetry shown on the dashboard."""

    cpu_pct: float
    mem_used_gb: float
    mem_total_gb: float
    mem_pct: float
    temp_c: float | None
    disk_pct: float
    net_up_kbs: float
    net_down_kbs: float
    uptime_s: float


def _read_temp_c():
    """Return the hottest sensor reading in Celsius, or None if unavailable."""
    try:
        sensors = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        sensors = {}
    readings = [
        entry.current
        for entries in sensors.values()
        for entry in entries
        if entry.current
    ]
    if readings:
        return max(readings)
    try:
        with open(_THERMAL_ZONE0) as zone:
            return int(zone.read().strip()) / 1000.0
    except (OSError, ValueError):
        return None


class MetricsReader:
    """Stateful reader that turns psutil counters into per-tick rates."""

    def __init__(self):
        psutil.cpu_percent(interval=None)  # prime the rolling CPU average
        self._net = psutil.net_io_counters()
        self._net_t = time.monotonic()

    def read(self):
        """Sample the host and return a SystemMetrics."""
        vm = psutil.virtual_memory()
        net = psutil.net_io_counters()
        now = time.monotonic()
        dt = max(now - self._net_t, 1e-6)
        up = (net.bytes_sent - self._net.bytes_sent) / dt / 1024.0
        down = (net.bytes_recv - self._net.bytes_recv) / dt / 1024.0
        self._net = net
        self._net_t = now
        return SystemMetrics(
            cpu_pct=psutil.cpu_percent(interval=None),
            mem_used_gb=vm.used / _GIB,
            mem_total_gb=vm.total / _GIB,
            mem_pct=vm.percent,
            temp_c=_read_temp_c(),
            disk_pct=psutil.disk_usage('/').percent,
            net_up_kbs=max(up, 0.0),
            net_down_kbs=max(down, 0.0),
            uptime_s=time.time() - psutil.boot_time(),
        )
