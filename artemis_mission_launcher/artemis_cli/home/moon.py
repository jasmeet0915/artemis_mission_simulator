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

# 49x23 brightness map (0 = off-disk/space, 9 = brightest), downsampled from the
# ASCIIMoon art. Higher resolution keeps the maria/highland texture legible.
_MOON = (
    '0000000000000000123577778877555432000000000000000',
    '0000000000001256776778888777778887853100000000000',
    '0000000001235544444455665666677888765554100000000',
    '0000000112224444444444434434444578776656641000000',
    '0000001112345434324346654354444677765565666400000',
    '0000111123332211223334565566545555675666665641000',
    '0001111222222111222334446655433444666667656675100',
    '0011122222221122222334344223332455677777566667410',
    '0111133222222222323333432222222236877665544556440',
    '0111112222323222222344432122222234557555322235321',
    '0311112323433333333344432222222223333567422145542',
    '0411112432444643332232222433421111111235753443352',
    '0311112333344433322334323344211111112233344444442',
    '0321111222334432222334567764322112322222112234331',
    '0432211223323433444435677766544224654322123443430',
    '0143222123222332456656677777875434565432234544310',
    '0025344322332332245556666778888754347554433334100',
    '0002553123333322235666767777788863446544454331000',
    '0000036423333322235767667777678876767777764200000',
    '0000002444434565567888777767777776777787531000000',
    '0000000023455677889998877777776676766542100000000',
    '0000000000013557888888887765666776542100000000000',
    '0000000000000012356787777665544322100000000000000',
)
_RAMP = ' .:-=+c*o#%@&'    # brightness 0-9 -> glyph


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
