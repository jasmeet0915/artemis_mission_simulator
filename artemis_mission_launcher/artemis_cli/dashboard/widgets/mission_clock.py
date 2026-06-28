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

from .glyphs import big_text
from .. import theme
from ..state import DashboardState


def _stats(state: DashboardState) -> RenderableType:
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='left', ratio=1)
    grid.add_row(Text('SIM TIME ELAPSED', style=theme.MUTED),
                 Text('TIME ACCELERATION', style=theme.MUTED))
    grid.add_row(Text(state.simulation_time, style=theme.PRIMARY),
                 Text(f'{state.time_acceleration:.1f}x', style=theme.WARN))
    return grid


def render(state: DashboardState) -> RenderableType:
    body = Group(
        Text(state.mission_date, style=f'bold {theme.PRIMARY}'),
        Text(''),
        big_text(state.mission_clock, style=f'bold {theme.ACCENT}'),
        Text('UTC', style=theme.MUTED),
        Rule(style=theme.FAINT),
        _stats(state),
    )
    return Panel(body, title=Text('MISSION CLOCK', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 2))
