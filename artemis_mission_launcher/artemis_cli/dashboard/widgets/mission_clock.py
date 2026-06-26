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
"""Mission Clock panel: large clock, sim time, acceleration, solar-day bar."""
from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .. import theme
from ..state import DashboardState
from .glyphs import big_text
from .sparklines import hbar


def _stats(state: DashboardState) -> RenderableType:
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='left', ratio=1)
    grid.add_row(Text('SIM TIME ELAPSED', style=theme.MUTED),
                 Text('TIME ACCELERATION', style=theme.MUTED))
    grid.add_row(Text(state.simulation_time, style=theme.PRIMARY),
                 Text(f'{state.time_acceleration:.1f}x', style=theme.WARN))
    return grid


def _solar(state: DashboardState) -> RenderableType:
    pct = state.solar_day_progress * 100.0
    bar = Table.grid(expand=True)
    bar.add_column(ratio=1)
    bar.add_column(justify='right', width=6)
    bar.add_row(hbar(state.solar_day_progress, 28, theme.PRIMARY, theme.FAINT),
                Text(f'{pct:.0f}%', style=theme.MUTED))
    return Group(Text('SOLAR DAY @ SOUTH POLE', style=theme.MUTED), bar)


def render(state: DashboardState) -> RenderableType:
    body = Group(
        Text(state.mission_date, style=f'bold {theme.PRIMARY}'),
        big_text(state.mission_clock, style=f'bold {theme.ACCENT}'),
        Text('UTC', style=theme.MUTED),
        Rule(style=theme.FAINT),
        _stats(state),
        Text(''),
        _solar(state),
    )
    return Panel(body, title=Text('MISSION CLOCK', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 2))
