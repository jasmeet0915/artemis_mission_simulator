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
"""Real host telemetry via psutil."""
from __future__ import annotations

import socket
import time

import psutil

from ..state import DashboardState
from .base import Provider

_GIB = 1024 ** 3


class SystemProvider(Provider):
    """Fills the system-monitor scalars from psutil; GPU left as N/A."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._hostname = socket.gethostname()
        self._boot = psutil.boot_time()
        psutil.cpu_percent(interval=None)  # prime
        self._net = psutil.net_io_counters()
        self._net_t = time.monotonic()

    def hostname(self) -> str:
        return self._hostname

    def uptime_seconds(self) -> float:
        return time.time() - self._boot

    def _sample_system(self, state: DashboardState) -> None:
        state.cpu_percent = psutil.cpu_percent(interval=None)

        vm = psutil.virtual_memory()
        state.memory_percent = vm.percent
        state.memory_used = vm.used / _GIB
        state.memory_total = vm.total / _GIB

        # GPU stats are not available through psutil — report N/A, never fail.
        state.gpu_percent = None
        state.vram_used = None
        state.vram_total = None

        disk = psutil.disk_usage('/')
        state.disk_used = disk.used / _GIB
        state.disk_total = disk.total / _GIB
        state.disk_percent = disk.percent

        net = psutil.net_io_counters()
        now = time.monotonic()
        dt = max(now - self._net_t, 1e-6)
        state.network_up = max((net.bytes_sent - self._net.bytes_sent) / dt / 1024.0, 0.0)
        state.network_down = max((net.bytes_recv - self._net.bytes_recv) / dt / 1024.0, 0.0)
        self._net = net
        self._net_t = now
