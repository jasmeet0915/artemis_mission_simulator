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

`block_text` and `line_graph` are the only rendering seams: `pyfiglet` /
`plotext` can later reimplement them without changing layout code.
"""
from rich.text import Text

# --- block_text: a 3-text-row half-block font ------------------------------
# Each glyph is a 5-pixel-tall, 3-pixel-wide '#'/' ' grid. Pixel rows are
# paired top/bottom into half-block chars, so 6 padded pixel rows -> 3 text
# rows. Fixed width keeps every glyph aligned (no drift).
_FONT5 = {
    ' ': ['   ', '   ', '   ', '   ', '   '],
    '0': ['###', '# #', '# #', '# #', '###'],
    '1': [' # ', '## ', ' # ', ' # ', '###'],
    '2': ['###', '  #', '###', '#  ', '###'],
    '3': ['###', '  #', '###', '  #', '###'],
    '4': ['# #', '# #', '###', '  #', '  #'],
    '5': ['###', '#  ', '###', '  #', '###'],
    '6': ['###', '#  ', '###', '# #', '###'],
    '7': ['###', '  #', '  #', '  #', '  #'],
    '8': ['###', '# #', '###', '# #', '###'],
    '9': ['###', '# #', '###', '  #', '###'],
    ':': ['   ', ' # ', '   ', ' # ', '   '],
    '-': ['   ', '   ', '###', '   ', '   '],
    '_': ['   ', '   ', '   ', '   ', '###'],
    'A': ['###', '# #', '###', '# #', '# #'],
    'B': ['## ', '# #', '## ', '# #', '## '],
    'C': ['###', '#  ', '#  ', '#  ', '###'],
    'D': ['## ', '# #', '# #', '# #', '## '],
    'E': ['###', '#  ', '###', '#  ', '###'],
    'F': ['###', '#  ', '###', '#  ', '#  '],
    'G': ['###', '#  ', '# #', '# #', '###'],
    'H': ['# #', '# #', '###', '# #', '# #'],
    'I': ['###', ' # ', ' # ', ' # ', '###'],
    'J': ['###', '  #', '  #', '# #', '###'],
    'K': ['# #', '# #', '## ', '# #', '# #'],
    'L': ['#  ', '#  ', '#  ', '#  ', '###'],
    'M': ['# #', '###', '###', '# #', '# #'],
    'N': ['# #', '###', '# #', '# #', '# #'],
    'O': ['###', '# #', '# #', '# #', '###'],
    'P': ['###', '# #', '###', '#  ', '#  '],
    'Q': ['###', '# #', '# #', '###', '  #'],
    'R': ['## ', '# #', '## ', '# #', '# #'],
    'S': ['###', '#  ', '###', '  #', '###'],
    'T': ['###', ' # ', ' # ', ' # ', ' # '],
    'U': ['# #', '# #', '# #', '# #', '###'],
    'V': ['# #', '# #', '# #', '# #', ' # '],
    'W': ['# #', '# #', '###', '###', '# #'],
    'X': ['# #', '# #', ' # ', '# #', '# #'],
    'Y': ['# #', '# #', ' # ', ' # ', ' # '],
    'Z': ['###', '  #', ' # ', '#  ', '###'],
}

_HALF = {(False, False): ' ', (True, False): '▀',
         (False, True): '▄', (True, True): '█'}


def _to_block(grid):
    """Pair a 5-row pixel grid (padded to 6) into 3 half-block text rows."""
    rows = list(grid) + ['   ']
    out = []
    for top, bot in ((rows[0], rows[1]), (rows[2], rows[3]),
                     (rows[4], rows[5])):
        out.append(''.join(
            _HALF[(top[c] == '#', bot[c] == '#')] for c in range(3)))
    return tuple(out)


_GLYPHS = {ch: _to_block(grid) for ch, grid in _FONT5.items()}
_BLANK = ('   ', '   ', '   ')


def block_text(s, *, style=None, gap=1):
    """Render a string as 3 rows of half-block 'big' text."""
    glyphs = [_GLYPHS.get(ch.upper(), _BLANK) for ch in s]
    sep = ' ' * gap
    if glyphs:
        lines = [sep.join(g[r] for g in glyphs) for r in range(3)]
    else:
        lines = ['', '', '']
    return Text('\n'.join(lines), style=style or '')


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
