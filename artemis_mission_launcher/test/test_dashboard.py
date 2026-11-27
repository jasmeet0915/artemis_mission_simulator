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
from artemis_cli.dashboard.state import DashboardState, HISTORY
from artemis_cli.dashboard.widgets.sparklines import column_chart, hbar, sparkline
from rich.console import Console


def _render(state: DashboardState) -> str:
    console = Console(width=160, height=40, record=True)
    console.print(build_layout(state))
    return console.export_text()


def _overview(state: DashboardState) -> str:
    from artemis_cli.dashboard.widgets import mission_overview
    console = Console(width=100, height=20, record=True)
    console.print(mission_overview.render(state))
    return console.export_text()


def test_sun_row_shows_placeholder_before_any_data():
    state = DashboardState()
    text = _overview(state)
    assert 'SUN (AZ/EL)' in text
    assert '--' in text


def test_sun_row_shows_azimuth_and_elevation_when_set():
    state = DashboardState()
    state.sun_azimuth_deg = 127.42
    state.sun_elevation_deg = 1.23
    assert '127.4° / +1.2°' in _overview(state)


def test_sun_elevation_below_horizon_renders_negative():
    state = DashboardState()
    state.sun_azimuth_deg = 12.0
    state.sun_elevation_deg = -0.44
    assert '12.0° / -0.4°' in _overview(state)


def test_sun_row_follows_the_elevation_row():
    state = DashboardState()
    state.sun_azimuth_deg = 5.0
    state.sun_elevation_deg = 5.0
    lines = _overview(state).splitlines()
    elevation_line = next(
        i for i, line in enumerate(lines) if 'ELEVATION' in line
        and 'SUN' not in line)
    sun_line = next(i for i, line in enumerate(lines) if 'SUN (AZ/EL)' in line)
    assert sun_line > elevation_line


def test_layout_contains_all_panels_and_labels():
    state = DashboardState()
    MockProvider().update(state)
    text = _render(state)
    for token in ('ARTEMIS', 'Welcome, Commander', 'UTC TIME', 'HOST',
                  'MISSION OVERVIEW', 'SITE', 'COORDINATES', 'ELEVATION',
                  'MISSION CLOCK', 'SIM TIME ELAPSED', 'TIME ACCELERATION',
                  'SYSTEM MONITOR', 'CPU USAGE', 'MEMORY USAGE',
                  'GPU USAGE', 'DISK USAGE', 'NETWORK', 'Press Ctrl+C to exit'):
        assert token in text, token
    for absent in ('SUN ELEVATION', 'EARTH VISIBILITY', 'CURRENT PHASE',
                   'SOLAR DAY'):
        assert absent not in text, absent


def test_satellite_glyph_is_aligned():
    from rich.cells import cell_len
    from artemis_cli.dashboard.widgets.mission_overview import _satellite
    lines = _satellite().plain.split('\n')
    # left wing top cap sits directly above the wing body
    assert lines[0].index('┌') == lines[1].index('│')
    # bus joint, mast, and antenna share one column
    bus = lines[4].index('┬')
    assert lines[7].index('│') == bus
    assert lines[8].index('°') == bus
    # every row has identical cell width so per-line centring cannot skew it
    widths = {cell_len(line) for line in lines}
    assert len(widths) == 1, widths


def test_satellite_stays_aligned_when_rendered():
    """Rendered glyph must stay aligned (centring inside the panel)."""
    import re
    from artemis_cli.dashboard.widgets import mission_overview
    state = DashboardState()
    MockProvider().update(state)
    for width in (76, 79, 80, 83):
        console = Console(width=width, height=20, record=True)
        console.print(mission_overview.render(state))
        rows = console.export_text().split('\n')
        cap = body = bus = ant = None
        for line in rows:
            if '┌───┐' in line and '▦' not in line:
                cap = line.index('┌')
            if line.count('▦') >= 6 and '┬' not in line and '┌' not in line \
                    and '└' not in line:
                body = [m.start() for m in re.finditer('│', line)][1]
            if '┬' in line:
                bus = line.index('┬')
            if '((' in line:
                ant = line.index('°')
        assert cap == body, (width, 'cap', cap, 'body', body)
        assert bus == ant, (width, 'bus', bus, 'antenna', ant)


def _render_fixed(renderable, width, height):
    from rich.layout import Layout
    console = Console(width=width, height=height, record=True)
    console.print(Layout(renderable))
    return console.export_text(clear=False).split('\n')[:height]


def test_starfield_fills_region_dimensions():
    from artemis_cli.dashboard.widgets.starfield import Starfield
    lines = _render_fixed(Starfield(seed=1), width=24, height=6)
    assert len(lines) == 6
    assert all(len(line) == 24 for line in lines)


def test_starfield_is_deterministic_for_a_region():
    from artemis_cli.dashboard.widgets.starfield import Starfield
    a = _render_fixed(Starfield(seed=1), 30, 8)
    b = _render_fixed(Starfield(seed=1), 30, 8)
    assert a == b                      # identical => no per-frame flicker


def test_starfield_is_sparse_but_present():
    from artemis_cli.dashboard.widgets.starfield import Starfield
    lines = _render_fixed(Starfield(seed=1, density=0.05), 40, 20)
    cells = ''.join(lines)
    stars = sum(1 for c in cells if c != ' ')
    fraction = stars / len(cells)
    assert 0.0 < fraction < 0.15       # some stars, not dense


def test_starfield_seeds_differ_between_regions():
    from artemis_cli.dashboard.widgets.starfield import Starfield
    assert _render_fixed(Starfield(seed=1), 30, 8) \
        != _render_fixed(Starfield(seed=2), 30, 8)


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


class _StubSky:
    """Minimal stand-in for SkySource: just the `latest` seam."""

    def __init__(self, latest=None):
        self.latest = latest


def test_provider_without_sky_source_leaves_sun_fields_unset():
    state = DashboardState()
    MockProvider().update(state)
    assert state.sun_azimuth_deg is None
    assert state.sun_elevation_deg is None


def test_provider_copies_sun_angles_from_sky_source():
    state = DashboardState()
    MockProvider(sky_source=_StubSky((127.4, 1.2))).update(state)
    assert state.sun_azimuth_deg == 127.4
    assert state.sun_elevation_deg == 1.2


def test_provider_leaves_fields_unset_while_source_has_no_data():
    state = DashboardState()
    MockProvider(sky_source=_StubSky(None)).update(state)
    assert state.sun_azimuth_deg is None


def test_provider_keeps_last_sun_angles_when_source_goes_quiet():
    state = DashboardState()
    source = _StubSky((10.0, 2.0))
    provider = MockProvider(sky_source=source)
    provider.update(state)
    source.latest = None
    provider.update(state)
    assert state.sun_azimuth_deg == 10.0
    assert state.sun_elevation_deg == 2.0


def test_sky_source_has_no_angles_before_any_message():
    from artemis_cli.dashboard.providers import SkySource
    assert SkySource().latest is None


def test_sky_source_callback_records_the_angles():
    from types import SimpleNamespace
    from artemis_cli.dashboard.providers import SkySource
    source = SkySource()
    source._on_sky_object(SimpleNamespace(azimuth_deg=91.5, elevation_deg=-2.5))
    assert source.latest == (91.5, -2.5)


def test_sky_source_start_survives_a_missing_rclpy(monkeypatch):
    import sys
    from artemis_cli.dashboard.providers import SkySource
    # Binding a module name to None makes `import rclpy` raise ImportError.
    monkeypatch.setitem(sys.modules, 'rclpy', None)
    source = SkySource()
    assert source.start() is False
    assert source.latest is None


def test_sky_source_stop_is_safe_before_start():
    from artemis_cli.dashboard.providers import SkySource
    SkySource().stop()  # must not raise


def test_dashboard_process_exits_on_sigterm():
    """ROS signal handlers must not keep mission control alive on a kill."""
    import pytest
    import signal
    import subprocess
    import sys
    import time
    proc = subprocess.Popen(
        [sys.executable, '-m', 'artemis_cli.dashboard'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)              # let SkySource init rclpy and start spinning
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        pytest.fail('dashboard ignored SIGTERM and had to be killed')
