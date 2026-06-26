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

# 55x25 brightness map (0 = off-disk/space, 9 = brightest), downsampled with a
# gamma boost from the ASCIIMoon art — enough resolution + contrast to keep the
# maria/highland texture reading as the Moon.
_MOON = (
    '0000000000000000002335687878878665643200000000000000000',
    '0000000000000023567767888988887778889887530000000000000',
    '0000000000012566554455566776776777898887656520000000000',
    '0000000001232443444444444444445555678886666666300000000',
    '0000000112234466444355456544454444467777667766663000000',
    '0000011111244423222234455665566655556677656667766610000',
    '0000111122442211122233445566766544555567767766566651000',
    '0002111222222222122323444447545544454467777786677776100',
    '0011124332322222222223444444233333355678887776766776510',
    '0211123322222222223344444442222332224687766555433565430',
    '0211121232233333333223456542122322223454666753221255422',
    '0311112233344444444434444433333322222343346785222356543',
    '0421112344345556444433332222543432211212223467644444453',
    '0311111343344455444333344323354321222111122434565544442',
    '0331111232334444333224444656665422211222223322122434432',
    '0431221222234344434443345677876443222366442222223444430',
    '0153322222332334435666656777777887543556653222346544410',
    '0025444432223334433466557687778888775545675444444444100',
    '0003655322334433333356666677777789985444665544544441000',
    '0000156421233443322367767766777778887456565555654310000',
    '0000003653344343333447778778877778888776778887642000000',
    '0000000134554547776889988887777877767677778754200000000',
    '0000000001245666788999998988777777677777664320000000000',
    '0000000000001355678898998887776667777765321000000000000',
    '0000000000000001234567888877666655543210000000000000000',
)
_RAMP = ' .::oo**##%%@@'    # brightness 0-9 -> glyph (dotty, no line artifacts)


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
