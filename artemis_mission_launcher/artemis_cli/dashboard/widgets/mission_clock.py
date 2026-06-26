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
"""Mission Clock panel: large Digits clock, sim time, acceleration, solar bar."""
from __future__ import annotations

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Digits, Label, ProgressBar, Static

from .. import theme
from ..state import DashboardState


def _stats(state: DashboardState) -> Table:
    grid = Table.grid(expand=True)
    grid.add_column(justify='left', ratio=1)
    grid.add_column(justify='left', ratio=1)
    grid.add_row(Text('SIM TIME ELAPSED', style=theme.MUTED),
                 Text('TIME ACCELERATION', style=theme.MUTED))
    grid.add_row(Text(state.simulation_time, style=theme.PRIMARY),
                 Text(f'{state.time_acceleration:.1f}x', style=theme.WARN))
    return grid


class MissionClockPanel(Vertical):
    """Bordered card with the big mission clock and time stats."""

    DEFAULT_CSS = f"""
    MissionClockPanel {{ padding: 1 2; }}
    MissionClockPanel #clock-date {{ color: {theme.PRIMARY}; text-style: bold; }}
    MissionClockPanel #clock-digits {{ color: {theme.ACCENT}; }}
    MissionClockPanel .clock-muted {{ color: {theme.MUTED}; }}
    MissionClockPanel #solar-bar {{ width: 1fr; margin-top: 1; }}
    MissionClockPanel #solar-bar Bar > .bar--bar {{ color: {theme.PRIMARY}; }}
    MissionClockPanel #solar-bar Bar > .bar--complete {{ color: {theme.OK}; }}
    MissionClockPanel #solar-bar PercentageStatus {{ color: {theme.MUTED}; }}
    """

    def on_mount(self) -> None:
        self.border_title = 'MISSION CLOCK'

    def compose(self) -> ComposeResult:
        yield Label('', id='clock-date')
        yield Digits('', id='clock-digits')
        yield Label('UTC', classes='clock-muted')
        yield Static(id='clock-stats')
        yield Label('SOLAR DAY @ SOUTH POLE', classes='clock-muted')
        yield ProgressBar(total=100, show_eta=False, id='solar-bar')

    def update_state(self, state: DashboardState) -> None:
        self.query_one('#clock-date', Label).update(state.mission_date)
        self.query_one('#clock-digits', Digits).update(state.mission_clock)
        self.query_one('#clock-stats', Static).update(_stats(state))
        self.query_one('#solar-bar', ProgressBar).update(
            total=100, progress=state.solar_day_progress * 100.0)
