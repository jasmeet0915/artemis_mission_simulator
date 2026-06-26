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
"""System Monitor panel: CPU / Memory / GPU / Disk / Network columns."""
from __future__ import annotations

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, ProgressBar, Sparkline, Static

from .. import theme
from ..state import DashboardState


def _head(label: str, value: str, value_style: str) -> Table:
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', style=theme.MUTED, ratio=1)
    grid.add_column(justify='right')
    grid.add_row(label, Text(value, style=f'bold {value_style}'))
    return grid


class SystemMonitorPanel(Horizontal):
    """Bordered card with five live telemetry columns."""

    DEFAULT_CSS = f"""
    SystemMonitorPanel {{ padding: 1 1; }}
    SystemMonitorPanel .mon-col {{ width: 1fr; padding: 0 1; }}
    SystemMonitorPanel .mon-sub {{ color: {theme.MUTED}; }}
    SystemMonitorPanel Sparkline {{ height: 3; margin-top: 1; }}
    SystemMonitorPanel Sparkline > .sparkline--max-color {{ color: {theme.PRIMARY}; }}
    SystemMonitorPanel Sparkline > .sparkline--min-color {{ color: {theme.FAINT}; }}
    SystemMonitorPanel #mem-spark > .sparkline--max-color {{ color: {theme.WARN}; }}
    SystemMonitorPanel #net-up-spark > .sparkline--max-color {{ color: {theme.OK}; }}
    SystemMonitorPanel #disk-bar {{ margin-top: 1; }}
    SystemMonitorPanel #disk-bar Bar > .bar--bar {{ color: {theme.PRIMARY}; }}
    SystemMonitorPanel #disk-bar Bar > .bar--complete {{ color: {theme.OK}; }}
    """

    def on_mount(self) -> None:
        self.border_title = 'SYSTEM MONITOR'

    def compose(self) -> ComposeResult:
        with Vertical(classes='mon-col'):
            yield Static(id='cpu-head')
            yield Sparkline([0.0], id='cpu-spark')
        with Vertical(classes='mon-col'):
            yield Static(id='mem-head')
            yield Sparkline([0.0], id='mem-spark')
            yield Label('', id='mem-sub', classes='mon-sub')
        with Vertical(classes='mon-col'):
            yield Static(id='gpu-head')
            yield Sparkline([0.0], id='gpu-spark')
            yield Label('', id='gpu-sub', classes='mon-sub')
        with Vertical(classes='mon-col'):
            yield Static(id='disk-head')
            yield ProgressBar(total=100, show_eta=False, id='disk-bar')
            yield Label('', id='disk-sub', classes='mon-sub')
        with Vertical(classes='mon-col'):
            yield Label('NETWORK', classes='mon-sub')
            yield Static(id='net-up-head')
            yield Sparkline([0.0], id='net-up-spark')
            yield Static(id='net-down-head')
            yield Sparkline([0.0], id='net-down-spark')

    def update_state(self, state: DashboardState) -> None:
        self.query_one('#cpu-head', Static).update(
            _head('CPU USAGE', f'{state.cpu_percent:.1f} %', theme.OK))
        self.query_one('#cpu-spark', Sparkline).data = list(state.cpu_history)

        self.query_one('#mem-head', Static).update(
            _head('MEMORY USAGE', f'{state.memory_percent:.1f} %', theme.OK))
        self.query_one('#mem-spark', Sparkline).data = list(state.memory_history)
        self.query_one('#mem-sub', Label).update(
            f'{state.memory_used:.1f} GiB / {state.memory_total:.1f} GiB')

        if state.gpu_percent is None:
            self.query_one('#gpu-head', Static).update(
                _head('GPU USAGE', 'N/A', theme.MUTED))
            self.query_one('#gpu-sub', Label).update('')
        else:
            self.query_one('#gpu-head', Static).update(
                _head('GPU USAGE', f'{state.gpu_percent:.1f} %', theme.OK))
            sub = ''
            if state.vram_used is not None and state.vram_total is not None:
                sub = f'VRAM {state.vram_used:.1f} / {state.vram_total:.1f} GiB'
            self.query_one('#gpu-sub', Label).update(sub)
        self.query_one('#gpu-spark', Sparkline).data = list(state.gpu_history)

        self.query_one('#disk-head', Static).update(
            _head('DISK USAGE', f'{state.disk_percent:.0f} %', theme.PRIMARY))
        self.query_one('#disk-bar', ProgressBar).update(
            total=100, progress=state.disk_percent)
        self.query_one('#disk-sub', Label).update(
            f'{state.disk_used:.0f}G / {state.disk_total:.0f}G')

        self.query_one('#net-up-head', Static).update(
            _head('UP', f'{state.network_up:.1f} KB/s ↑', theme.OK))
        self.query_one('#net-up-spark', Sparkline).data = list(state.net_up_history)
        self.query_one('#net-down-head', Static).update(
            _head('DOWN', f'{state.network_down:.1f} KB/s ↓', theme.PRIMARY))
        self.query_one('#net-down-spark', Sparkline).data = \
            list(state.net_down_history)
