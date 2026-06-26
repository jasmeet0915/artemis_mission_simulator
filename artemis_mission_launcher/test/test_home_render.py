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
"""Tests for artemis_cli.home.render."""
from artemis_cli.home.render import block_text, line_graph

_BLANK_BRAILLE = chr(0x2800)


def test_block_text_is_multirow_and_nonblank():
    plain = block_text('12').plain
    assert '\n' in plain  # figlet output spans multiple rows
    assert plain.strip() != ''


def test_block_text_empty_is_blank():
    assert block_text('').plain == ''


def test_block_text_custom_font():
    plain = block_text('A', font='standard').plain
    assert plain.strip() != ''


def test_line_graph_dimensions():
    lines = line_graph([1, 2, 3, 4], width=6, height=2).plain.split('\n')
    assert len(lines) == 2
    assert all(len(line) == 6 for line in lines)


def test_line_graph_empty_is_blank_braille():
    lines = line_graph([], width=4, height=2).plain.split('\n')
    assert all(set(line) <= {_BLANK_BRAILLE} for line in lines)


def test_line_graph_renders_dots_for_data():
    plain = line_graph([0, 100], width=8, height=3, vmax=100).plain
    assert any(ch != _BLANK_BRAILLE and ch != '\n' for ch in plain)
