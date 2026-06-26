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

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .sparklines import column_chart, hbar, sparkline
from .. import theme
from ..state import DashboardState

_CHART_W = 20
_CHART_H = 5


def _title(label: str, value: str, value_style: str) -> RenderableType:
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', style=theme.MUTED, ratio=1)
    grid.add_column(justify='right')
    grid.add_row(label, Text(value, style=f'bold {value_style}'))
    return grid


def _axis_chart(history, color: str) -> RenderableType:
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style=theme.FAINT, justify='right')
    grid.add_column()
    axis = Text('100%\n\n50%\n\n0%', style=theme.FAINT)
    grid.add_row(axis, column_chart(history, _CHART_W, _CHART_H, color, vmax=100))
    return grid


def _cpu(state: DashboardState) -> RenderableType:
    return Group(_title('CPU USAGE', f'{state.cpu_percent:.1f} %', theme.OK),
                 _axis_chart(state.cpu_history, theme.PRIMARY))


def _memory(state: DashboardState) -> RenderableType:
    return Group(
        _title('MEMORY USAGE', f'{state.memory_percent:.1f} %', theme.OK),
        _axis_chart(state.memory_history, theme.WARN),
        Text(f'{state.memory_used:.1f} GiB / {state.memory_total:.1f} GiB',
             style=theme.WARN))


def _gpu(state: DashboardState) -> RenderableType:
    if state.gpu_percent is None:
        body = Text('\n   N/A', style=theme.MUTED)
        return Group(_title('GPU USAGE', 'N/A', theme.MUTED), body)
    sub = ''
    if state.vram_used is not None and state.vram_total is not None:
        sub = f'VRAM {state.vram_used:.1f} GiB / {state.vram_total:.1f} GiB'
    return Group(_title('GPU USAGE', f'{state.gpu_percent:.1f} %', theme.OK),
                 _axis_chart(state.gpu_history, theme.PRIMARY),
                 Text(sub, style=theme.MUTED))


def _disk(state: DashboardState) -> RenderableType:
    frac = state.disk_percent / 100.0
    return Group(
        _title('DISK USAGE', f'{state.disk_percent:.0f} %', theme.PRIMARY),
        Text(''),
        hbar(frac, _CHART_W, theme.PRIMARY, theme.FAINT),
        Text(''),
        Text(f'{state.disk_used:.0f}G / {state.disk_total:.0f}G',
             style=theme.MUTED))


def _network(state: DashboardState) -> RenderableType:
    return Group(
        Text('NETWORK', style=theme.MUTED),
        Text(''),
        Text.assemble(('UP    ', theme.MUTED),
                      (f'{state.network_up:.1f} KB/s ↑', theme.OK)),
        Text(sparkline(state.net_up_history, _CHART_W), style=theme.OK),
        Text(''),
        Text.assemble(('DOWN  ', theme.MUTED),
                      (f'{state.network_down:.1f} KB/s ↓', theme.PRIMARY)),
        Text(sparkline(state.net_down_history, _CHART_W), style=theme.PRIMARY))


def _sep() -> Text:
    return Text('\n'.join('┊' for _ in range(8)), style=theme.FAINT)


def render(state: DashboardState) -> RenderableType:
    grid = Table.grid(expand=True, padding=(0, 1))
    cols = (_cpu(state), _memory(state), _gpu(state), _disk(state),
            _network(state))
    renderables = []
    for i, col in enumerate(cols):
        grid.add_column(ratio=1)
        renderables.append(col)
        if i < len(cols) - 1:
            grid.add_column(width=1)
            renderables.append(_sep())
    grid.add_row(*renderables)
    return Panel(grid, title=Text('SYSTEM MONITOR', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 1))
