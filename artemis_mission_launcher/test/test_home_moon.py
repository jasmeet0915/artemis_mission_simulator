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
"""Tests for artemis_cli.home.moon."""
from artemis_cli.home.moon import lunar_phase, moon_art

_SYNODIC = 29.530588853
_REF_NEW_MOON = 947182440  # a known new moon


def test_phase_at_reference_is_new_moon():
    ph = lunar_phase(_REF_NEW_MOON)
    assert ph['name'] == 'NEW MOON'
    assert ph['fraction'] < 0.02


def test_phase_at_half_synodic_is_full_moon():
    ph = lunar_phase(_REF_NEW_MOON + int(_SYNODIC / 2 * 86400))
    assert ph['name'] == 'FULL MOON'
    assert ph['fraction'] > 0.98


def test_phase_waxing_then_waning():
    assert lunar_phase(_REF_NEW_MOON + 5 * 86400)['waxing'] is True
    assert lunar_phase(_REF_NEW_MOON + 22 * 86400)['waxing'] is False


def test_moon_art_is_multirow_text():
    art = moon_art(_REF_NEW_MOON + 7 * 86400).plain
    assert '\n' in art
    # the full-moon disk has bright glyphs near full phase
    full = moon_art(_REF_NEW_MOON + int(_SYNODIC / 2 * 86400)).plain
    assert any(ch in full for ch in '#%@')
