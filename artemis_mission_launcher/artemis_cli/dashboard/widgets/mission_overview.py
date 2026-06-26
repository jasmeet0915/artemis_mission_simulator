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
"""Mission Overview panel: site metadata + a polar south-pole moon plot."""
from __future__ import annotations

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import theme
from ..state import DashboardState

_CRATERS = ((0.34, -0.28), (-0.42, 0.18), (0.12, 0.46),
            (-0.22, -0.44), (0.46, 0.22), (-0.05, -0.12))


def _polar(width: int, height: int) -> Text:
    """A compass/polar disc: ring, crosshair, craters, centred site marker."""
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    rx, ry = (width - 1) / 2.0, (height - 1) / 2.0
    grid = [[(' ', '') for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            dx = (x - cx) / rx if rx else 0.0
            dy = (y - cy) / ry if ry else 0.0
            dist = (dx * dx + dy * dy) ** 0.5
            if 0.86 <= dist <= 1.04:
                grid[y][x] = ('◦', theme.PRIMARY)        # outer ring
            elif 0.44 <= dist <= 0.56:
                grid[y][x] = ('·', theme.FAINT)          # inner ring
            elif dist < 0.86 and (abs(x - cx) < 0.55 or abs(y - cy) < 0.55):
                grid[y][x] = ('·', theme.FAINT)          # crosshair

    def put(x: int, y: int, ch: str, st: str) -> None:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = (ch, st)

    for fx, fy in _CRATERS:
        put(int(round(cx + fx * rx)), int(round(cy + fy * ry)), '∘', theme.MUTED)
    put(int(round(cx)), int(round(cy)), '◉', theme.ACCENT)
    put(int(round(cx)), 0, 'N', theme.MUTED)
    put(int(round(cx)), height - 1, 'S', theme.MUTED)
    put(width - 1, int(round(cy)), 'E', theme.MUTED)
    put(0, int(round(cy)), 'W', theme.MUTED)

    text = Text()
    for r, row in enumerate(grid):
        for ch, st in row:
            text.append(ch, style=st)
        if r < height - 1:
            text.append('\n')
    return text


def _fields(state: DashboardState) -> RenderableType:
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


def render(state: DashboardState) -> RenderableType:
    body = Table.grid(expand=True, padding=(0, 1))
    body.add_column(justify='left', ratio=3)
    body.add_column(justify='center', ratio=2)
    body.add_row(
        Align(_fields(state), vertical='middle'),
        Align(_polar(21, 11), vertical='middle'),
    )
    return Panel(body, title=Text('MISSION OVERVIEW', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 1))
