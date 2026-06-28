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
"""A sparse, stable starfield that fills the dashboard's margin regions."""
# Used as the dashboard's background: it replaces the blank margin/spacer panels
# so the centred content appears to float in space. Star positions are derived
# deterministically from the region size and a per-region seed, so the field is
# stable from frame to frame (no flicker) while differing between regions.
from __future__ import annotations

import random

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text

from .. import theme

# (glyph, style, weight): mostly faint pinprick dots, a few brighter stars, so
# the field reads as varied 'size and brightness' without being busy.
_STARS = (
    ('·', theme.FAINT, 46),
    ('·', theme.MUTED, 22),
    ('∙', theme.MUTED, 12),
    ('✦', theme.FAINT, 8),
    ('✧', theme.MUTED, 6),
    ('✦', theme.PRIMARY, 4),
    ('✶', f'bold {theme.PRIMARY}', 2),
)
_GLYPHS = [g for g, _, _ in _STARS]
_STYLES = [s for _, s, _ in _STARS]
_WEIGHTS = [w for _, _, w in _STARS]


class Starfield:
    """Render a sparse, stable starfield sized to the available region."""

    def __init__(self, *, density: float = 0.03, seed: int = 0) -> None:
        self.density = density
        self.seed = seed

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        height = options.height if options.height is not None else 1
        rng = random.Random(f'{self.seed}:{width}x{height}')
        for _y in range(height):
            line = Text()
            for _x in range(width):
                if rng.random() < self.density:
                    idx = rng.choices(range(len(_STARS)), weights=_WEIGHTS)[0]
                    line.append(_GLYPHS[idx], style=_STYLES[idx])
                else:
                    line.append(' ')
            yield line
