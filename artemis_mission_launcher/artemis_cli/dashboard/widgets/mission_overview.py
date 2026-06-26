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

# (x, y, radius) craters in normalised disc coordinates.
_CRATERS = ((-0.30, -0.18, 0.17), (-0.04, 0.30, 0.13), (0.20, -0.30, 0.11),
            (-0.44, 0.22, 0.10), (0.30, 0.20, 0.12), (0.06, -0.02, 0.07))
_SURF = ' ·:∘oO'          # moon-surface brightness ramp
_RINGS = (0.34, 0.67, 1.0)
_SPOKES = tuple(range(0, 360, 30))


def _moon_plot(width: int, height: int) -> Text:
    """Shaded lunar disc (lit on the left) under a polar graticule + compass."""
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    rx, ry = (width - 1) / 2.0, (height - 1) / 2.0
    grid = [[(' ', '') for _ in range(width)] for _ in range(height)]

    for y in range(height):
        for x in range(width):
            nx = (x - cx) / rx if rx else 0.0
            ny = (y - cy) / ry if ry else 0.0
            dist = math.hypot(nx, ny)
            if dist > 1.0:
                continue
            bright = 0.78 - 0.36 * nx                     # waxing-gibbous look
            for ccx, ccy, cr in _CRATERS:
                if math.hypot(nx - ccx, ny - ccy) < cr:
                    bright -= 0.4
            bright = min(max(bright, 0.12), 1.0)          # faint floor: full disc
            ch = _SURF[int(bright * (len(_SURF) - 1))]
            grid[y][x] = (ch, theme.MUTED if bright > 0.45 else theme.FAINT)

            ang = math.degrees(math.atan2(ny, nx)) % 360
            on_ring = any(abs(dist - r) < 0.05 for r in _RINGS)
            on_spoke = dist > 0.12 and min(
                (abs(ang - s) for s in _SPOKES + (360,))) < 2.2
            if on_ring or on_spoke:
                grid[y][x] = ('·', theme.FAINT)

    def put(x: int, y: int, ch: str, st: str) -> None:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = (ch, st)

    put(int(round(cx)), int(round(cy)), '◉', f'bold {theme.ACCENT}')
    put(int(round(cx)), 0, 'N', theme.PRIMARY)
    put(int(round(cx)), height - 1, 'S', theme.PRIMARY)
    put(width - 1, int(round(cy)), 'E', theme.PRIMARY)
    put(0, int(round(cy)), 'W', theme.PRIMARY)

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
        Align(_moon_plot(27, 13), vertical='middle'),
    )
    return Panel(body, title=Text('MISSION OVERVIEW', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 1), style=theme.ON_BG)
