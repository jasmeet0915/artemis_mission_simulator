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
"""Swappable text-rendering primitives for the mission-control dashboard.

`seven_seg` (a self-contained 7-segment LED renderer for the big clock) and
`line_graph` (braille line plot) are the only rendering seams: change the glyph
table / plotting backend here without touching layout code. Deliberately no
external font dependency — Debian's `python3-pyfiglet` ships no fonts, so we draw
the digits ourselves.
"""
from rich.text import Text

# --- seven_seg: a 3-row, ASCII 7-segment LED renderer ----------------------
# Each glyph is exactly three columns wide; glyphs are joined with a single
# space so adjacent bars never touch. Covers everything a clock/date needs.
_SEG = {
    '0': (' _ ', '| |', '|_|'),
    '1': ('   ', '  |', '  |'),
    '2': (' _ ', ' _|', '|_ '),
    '3': (' _ ', ' _|', ' _|'),
    '4': ('   ', '|_|', '  |'),
    '5': (' _ ', '|_ ', ' _|'),
    '6': (' _ ', '|_ ', '|_|'),
    '7': (' _ ', '  |', '  |'),
    '8': (' _ ', '|_|', '|_|'),
    '9': (' _ ', '|_|', ' _|'),
    ':': ('   ', ' · ', ' · '),
    '-': ('   ', ' _ ', '   '),
    '.': ('   ', '   ', ' . '),
    ' ': ('   ', '   ', '   '),
}
_SEG_BLANK = ('   ', '   ', '   ')


def seven_seg(s, *, style=None):
    """Render a digit/clock string as 3-row 7-segment 'LED' text."""
    glyphs = [_SEG.get(ch, _SEG_BLANK) for ch in str(s)]
    if not glyphs:
        return Text('', style=style or '')
    rows = [' '.join(g[r] for g in glyphs) for r in range(3)]
    return Text('\n'.join(rows), style=style or '')


# --- big_text: a 5-row block-letter banner font (A-Z, space, comma) ---------
# Each glyph is five rows of a 5-wide bitmap ('1' = filled). Self-contained so
# the welcome banner needs no external font.
_FONT = {
    'A': ('01110', '10001', '11111', '10001', '10001'),
    'B': ('11110', '10001', '11110', '10001', '11110'),
    'C': ('01111', '10000', '10000', '10000', '01111'),
    'D': ('11110', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '11110', '10000', '11111'),
    'F': ('11111', '10000', '11110', '10000', '10000'),
    'G': ('01111', '10000', '10011', '10001', '01111'),
    'H': ('10001', '10001', '11111', '10001', '10001'),
    'I': ('11111', '00100', '00100', '00100', '11111'),
    'J': ('00111', '00010', '00010', '10010', '01100'),
    'K': ('10001', '10010', '11100', '10010', '10001'),
    'L': ('10000', '10000', '10000', '10000', '11111'),
    'M': ('10001', '11011', '10101', '10001', '10001'),
    'N': ('10001', '11001', '10101', '10011', '10001'),
    'O': ('01110', '10001', '10001', '10001', '01110'),
    'P': ('11110', '10001', '11110', '10000', '10000'),
    'Q': ('01110', '10001', '10101', '10010', '01101'),
    'R': ('11110', '10001', '11110', '10010', '10001'),
    'S': ('01111', '10000', '01110', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100'),
    'U': ('10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '01010', '00100'),
    'W': ('10001', '10001', '10101', '11011', '10001'),
    'X': ('10001', '01010', '00100', '01010', '10001'),
    'Y': ('10001', '01010', '00100', '00100', '00100'),
    'Z': ('11111', '00010', '00100', '01000', '11111'),
    ',': ('00000', '00000', '00000', '00100', '01000'),
    ' ': ('00000', '00000', '00000', '00000', '00000'),
}
_FONT_BLANK = ('00000',) * 5
_FILL = '█'


def big_text(s, *, style=None):
    """Render an uppercase string as 5-row block-letter banner text."""
    glyphs = [_FONT.get(ch, _FONT_BLANK) for ch in str(s).upper()]
    if not glyphs:
        return Text('', style=style or '')
    rows = []
    for r in range(5):
        cells = [g[r].replace('1', _FILL).replace('0', ' ') for g in glyphs]
        rows.append(' '.join(cells))
    return Text('\n'.join(rows), style=style or '')


# --- line_graph: a braille (2x4 dots/cell) line plot -----------------------
_DOTS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
_BRAILLE_BASE = 0x2800


def line_graph(values, width, height, *, vmax=None, style=None):
    """Render a numeric series as a braille line graph (height x width)."""
    series = [v for v in values if v is not None]
    px_w, px_h = width * 2, height * 4
    grid = [[0] * width for _ in range(height)]
    if series and px_w > 0:
        hi = vmax if vmax is not None else max(series)
        if not hi or hi <= 0:
            hi = 1.0
        n = len(series)
        ys = []
        for x in range(px_w):
            idx = x * (n - 1) / (px_w - 1) if px_w > 1 else 0.0
            i0 = int(idx)
            i1 = min(i0 + 1, n - 1)
            frac = idx - i0
            val = series[i0] * (1 - frac) + series[i1] * frac
            norm = min(max(val / hi, 0.0), 1.0)
            ys.append(int(round((1 - norm) * (px_h - 1))))
        prev = None
        for x, y in enumerate(ys):
            span = (y,) if prev is None else range(min(prev, y),
                                                   max(prev, y) + 1)
            for yy in span:
                grid[yy // 4][x // 2] |= _DOTS[yy % 4][x % 2]
            prev = y
    rows = [''.join(chr(_BRAILLE_BASE + cell) for cell in grid[r])
            for r in range(height)]
    return Text('\n'.join(rows), style=style or '')
