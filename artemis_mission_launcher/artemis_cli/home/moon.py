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
"""Lunar phase maths + a phase-shaded ASCII moon for the dashboard centre.

The brightness map below is a downsampled version of the ASCII moon from
Sean Rooney's ASCIIMoon project (https://github.com/Sean-93/asciimoon, MIT),
itself traced from a 1992 NASA/Galileo photograph. Each cell is a 0-9
brightness; `moon_art` shades it for the current phase computed from the
mission epoch.
"""
import math

from rich.text import Text

_SYNODIC = 29.530588853          # days, mean synodic month
_REF_NEW_MOON = 947182440        # unix UTC of the 2000-01-06 18:14 new moon

# 37x17 brightness map (0 = off-disk/space, 9 = brightest).
_MOON = (
    '0000000000013467889886664210000000000',
    '0000000024555566787767789885320000000',
    '0000001224444444444444568876665300000',
    '0000112344333344664555456775666662000',
    '0011112322122233456665455576776666300',
    '0011222222222233444333335578776667620',
    '0212332222223333442222223777654335641',
    '1211222333333234532222222434684223542',
    '1311243345634323222333222222356444443',
    '1211233333333234444543221222232333442',
    '0422112333433443577754322454321234441',
    '0243322323334565677778754566432344410',
    '0045422342333466667788996436544433200',
    '0002542333322476777777887666666631000',
    '0000034444666799888778777777875200000',
    '0000000245678999988777777765310000000',
    '0000000000134678887665543210000000000',
)
_RAMP = ' .:-=+*o#%@'    # brightness 0-9 -> glyph


def lunar_phase(epoch_sec):
    """Return phase info for a unix-UTC epoch.

    Keys: ``age_days`` (0..synodic), ``fraction`` illuminated (0..1),
    ``waxing`` (bool) and a human ``name``.
    """
    age = ((epoch_sec - _REF_NEW_MOON) / 86400.0) % _SYNODIC
    p = age / _SYNODIC
    fraction = (1.0 - math.cos(2.0 * math.pi * p)) / 2.0
    waxing = p < 0.5
    if p < 0.02 or p > 0.98:
        name = 'NEW MOON'
    elif p < 0.23:
        name = 'WAXING CRESCENT'
    elif p < 0.27:
        name = 'FIRST QUARTER'
    elif p < 0.48:
        name = 'WAXING GIBBOUS'
    elif p < 0.52:
        name = 'FULL MOON'
    elif p < 0.73:
        name = 'WANING GIBBOUS'
    elif p < 0.77:
        name = 'LAST QUARTER'
    else:
        name = 'WANING CRESCENT'
    return {'age_days': age, 'fraction': fraction,
            'waxing': waxing, 'name': name}


def moon_art(epoch_sec, *, lit_style=None, shadow_style=None):
    """Render the ASCII moon shaded for the phase at ``epoch_sec``."""
    ph = lunar_phase(epoch_sec)
    p = ph['age_days'] / _SYNODIC
    cos_p = math.cos(2.0 * math.pi * p)
    waxing = ph['waxing']
    height = len(_MOON)
    width = len(_MOON[0])
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    rx, ry = width / 2.0, height / 2.0

    text = Text()
    for y, line in enumerate(_MOON):
        for x, digit in enumerate(line):
            d = int(digit)
            if d == 0:
                text.append(' ')
                continue
            nx, ny = (x - cx) / rx, (y - cy) / ry
            half = math.sqrt(max(0.0, 1.0 - ny * ny))
            terminator = cos_p * half
            # Waxing: lit limb on the right (nx >= terminator). Waning: lit limb
            # on the left, mirrored about the centre (nx <= -terminator).
            lit = nx >= terminator if waxing else nx <= -terminator
            glyph = _RAMP[round(d / 9.0 * (len(_RAMP) - 1))]
            text.append(glyph, style=lit_style if lit else shadow_style)
        if y < height - 1:
            text.append('\n')
    return text
