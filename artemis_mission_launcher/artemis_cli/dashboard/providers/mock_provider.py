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
"""Deterministic-ish mock telemetry (random walk) so the UI runs anywhere."""
from __future__ import annotations

import random
import time

from ..state import DashboardState
from .base import Provider


def _walk(value: float, lo: float, hi: float, step: float) -> float:
    return min(hi, max(lo, value + random.uniform(-step, step)))


class MockProvider(Provider):
    """Fills the system-monitor scalars with a bounded random walk."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._start_wall = time.time()
        self._cpu = 18.7
        self._mem = 41.2
        self._gpu = 23.4
        self._up = 12.4
        self._down = 98.7

    def hostname(self) -> str:
        return 'artemis'

    def uptime_seconds(self) -> float:
        return time.time() - self._start_wall + 767.0  # ~0d 00:12:47 to start

    def _sample_system(self, state: DashboardState) -> None:
        self._cpu = _walk(self._cpu, 3, 95, 4)
        self._mem = _walk(self._mem, 20, 80, 2)
        self._gpu = _walk(self._gpu, 0, 90, 5)
        self._up = _walk(self._up, 0, 400, 8)
        self._down = _walk(self._down, 0, 800, 20)

        state.cpu_percent = self._cpu
        state.memory_percent = self._mem
        state.memory_used = self._mem / 100.0 * 15.6
        state.memory_total = 15.6
        state.gpu_percent = self._gpu
        state.vram_used = self._gpu / 100.0 * 8.0
        state.vram_total = 8.0
        state.disk_used = 89.0
        state.disk_total = 317.0
        state.disk_percent = 28.0
        state.network_up = self._up
        state.network_down = self._down
