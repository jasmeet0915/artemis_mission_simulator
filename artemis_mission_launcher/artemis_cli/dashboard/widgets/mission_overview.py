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
"""Mission Overview panel: site metadata + a simple ASCII spacecraft."""
from __future__ import annotations

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

# Simple ASCII spacecraft. Spaces are transparent (stars show through);
# '#' marks the window, flame rows are styled separately below.
_CRAFT = (
    '    /\\',
    '   /  \\',
    '   |  |',
    '   |##|',
    '   |  |',
    '  /|  |\\',
    ' / |  | \\',
    '/__|__|__\\',
    '   |||',
    '  \\|||/',
    '   \\|/',
    '    v',
)


def _spacecraft(width: int, height: int) -> Text:
    """Draw a centered ASCII spacecraft over a faint starfield."""
    grid = [[(' ', '') for _ in range(width)] for _ in range(height)]

    def put(x: int, y: int, ch: str, st: str) -> None:
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = (ch, st)

    for sx, sy in _STARS:
        put(sx, sy, '·', theme.FAINT)
    for sx, sy in _BRIGHT_STARS:
        put(sx, sy, '✦', theme.MUTED)

    art_w = max(len(line) for line in _CRAFT)
    left = (width - art_w) // 2
    top = (height - len(_CRAFT)) // 2
    for r, line in enumerate(_CRAFT):
        for c, ch in enumerate(line):
            if ch == ' ':
                continue
            if ch == '#':
                style = f'bold {theme.ACCENT}'
            elif r == len(_CRAFT) - 1:           # flame tip
                style = f'bold {theme.ACCENT}'
            elif r >= len(_CRAFT) - 3:            # exhaust flame
                style = theme.WARN
            else:                                 # hull / fins
                style = theme.PRIMARY
            put(left + c, top + r, ch, style)

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
