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
import asyncio

from artemis_cli.dashboard.app import ArtemisDashboardApp
from artemis_cli.dashboard.providers import MockProvider, SystemProvider
from artemis_cli.dashboard.state import HISTORY, DashboardState


def test_app_boots_and_has_panels():
    async def go():
        app = ArtemisDashboardApp(
            MockProvider(site='shackleton_rim', epoch_sec=0, acceleration=100.0))
        async with app.run_test() as pilot:
            await pilot.pause()
            for pid in ('#wordmark', '#welcome', '#status', '#overview',
                        '#clock', '#monitor', '#footer'):
                assert app.query_one(pid) is not None
    asyncio.run(go())


def test_welcome_card_has_green_nominal():
    from artemis_cli.dashboard import theme
    from artemis_cli.dashboard.widgets.header import WelcomeCard
    txt = WelcomeCard.render_text()
    plain = txt.plain
    assert 'Welcome, Commander' in plain
    start = plain.index('nominal')
    end = start + len('nominal')
    # a styled span covering 'nominal' uses the OK (green) colour
    assert any(s.start <= start and s.end >= end and theme.OK in str(s.style)
               for s in txt.spans)


def test_radar_dimensions_and_blip():
    from artemis_cli.dashboard.widgets.mission_overview import _radar
    txt = _radar(27, 13)
    lines = txt.plain.split('\n')
    assert len(lines) == 13
    assert all(len(line) == 27 for line in lines)
    assert '◉' in txt.plain          # the contact blip


def test_mission_clock_digits_and_solar_bar():
    from textual.widgets import Digits, ProgressBar

    async def go():
        app = ArtemisDashboardApp(
            MockProvider(site='shackleton_rim', epoch_sec=0, acceleration=100.0))
        async with app.run_test() as pilot:
            await pilot.pause()
            digits = app.query_one('#clock-digits', Digits)
            assert digits.value == app.state.mission_clock
            bar = app.query_one('#solar-bar', ProgressBar)
            assert bar.percentage is not None
    asyncio.run(go())


def test_system_monitor_cpu_sparkline_bounded():
    from textual.widgets import Sparkline

    async def go():
        app = ArtemisDashboardApp(
            MockProvider(site='shackleton_rim', epoch_sec=0, acceleration=100.0))
        async with app.run_test() as pilot:
            for _ in range(3):
                await pilot.pause()
            spark = app.query_one('#cpu-spark', Sparkline)
            assert 1 <= len(spark.data) <= HISTORY
    asyncio.run(go())


def test_system_monitor_boots_with_real_provider_gpu_na():
    async def go():
        app = ArtemisDashboardApp(
            SystemProvider(site='shackleton_rim', epoch_sec=0,
                           acceleration=100.0))
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.state.gpu_percent is None   # N/A branch ran, no crash
    asyncio.run(go())


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
