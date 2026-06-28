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
"""Mission Overview panel: site metadata + a satellite over a starfield."""
from __future__ import annotations

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import theme
from ..state import DashboardState

_PANEL = theme.PRIMARY            # solar-array cells
_FRAME = theme.MUTED              # panel / bus framing
_BUS = f'bold {theme.ACCENT}'     # central body + sensor
_BOOM = theme.FAINT               # booms, mast, stars
_SIGNAL = f'bold {theme.WARN}'    # transmitting antenna

# Satellite drawn as styled segments per row: two solar-array wings on booms
# flanking a central bus with a sensor eye, and a downlink antenna below.
_SAT = (
    (('  ', ''), ('┌───┐', _FRAME), ('       ', ''), ('┌───┐', _FRAME),
     ('  ✦', _BOOM)),
    (('  ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME),
     ('       ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME)),
    (('  ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME),
     ('  ', ''), ('┌─┐', _BUS), ('  ', ''),
     ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME)),
    (('  ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME),
     ('══', _BOOM), ('┤', _BUS), ('◉', _BUS), ('├', _BUS), ('══', _BOOM),
     ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME)),
    (('  ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME),
     ('  ', ''), ('└┬┘', _BUS), ('  ', ''),
     ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME)),
    (('  ', ''), ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME),
     ('   ', ''), ('│', _BOOM), ('   ', ''),
     ('│', _FRAME), ('▦▦▦', _PANEL), ('│', _FRAME)),
    (('  ', ''), ('└───┘', _FRAME), ('   ', ''), ('│', _BOOM),
     ('   ', ''), ('└───┘', _FRAME)),
    (('          ', ''), ('│', _BOOM)),
    (('        ', ''), ('((', _SIGNAL), ('°', _SIGNAL), ('))', _SIGNAL),
     ('  ✦', _BOOM)),
)


def _satellite() -> Text:
    """Render a recognizable satellite: solar-array wings, bus, and antenna."""
    # Right-pad every row to a common width so the glyph stays a rigid
    # rectangle: Align.center centres each line by its own width, so unequal
    # rows would otherwise drift apart horizontally.
    width = max(sum(len(seg) for seg, _ in row) for row in _SAT)
    text = Text()
    for r, row in enumerate(_SAT):
        row_width = 0
        for seg, style in row:
            text.append(seg, style=style)
            row_width += len(seg)
        text.append(' ' * (width - row_width))
        if r < len(_SAT) - 1:
            text.append('\n')
    return text


def _fields(state: DashboardState) -> RenderableType:
    rows = (
        ('◆', 'SITE', state.site_name.upper(), theme.PRIMARY),
        ('✧', 'COORDINATES', state.coordinates, theme.PRIMARY),
        ('▲', 'ELEVATION', state.elevation, theme.PRIMARY),
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
    # NOTE: keep this column left-justified. A 'center' column re-centres each
    # line of the satellite by its own width, skewing the glyph; Align.center
    # below does the block centring instead.
    body.add_column(justify='left', ratio=2)
    body.add_row(
        Align(_fields(state), vertical='middle'),
        Align.center(_satellite(), vertical='middle'),
    )
    return Panel(body, title=Text('MISSION OVERVIEW', style=theme.TITLE),
                 title_align='left', box=theme.BOX,
                 border_style=theme.BORDER, padding=(1, 1))
