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
"""Assemble the Rich Layout and drive the live render loop."""
from __future__ import annotations

import time
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from .providers import Provider
from .state import DashboardState
from .widgets import footer, header, mission_clock, mission_overview, system_monitor
from .widgets.starfield import Starfield


def build_layout(state: DashboardState) -> Layout:
    """Compose the full dashboard for one frame, centred with edge margins."""
    # Outer row: fixed side margins flank the centred content column. Flexible
    # top/bottom spacers inside vertically centre the fixed-height content. The
    # margins and spacers carry a starfield so the content floats in space; each
    # region gets its own seed so the fields differ.
    root = Layout()
    root.split_row(
        Layout(Starfield(seed=1), name='left', size=4),
        Layout(name='center', ratio=1),
        Layout(Starfield(seed=2), name='right', size=4),
    )
    center = root['center']
    center.split_column(
        Layout(Starfield(seed=3), name='top', ratio=1),
        Layout(header.render(state), name='header', size=7),
        Layout(name='main', size=13),
        Layout(system_monitor.render(state), name='monitor', size=13),
        Layout(footer.render(state), name='footer', size=1),
        Layout(Starfield(seed=4), name='bottom', ratio=1),
    )
    center['main'].split_row(
        Layout(mission_overview.render(state), name='overview', ratio=53),
        Layout(mission_clock.render(state), name='clock', ratio=47),
    )
    return root


def run(provider: Provider, *, fps: int = 10,
        ticks: Optional[int] = None) -> None:
    """Boot the live dashboard and update it at ``fps`` until interrupted."""
    console = Console()
    state = DashboardState()
    period = 1.0 / fps
    count = 0
    with Live(build_layout(state), console=console, screen=True,
              refresh_per_second=fps) as live:
        while ticks is None or count < ticks:
            provider.update(state)
            live.update(build_layout(state))
            count += 1
            time.sleep(period)
