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
"""Header widget: ARTEMIS wordmark, welcome line, and UTC/uptime/host table."""
from __future__ import annotations

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .glyphs import big_text
from .. import theme
from ..state import DashboardState


def _left() -> RenderableType:
    return Group(
        big_text('ARTEMIS', style=f'bold {theme.ACCENT}'),
        Text('MISSION LAUNCHER      v1.0.0', style=theme.MUTED),
    )


def _center() -> RenderableType:
    greeting = Text('Welcome, Commander', style=f'bold {theme.ACCENT}',
                    justify='center')
    subtitle = Text(justify='center')
    subtitle.append('All systems ', style=theme.MUTED)
    subtitle.append('nominal', style=f'bold {theme.OK}')
    subtitle.append('.', style=theme.MUTED)
    card = Panel(Group(greeting, subtitle), box=theme.BOX,
                 border_style=theme.BORDER, padding=(0, 2))
    return Align.center(card, vertical='middle')


def _right(state: DashboardState) -> RenderableType:
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style=theme.MUTED, justify='left')
    grid.add_column(style=theme.PRIMARY, justify='left')
    grid.add_row('◷ UTC TIME', Text(state.utc_time, style=theme.ACCENT))
    grid.add_row('⊙ UPTIME', Text(state.uptime, style=theme.PRIMARY))
    grid.add_row('◆ HOST', Text(state.hostname, style=theme.OK))
    return Panel(grid, box=theme.BOX, border_style=theme.BORDER,
                 padding=(0, 1))


def render(state: DashboardState) -> RenderableType:
    grid = Table.grid(expand=True)
    # symmetric side columns keep the centred Welcome card screen-centred
    grid.add_column(justify='left', ratio=5)
    grid.add_column(justify='center', ratio=6)
    grid.add_column(justify='right', ratio=5)
    grid.add_row(_left(), _center(), _right(state))
    return grid
