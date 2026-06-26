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
