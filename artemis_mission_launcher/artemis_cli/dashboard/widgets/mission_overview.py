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

import math

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import theme
from ..state import DashboardState

# Fixed background starfield (x, y) positions.
_STARS = ((2, 1), (7, 9), (23, 2), (25, 10), (19, 1), (5, 11), (21, 7),
          (12, 0), (1, 5), (16, 12))
_BRIGHT_STARS = ((25, 4), (3, 10), (14, 1))


def _orbit(width: int, height: int) -> Text:
    """A mission-control orbital scope: planet, elliptical orbit, spacecraft."""
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    grid = [[(' ', '') for _ in range(width)] for _ in range(height)]

    def put(x: float, y: float, ch: str, st: str) -> None:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < width and 0 <= yi < height:
            grid[yi][xi] = (ch, st)

    for sx, sy in _STARS:
        put(sx, sy, '·', theme.FAINT)
    for sx, sy in _BRIGHT_STARS:
        put(sx, sy, '✦', theme.MUTED)

    # elliptical orbit path (dotted)
    a, b = (width - 1) / 2.0 * 0.94, (height - 1) / 2.0 * 0.80
    for i in range(180):
        t = 2.0 * math.pi * i / 180.0
        put(cx + a * math.cos(t), cy + b * math.sin(t), '·', theme.PRIMARY)

    # central body — a small lit planet at the focus
    for y in range(height):
        for x in range(width):
            dx, dy = (x - cx) / 2.6, (y - cy) / 1.4
            if dx * dx + dy * dy <= 1.0:
                lit = 0.6 - 0.55 * dx
                if lit > 0.62:
                    grid[y][x] = ('●', f'bold {theme.ACCENT}')
                elif lit > 0.4:
                    grid[y][x] = ('●', theme.PRIMARY)
                else:
                    grid[y][x] = ('◗', theme.FAINT)

    # spacecraft marker on the orbit, with a short fading trail
    t0 = -0.7
    for k, (ch, st) in enumerate(
            ((' ', ''), ('·', theme.MUTED), ('·', theme.FAINT))):
        if k == 0:
            put(cx + a * math.cos(t0), cy + b * math.sin(t0),
                '◆', f'bold {theme.ACCENT}')
        else:
            tt = t0 - 0.13 * k
            put(cx + a * math.cos(tt), cy + b * math.sin(tt), ch, st)

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
        Align(_orbit(27, 13), vertical='middle'),
    )
    return Panel(body, title=Text('MISSION OVERVIEW', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 1))
