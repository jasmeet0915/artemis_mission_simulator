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
"""Pure Unicode chart primitives (no colour, no data access)."""
from __future__ import annotations

from typing import Iterable, List, Optional

from rich.text import Text

_BLOCKS = ' ▁▂▃▄▅▆▇█'      # 0/8 .. 8/8 of a cell
_BARS = '▁▂▃▄▅▆▇█'         # 1/8 .. 8/8


def _resample(values: Iterable[float], width: int) -> List[float]:
    series = [float(v) for v in values]
    if not series or width <= 0:
        return [0.0] * max(width, 0)
    if len(series) >= width:
        return series[-width:]
    return [series[0]] * (width - len(series)) + series


def sparkline(values: Iterable[float], width: int,
              vmax: Optional[float] = None) -> str:
    """One-row block sparkline, right-aligned to ``width``."""
    series = _resample(values, width)
    hi = vmax if vmax is not None else max(series + [1e-9])
    hi = hi if hi > 0 else 1.0
    out = []
    for v in series:
        frac = min(max(v / hi, 0.0), 1.0)
        out.append(_BARS[min(len(_BARS) - 1, int(round(frac * (len(_BARS) - 1))))]
                   if frac > 0 else ' ')
    return ''.join(out)


def column_chart(values: Iterable[float], width: int, height: int,
                 style: str, vmax: Optional[float] = None) -> Text:
    """Render a filled vertical-column area chart, ``height`` rows tall."""
    series = _resample(values, width)
    hi = vmax if vmax is not None else max(series + [1e-9])
    hi = hi if hi > 0 else 1.0
    eighths = [min(max(v / hi, 0.0), 1.0) * height * 8 for v in series]
    rows = []
    for row in range(height):           # row 0 = top
        cells = []
        floor_eighths = (height - row - 1) * 8
        for filled in eighths:
            delta = filled - floor_eighths
            if delta >= 8:
                cells.append('█')
            elif delta <= 0:
                cells.append(' ')
            else:
                cells.append(_BLOCKS[int(delta)])
        rows.append(''.join(cells))
    return Text('\n'.join(rows), style=style)


def hbar(fraction: float, width: int, fill_style: str, track_style: str) -> Text:
    """Horizontal progress bar built from block glyphs."""
    frac = min(max(fraction, 0.0), 1.0)
    filled = int(round(frac * width))
    return Text.assemble(('█' * filled, fill_style),
                         ('─' * (width - filled), track_style))
