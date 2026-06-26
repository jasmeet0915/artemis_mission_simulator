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
"""Mission Overview panel: site metadata + a mission-control radar scope."""
from __future__ import annotations

import math

from rich.align import Align
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from .. import theme
from ..state import DashboardState

# Faint background starfield (x, y) positions for the radar scope.
_STARS = ((2, 1), (24, 2), (5, 11), (21, 9), (12, 0), (1, 6), (25, 6))


def _radar(width: int, height: int) -> Text:
    """A polar radar scope: range rings, crosshair, and a contact blip.

    Cells are ~twice as tall as wide, so the horizontal radius is taken at the
    full half-width while the vertical radius uses the half-height; this keeps
    the rings looking round rather than squashed.
    """
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    grid = [[(' ', '') for _ in range(width)] for _ in range(height)]

    def put(x: float, y: float, ch: str, st: str) -> None:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < width and 0 <= yi < height:
            grid[yi][xi] = (ch, st)

    # faint starfield behind the scope
    for sx, sy in _STARS:
        put(sx, sy, '·', theme.FAINT)

    # crosshair (drawn first so the rings sit on top at the axes)
    for x in range(width):
        put(x, cy, '─', theme.FAINT)
    for y in range(height):
        put(cx, y, '│', theme.FAINT)
    put(cx, cy, '┼', theme.FAINT)

    # concentric range rings
    for frac in (1.0, 0.66, 0.33):
        rx, ry = cx * frac, cy * frac
        for i in range(160):
            t = 2.0 * math.pi * i / 160.0
            put(cx + rx * math.cos(t), cy + ry * math.sin(t), '·', theme.PRIMARY)

    # a single contact blip riding the middle ring
    bt = -0.9
    put(cx + cx * 0.66 * math.cos(bt), cy + cy * 0.66 * math.sin(bt),
        '◉', f'bold {theme.ACCENT}')

    text = Text()
    for r, row in enumerate(grid):
        for ch, st in row:
            text.append(ch, style=st)
        if r < height - 1:
            text.append('\n')
    return text


def _fields(state: DashboardState) -> Table:
    visible = ('YES', theme.OK) if state.earth_visible else ('NO', theme.ERR)
    rows = (
        ('◆', 'SITE', state.site_name.upper(), theme.PRIMARY),
        ('✧', 'COORDINATES', state.coordinates, theme.PRIMARY),
        ('▲', 'ELEVATION', state.elevation, theme.PRIMARY),
        ('☀', 'SUN ELEVATION', state.sun_elevation, theme.WARN),
        ('⊕', 'EARTH VISIBILITY', visible[0], visible[1]),
        ('☾', 'CURRENT PHASE', state.mission_phase.upper(), theme.ACCENT),
    )
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style=theme.FAINT, justify='center', width=1)
    grid.add_column(style=theme.MUTED, justify='left')
    grid.add_column(justify='left')
    for icon, label, value, style in rows:
        grid.add_row(icon, label, Text(value, style=style))
    return grid


class MissionOverviewPanel(Static):
    """Bordered card: site metadata on the left, radar scope on the right."""

    def on_mount(self) -> None:
        self.border_title = 'MISSION OVERVIEW'

    def update_state(self, state: DashboardState) -> None:
        body = Table.grid(expand=True, padding=(0, 1))
        body.add_column(justify='left', ratio=3)
        body.add_column(justify='center', ratio=2)
        body.add_row(
            Align(_fields(state), vertical='middle'),
            Align(_radar(27, 13), vertical='middle'),
        )
        self.update(body)
