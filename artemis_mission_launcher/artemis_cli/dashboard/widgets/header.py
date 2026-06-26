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

from .. import theme
from ..state import DashboardState

# 5-row block bitmaps; drawn as 3 half-block rows so the wordmark stays legible.
_GLYPHS = {
    'A': ('01110', '10001', '11111', '10001', '10001'),
    'E': ('11111', '10000', '11110', '10000', '11111'),
    'I': ('11111', '00100', '00100', '00100', '11111'),
    'M': ('10001', '11011', '10101', '10001', '10001'),
    'R': ('11110', '10001', '11110', '10010', '10001'),
    'S': ('01111', '10000', '01110', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100'),
    ' ': ('00000', '00000', '00000', '00000', '00000'),
}
_HALF = {(0, 0): ' ', (1, 0): '▀', (0, 1): '▄', (1, 1): '█'}


def _big(text: str) -> str:
    glyphs = [_GLYPHS.get(c, _GLYPHS[' ']) for c in text.upper()]
    rows = []
    for top in range(0, 6, 2):
        cells = []
        for g in glyphs:
            up = g[top] if top < len(g) else '00000'
            lo = g[top + 1] if top + 1 < len(g) else '00000'
            cells.append(''.join(_HALF[(int(up[c]), int(lo[c]))] for c in range(5)))
        rows.append(' '.join(cells))
    return '\n'.join(rows)


_ARTEMIS = _big('ARTEMIS')


def _left() -> RenderableType:
    return Group(
        Text(_ARTEMIS, style=f'bold {theme.ACCENT}'),
        Text('MISSION LAUNCHER      v1.0.0', style=theme.MUTED),
    )


def _center() -> RenderableType:
    inner = Table.grid()
    inner.add_column(justify='center')
    inner.add_row(Text('✦', style=theme.ACCENT))
    inner.add_row(Text('Welcome, Commander', style=f'bold {theme.PRIMARY}'))
    inner.add_row(Text('All systems nominal.', style=theme.MUTED))
    return Align.center(inner, vertical='middle')


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
    grid.add_column(justify='left', ratio=5)
    grid.add_column(justify='center', ratio=6)
    grid.add_column(justify='right', ratio=4)
    grid.add_row(_left(), _center(), _right(state))
    return grid
