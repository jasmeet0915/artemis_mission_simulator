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
"""Tests for the artemis_cli.dashboard package."""
from artemis_cli.dashboard.dashboard import build_layout
from artemis_cli.dashboard.providers import MockProvider, SystemProvider
from artemis_cli.dashboard.state import HISTORY, DashboardState
from artemis_cli.dashboard.widgets.sparklines import column_chart, hbar, sparkline
from rich.console import Console


def _render(state: DashboardState) -> str:
    console = Console(width=160, height=40, record=True)
    console.print(build_layout(state))
    return console.export_text()


def test_layout_contains_all_panels_and_labels():
    state = DashboardState()
    MockProvider().update(state)
    text = _render(state)
    for token in ('ARTEMIS', 'Welcome, Commander', 'UTC TIME', 'HOST',
                  'MISSION OVERVIEW', 'SITE', 'COORDINATES', 'SUN ELEVATION',
                  'MISSION CLOCK', 'SIM TIME ELAPSED', 'TIME ACCELERATION',
                  'SOLAR DAY', 'SYSTEM MONITOR', 'CPU USAGE', 'MEMORY USAGE',
                  'GPU USAGE', 'DISK USAGE', 'NETWORK', 'Press Ctrl+C to exit'):
        assert token in text, token


def test_mock_provider_fills_sane_values():
    state = DashboardState()
    MockProvider().update(state)
    assert 0.0 <= state.cpu_percent <= 100.0
    assert 0.0 <= state.memory_percent <= 100.0
    assert state.gpu_percent is not None          # mock provides a GPU
    assert state.hostname == 'artemis'
    assert len(state.cpu_history) == 1


def test_system_provider_gpu_is_na_and_does_not_fail():
    state = DashboardState()
    SystemProvider().update(state)
    assert state.gpu_percent is None              # psutil has no GPU
    assert state.memory_total > 0.0
    assert state.disk_total > 0.0


def test_histories_are_bounded():
    state = DashboardState()
    provider = MockProvider()
    for _ in range(HISTORY + 20):
        provider.update(state)
    assert len(state.cpu_history) == HISTORY


def test_sparkline_width_and_glyphs():
    line = sparkline([0, 25, 50, 75, 100], width=10, vmax=100)
    assert len(line) == 10
    assert line[-1] in '▁▂▃▄▅▆▇█'


def test_column_chart_dimensions():
    chart = column_chart([1, 2, 3, 4], width=8, height=4, style='cyan')
    lines = chart.plain.split('\n')
    assert len(lines) == 4
    assert all(len(line) == 8 for line in lines)


def test_hbar_is_full_width():
    bar = hbar(0.5, 10, 'cyan', 'grey37')
    assert len(bar.plain) == 10
